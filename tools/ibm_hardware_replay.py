#!/usr/bin/env python3
"""Replay a captured IBM result offline; never authenticate or submit a job."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile

import ibm_quantum as ibm


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "experiments/quantum/ibm-hardware-bell-xx"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def replay(fslc=None, sdk_wire=False):
    lock = ibm.read_json(CAPTURE / "capture.lock.json")
    require(sha(Path(__file__)) == lock["replay_tool_sha256"], "replay tool changed")
    require(sha(ROOT / "tools/ibm_quantum.py") == lock["comparison_owner_sha256"], "comparison owner changed")
    for name, digest in lock["files"].items():
        require(Path(name).name == name, "nonlocal capture filename")
        require(sha(CAPTURE / name) == digest, f"capture hash mismatch: {name}")
    require(sha(ROOT / lock["source_file"]) == lock["source_sha256"], "source changed")
    receipt = ibm.read_json(CAPTURE / "receipt.json")
    native = ibm.read_json(CAPTURE / "native-bundle-manifest.json")
    require(
        sha(CAPTURE / "native-bundle-manifest.json") == receipt["bundle_sha256"],
        "native bundle binding differs",
    )
    for name in ["source.fslc", "circuit.qasm", "reference.json", "expected.json"]:
        require(sha(CAPTURE / name) == native["files"][name], f"native artifact differs: {name}")
    job = ibm.read_json(CAPTURE / "job.json")
    request = ibm.read_json(CAPTURE / "sdk-request.json")
    recorded = ibm.read_json(CAPTURE / "comparison.json")
    require(receipt["state"] == "completed", "receipt not completed")
    require(job["state"]["status"] == "Completed", "provider job not completed")
    require(job["id"] == receipt["job_id"] == lock["hardware_job_id"], "job mismatch")
    require(job["backend"] == receipt["backend"] == request["backend"], "backend mismatch")
    require(receipt["submission_posts"] == lock["submission_posts"] == 1, "submission count")
    require(receipt["dry_run"] is False and request.get("dry_run", False) is False, "dry run")
    require(request["program_id"] == "sampler" and request["cost"] == 60, "job contract")
    pubs = request["params"]["pubs"]
    require(len(pubs) == 1 and len(pubs[0]) == 3 and pubs[0][2] == 1024, "PUB shots")
    expected = ibm.read_json(CAPTURE / "expected.json")
    manifest = {"trace_values": [], "physical_qubits": [135, 139], "shots": 1024}
    counts = ibm.counts_from_result(ibm.read_json(CAPTURE / "result-raw.json"), manifest)
    comparison = ibm.compare_counts(counts, expected, manifest)
    for key, value in comparison.items():
        actual = recorded[key]
        require(
            math.isclose(actual, value, rel_tol=0, abs_tol=1e-12)
            if type(value) is float
            else actual == value,
            f"recorded comparison mismatch: {key}",
        )
    require(sha(CAPTURE / "result-raw.json") == recorded["result_raw_sha256"], "raw result changed")
    require(recorded["ideal_sampling_compatible"] is False, "unexpected ideal-model result")
    wire_replayed = False
    if sdk_wire:
        from qiskit import qasm3
        from qiskit_ibm_runtime import RuntimeDecoder

        decoded = json.loads((CAPTURE / "sdk-request.json").read_text(), cls=RuntimeDecoder)
        sent = decoded["params"]["pubs"][0][0]
        native_circuit = qasm3.loads((CAPTURE / "circuit.qasm").read_text())

        def signature(circuit):
            return (
                circuit.num_qubits,
                circuit.num_clbits,
                tuple((register.name, len(register)) for register in circuit.cregs),
                float(circuit.global_phase),
                tuple(
                    (
                        instruction.operation.name,
                        tuple(float(value) for value in instruction.operation.params),
                        tuple(circuit.find_bit(bit).index for bit in instruction.qubits),
                        tuple(circuit.find_bit(bit).index for bit in instruction.clbits),
                    )
                    for instruction in circuit.data
                ),
            )

        require(signature(sent) == signature(native_circuit), "SDK wire circuit differs from native QASM")
        wire_replayed = True
    native_replayed = False
    if fslc:
        with tempfile.TemporaryDirectory(prefix="fission-ibm-replay-") as tmp:
            tmp = Path(tmp)
            package = tmp / "source.fslc"
            ibm.run([fslc, "compile", ROOT / lock["source_file"], package])
            require(package.read_bytes() == (CAPTURE / "source.fslc").read_bytes(), "package differs")
            qasm = tmp / "circuit.qasm"
            ibm.run([fslc, "emit-ibm", package, "bell_coherent", "135,139", "cz", "135:139,139:135", 0, "XX", qasm])
            require(qasm.read_bytes() == (CAPTURE / "circuit.qasm").read_bytes(), "native QASM differs")
            reference = json.loads(ibm.run([fslc, "simulate-quantum", package, "bell_coherent", 2, "basis:0"]))
            probabilities = ibm.expected_distribution(reference, [], "XX")
            require(probabilities.keys() == expected.keys(), "reference outcome set differs")
            require(all(math.isclose(v, expected[k], rel_tol=0, abs_tol=2e-10) for k, v in probabilities.items()), "FIR probabilities differ")
            native_replayed = True
    return {
        "status": "passed",
        "job_id": job["id"],
        "backend": job["backend"],
        "native_replayed": native_replayed,
        "sdk_wire_replayed": wire_replayed,
        "sdk_request_matches_native_qasm": True if wire_replayed else None,
        "captured_hardware_execution": True,
        "hardware_reexecuted": False,
        "network_requests": 0,
        "comparison": comparison,
        "scope": "Offline capture integrity and FIR emission/reference replay; ideal-model incompatibility is retained, not treated as equivalence.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=Path)
    parser.add_argument("--sdk-wire", action="store_true", help="Also decode the sent QPY using the optional SDK environment")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = replay(args.fslc.resolve() if args.fslc else None, args.sdk_wire)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        ibm.write_json(args.report, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
