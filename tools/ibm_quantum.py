#!/usr/bin/env python3
"""Separate stdlib-only IBM Open Plan adapter for owned FIR circuit projections.

Preparation is offline. Network submission is an explicit command and requires
IQP_API_TOKEN and IBM_QUANTUM_CRN in the caller's environment. No SDK is imported.
"""

import argparse
import ast
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zlib

API_VERSION = "2026-04-15"
API = "https://quantum.cloud.ibm.com/api/v1"
CATALOG = "https://globalcatalog.cloud.ibm.com/api/v1"
MAX_BYTES = 8 * 1024 * 1024
MAX_SHOTS = 4096


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def read_json(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("input exceeds 8 MiB")
    return json.loads(
        raw,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
    )


def write_json(path, value):
    Path(path).write_bytes(encoded(value))


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError("invalid provider identifier")
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http(method, url, headers, body=None):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(
            request, timeout=30
        ) as response:
            raw = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Provider error bodies and authentication material never enter logs.
        raise ValueError(f"IBM HTTP status {exc.code}; no automatic retry") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError(
            "IBM transport outcome uncertain; no automatic retry"
        ) from None
    if len(raw) > MAX_BYTES:
        raise ValueError("IBM response exceeds 8 MiB")
    return json.loads(
        raw,
        parse_constant=lambda _: (_ for _ in ()).throw(
            ValueError("nonfinite provider JSON")
        ),
    )


class Client:
    def __init__(self, key, crn, transport=http):
        parts = crn.split(":")
        if (
            len(parts) != 10
            or parts[:6]
            != ["crn", "v1", "bluemix", "public", "quantum-computing", "us-east"]
            or any(c.isspace() for c in crn)
        ):
            raise ValueError("explicit us-east IBM Quantum CRN required")
        if not key or any(c.isspace() for c in key):
            raise ValueError("IBM API key required")
        self.crn = crn
        self.transport = transport
        response = transport(
            "POST",
            "https://iam.cloud.ibm.com/identity/token",
            {"Content-Type": "application/x-www-form-urlencoded"},
            urllib.parse.urlencode(
                {"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": key}
            ).encode(),
        )
        self.token = response["access_token"]
        if (
            not isinstance(self.token, str)
            or not self.token
            or any(c.isspace() for c in self.token)
        ):
            raise ValueError("invalid IAM access token")

    @classmethod
    def from_env(cls):
        return cls(
            os.environ.get("IQP_API_TOKEN", ""), os.environ.get("IBM_QUANTUM_CRN", "")
        )

    def call(self, method, path, body=None, catalog=False):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "IBM-API-Version": API_VERSION,
        }
        if not catalog:
            headers["Service-CRN"] = self.crn
        if body is not None:
            headers["Content-Type"] = "application/json"
        return self.transport(
            method,
            (CATALOG if catalog else API) + path,
            headers,
            encoded(body) if body is not None else None,
        )

    def snapshot(self, backend):
        backend = identifier(backend)
        instance = self.call("GET", "/instance")
        plan_id = identifier(instance["plan_id"])
        plan = self.call("GET", "/" + plan_id, catalog=True)
        if (
            plan.get("id") != plan_id
            or plan.get("kind") != "plan"
            or plan.get("name") != "open"
        ):
            raise ValueError("instance is not a verified Open Plan; no submission")
        snapshot = {
            "schema": "fission.ibm.snapshot.v1",
            "synthetic": False,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "api_version": API_VERSION,
            "crn_sha256": digest(self.crn.encode()),
            "instance": instance,
            "catalog_plan": plan,
            "usage": self.call("GET", "/instances/usage"),
            "configuration": self.call("GET", f"/backends/{backend}/configuration"),
            "properties": self.call("GET", f"/backends/{backend}/properties"),
            "status": self.call("GET", f"/backends/{backend}/status"),
        }
        admit_snapshot(snapshot)
        return snapshot


def admit_snapshot(snapshot):
    if (
        snapshot.get("schema") != "fission.ibm.snapshot.v1"
        or snapshot.get("api_version") != API_VERSION
        or type(snapshot.get("synthetic")) is not bool
    ):
        raise ValueError("unsupported snapshot envelope")
    plan = snapshot["catalog_plan"]
    if (
        plan.get("id") != snapshot["instance"].get("plan_id")
        or plan.get("kind") != "plan"
        or plan.get("name") != "open"
    ):
        raise ValueError("snapshot does not identify Open Plan")
    config = snapshot["configuration"]
    identifier(config["backend_name"])
    if (
        config.get("simulator") is not False
        or snapshot["status"].get("operational") is not True
    ):
        raise ValueError("operational physical backend required")
    if type(config["n_qubits"]) is not int or not 1 <= config["n_qubits"] <= 65536:
        raise ValueError("invalid device extent")
    if snapshot["properties"].get("backend_name") != config[
        "backend_name"
    ] or not snapshot["properties"].get("last_update_date"):
        raise ValueError("missing identified calibration snapshot")


def target(snapshot, layout):
    admit_snapshot(snapshot)
    config = snapshot["configuration"]
    if (
        not 1 <= len(layout) <= 8
        or len(set(layout)) != len(layout)
        or any(type(q) is not int or not 0 <= q < config["n_qubits"] for q in layout)
    ):
        raise ValueError("injective 1..8 qubit physical layout required")
    if not {"reset", "measure"} <= set(config.get("supported_instructions", [])):
        raise ValueError("reset/measure availability missing")
    gates = {g["name"]: g for g in config["gates"]}
    if len(gates) != len(config["gates"]):
        raise ValueError("ambiguous duplicate gate definitions")
    for gate in ("rz", "sx", "x"):
        if (
            gate not in config["basis_gates"]
            or gate not in gates
            or any([q] not in gates[gate].get("coupling_map", []) for q in layout)
        ):
            raise ValueError(f"explicit per-qubit {gate} support missing")
    for entangler in ("cz", "cx"):
        if entangler in config["basis_gates"] and entangler in gates:
            edges = gates[entangler].get("coupling_map", [])
            if any(
                not isinstance(e, list)
                or len(e) != 2
                or any(type(q) is not int or not 0 <= q < config["n_qubits"] for q in e)
                or e[0] == e[1]
                for e in edges
            ):
                raise ValueError("invalid two-qubit coupling map")
            return entangler, edges
    # A single-qubit body can project without an entangler; no two-qubit edge.
    return "cz", []


def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace"))
    if len(result.stdout) > MAX_BYTES:
        raise ValueError("native reference output exceeds 8 MiB")
    return result.stdout


def expected_distribution(result, trace_values, axes):
    n = len(axes)
    if result.get("hardware_execution") is not False or result["qubits"] != n:
        raise ValueError("reference identity mismatch")
    probabilities = Counter()
    for branch in result["branches"]:
        record = branch["measurements"]
        if [v[0] for v in record] != trace_values:
            raise ValueError("measurement origin/order mismatch")
        trace = sum(v[1] << i for i, v in enumerate(record))
        vector = [complex(*a) for a in branch["amplitudes"]]
        for q, axis in enumerate(axes):
            if axis == "Y":
                vector = [
                    v * (-1j if i & (1 << q) else 1) for i, v in enumerate(vector)
                ]
            if axis != "Z":
                old = vector[:]
                for i in range(1 << n):
                    if i & (1 << q) == 0:
                        vector[i] = (old[i] + old[i | (1 << q)]) / math.sqrt(2)
                        vector[i | (1 << q)] = (old[i] - old[i | (1 << q)]) / math.sqrt(
                            2
                        )
        for final, amplitude in enumerate(vector):
            probabilities[trace | (final << len(trace_values))] += (
                branch["probability"] * abs(amplitude) ** 2
            )
    if abs(sum(probabilities.values()) - 1) > 2e-10 or any(
        not math.isfinite(p) or p < 0 for p in probabilities.values()
    ):
        raise ValueError("invalid expected instrument probabilities")
    return {str(k): v for k, v in sorted(probabilities.items()) if v > 0}


def payload(backend, qasm, shots, max_seconds):
    if (
        type(shots) is not int
        or not 1 <= shots <= MAX_SHOTS
        or type(max_seconds) is not int
        or not 1 <= max_seconds <= 60
    ):
        raise ValueError("shots 1..4096 and execution cap 1..60 seconds required")
    return {
        "program_id": "sampler",
        "backend": identifier(backend),
        # Runtime's SDK places max_execution_time in the top-level cost field.
        # Enforcement follows provider semantics; this is not a billing guarantee.
        "cost": max_seconds,
        "params": {
            "pubs": [[qasm]],
            "version": 2,
            "options": {
                "default_shots": shots,
                "execution": {"init_qubits": True},
                "dynamical_decoupling": {"enable": False},
                "twirling": {"enable_gates": False, "enable_measure": False},
            },
        },
    }


def prepare(
    fslc, package, name, snapshot, layout, initial, axes, shots, max_seconds, directory
):
    entangler, edges = target(snapshot, layout)
    if not axes or len(axes) != len(layout) or any(a not in "XYZ" for a in axes):
        raise ValueError("one X/Y/Z observation axis per logical qubit required")
    if type(initial) is not int or not 0 <= initial < 1 << len(layout):
        raise ValueError("explicit computational-basis input required")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    package_raw = Path(package).read_bytes()
    (directory / "source.fslc").write_bytes(package_raw)
    cli = Path(fslc).resolve()
    metadata = json.loads(
        run(
            [
                cli,
                "emit-ibm",
                directory / "source.fslc",
                name,
                ",".join(map(str, layout)),
                entangler,
                ",".join(f"{a}:{b}" for a, b in edges) or "-",
                initial,
                axes,
                directory / "circuit.qasm",
            ]
        )
    )
    qasm = (directory / "circuit.qasm").read_text()
    if "if (" in qasm and snapshot["configuration"].get("conditional") is not True:
        raise ValueError("backend does not declare classical conditional support")
    reference = json.loads(
        run(
            [
                cli,
                "simulate-quantum",
                directory / "source.fslc",
                name,
                len(layout),
                f"basis:{initial}",
            ]
        )
    )
    expected = expected_distribution(reference, metadata["trace_values"], axes)
    request = payload(
        snapshot["configuration"]["backend_name"], qasm, shots, max_seconds
    )
    write_json(directory / "snapshot.json", snapshot)
    write_json(directory / "reference.json", reference)
    write_json(directory / "request.json", request)
    write_json(directory / "expected.json", expected)
    manifest = {
        "schema": "fission.ibm.bundle.v1",
        "backend": request["backend"],
        "instruction": name,
        "physical_qubits": layout,
        "initial_basis": initial,
        "observation_axes": axes,
        "trace_values": metadata["trace_values"],
        "entangler": entangler,
        "shots": shots,
        "max_seconds": max_seconds,
        "api_version": API_VERSION,
        "compiler_executable_sha256": digest(cli.read_bytes()),
        "hardware_execution": False,
        "target_validation": "snapshot-only; live recheck required",
        "files": {
            name: digest((directory / name).read_bytes())
            for name in [
                "source.fslc",
                "circuit.qasm",
                "snapshot.json",
                "reference.json",
                "request.json",
                "expected.json",
            ]
        },
    }
    write_json(directory / "manifest.json", manifest)
    return manifest


def load_bundle(directory):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    files = {
        "source.fslc",
        "circuit.qasm",
        "snapshot.json",
        "reference.json",
        "request.json",
        "expected.json",
    }
    if (
        manifest.get("schema") != "fission.ibm.bundle.v1"
        or set(manifest["files"]) != files
    ):
        raise ValueError("unsupported bundle manifest")
    for name in files:
        if digest((directory / name).read_bytes()) != manifest["files"][name]:
            raise ValueError("bundle hash mismatch")
    snapshot = read_json(directory / "snapshot.json")
    entangler, _ = target(snapshot, manifest["physical_qubits"])
    if (
        entangler != manifest["entangler"]
        or snapshot["configuration"]["backend_name"] != manifest["backend"]
        or manifest["api_version"] != API_VERSION
    ):
        raise ValueError("bundle target identity mismatch")
    wanted = payload(
        manifest["backend"],
        (directory / "circuit.qasm").read_text(),
        manifest["shots"],
        manifest["max_seconds"],
    )
    if read_json(directory / "request.json") != wanted:
        raise ValueError("request differs from bounded single-job contract")
    expected = expected_distribution(
        read_json(directory / "reference.json"),
        manifest["trace_values"],
        manifest["observation_axes"],
    )
    if read_json(directory / "expected.json") != expected:
        raise ValueError("expected distribution differs from retained FIR reference")
    return manifest, snapshot, wanted, expected


def submit(client, directory, receipt_directory):
    manifest, snapshot, request, _ = load_bundle(directory)
    current = client.snapshot(manifest["backend"])
    if (
        snapshot["synthetic"]
        or current["synthetic"]
        or snapshot.get("crn_sha256") != current["crn_sha256"]
        or snapshot["configuration"] != current["configuration"]
    ):
        raise ValueError(
            "live target differs or bundle is synthetic; prepare from a fresh snapshot"
        )
    usage = current["usage"]
    consumed, limit = usage["usage_consumed_seconds"], usage["usage_limit_seconds"]
    if (
        any(
            type(v) not in (int, float) or not math.isfinite(v) or v < 0
            for v in (consumed, limit)
        )
        or usage.get("usage_limit_reached") is not False
        or limit - consumed < manifest["max_seconds"]
    ):
        raise ValueError("insufficient verified Open Plan allowance")
    receipt_directory = Path(receipt_directory)
    receipt_directory.mkdir(parents=True, exist_ok=False)
    write_json(receipt_directory / "preflight.json", current)
    receipt = {
        "schema": "fission.ibm.receipt.v1",
        "state": "submission_outcome_unknown",
        "bundle_sha256": digest((Path(directory) / "manifest.json").read_bytes()),
        "backend": manifest["backend"],
        "hardware_execution": False,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(receipt_directory / "receipt.json", receipt)
    # Exactly one POST. A timeout can mean acceptance; never retry automatically.
    response = client.call("POST", "/jobs", request)
    write_json(receipt_directory / "response.json", response)
    if response.get("backend") != manifest["backend"]:
        raise ValueError(
            "provider backend mismatch; inspect saved response before any retry"
        )
    receipt.update(state="submitted", job_id=identifier(response["id"]))
    write_json(receipt_directory / "receipt.json", receipt)
    return receipt


def unwrap(value, kind):
    if not isinstance(value, dict) or value.get("__type__") != kind:
        raise ValueError(f"unsupported provider result wrapper: expected {kind}")
    return value["__value__"]


def unpack_bits(value, bits, shots):
    obj = unwrap(value, "BitArray")
    if obj["num_bits"] != bits:
        raise ValueError("provider classical width mismatch")
    compressed = unwrap(obj["array"], "ndarray")
    if not isinstance(compressed, str) or len(compressed) > MAX_BYTES:
        raise ValueError("only bounded compressed uint8 arrays are admitted")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(base64.b64decode(compressed, validate=True), MAX_BYTES + 1)
    if len(raw) > MAX_BYTES or not decoder.eof or decoder.unused_data:
        raise ValueError("invalid or oversized compressed array")
    if raw[:6] != b"\x93NUMPY" or raw[6:8] not in (b"\x01\x00", b"\x02\x00"):
        raise ValueError("only NPY v1/v2 uint8 arrays are admitted")
    size = 2 if raw[6] == 1 else 4
    length = int.from_bytes(raw[8 : 8 + size], "little")
    start = 8 + size
    if length > 65536 or start + length > len(raw):
        raise ValueError("invalid NPY header size")
    header = ast.literal_eval(raw[start : start + length].decode("ascii"))
    width = (bits + 7) // 8
    if header != {"descr": "|u1", "fortran_order": False, "shape": (shots, width)}:
        raise ValueError("only unparameterized shot-major uint8 storage is admitted")
    data = raw[start + length :]
    if len(data) != shots * width:
        raise ValueError("NPY payload size mismatch")
    rows = [
        int.from_bytes(data[i : i + width], "big") for i in range(0, len(data), width)
    ]
    if any(v >= 1 << bits for v in rows):
        raise ValueError("nonzero unused classical padding bits")
    return rows


def counts_from_result(result, manifest):
    obj = unwrap(result, "PrimitiveResult")
    pubs = obj["pub_results"]
    if len(pubs) != 1:
        raise ValueError("one scalar sampler PUB required")
    pub = pubs[0]
    if pub.get("__type__") not in ("SamplerPubResult", "PubResult"):
        raise ValueError("unsupported sampler PUB wrapper")
    data = unwrap(pub["__value__"]["data"], "DataBin")
    m, n = len(manifest["trace_values"]), len(manifest["physical_qubits"])
    if data["shape"] != [] or set(data["fields"]) != (
        {"out", "trace"} if m else {"out"}
    ):
        raise ValueError("unexpected or parameterized classical registers")
    final = unpack_bits(data["fields"]["out"], n, manifest["shots"])
    trace = (
        unpack_bits(data["fields"]["trace"], m, manifest["shots"])
        if m
        else [0] * manifest["shots"]
    )
    return Counter(t | (o << m) for t, o in zip(trace, final))


def compare_counts(counts, expected, manifest):
    bits = len(manifest["trace_values"]) + len(manifest["physical_qubits"])
    shots = manifest["shots"]
    if (
        not counts
        or any(
            type(k) is not int or not 0 <= k < 1 << bits or type(v) is not int or v <= 0
            for k, v in counts.items()
        )
        or sum(counts.values()) != shots
    ):
        raise ValueError("invalid joint outcome counts or shot count")
    predicted = {int(k): v for k, v in expected.items()}
    if (
        any(
            not 0 <= k < 1 << bits or not math.isfinite(v) or v < 0
            for k, v in predicted.items()
        )
        or abs(sum(predicted.values()) - 1) > 2e-10
    ):
        raise ValueError("invalid predicted probabilities")
    keys = counts.keys() | predicted.keys()
    errors = {k: abs(counts.get(k, 0) / shots - predicted.get(k, 0)) for k in keys}
    alpha = 0.01
    epsilon = math.sqrt(math.log(2 * (1 << bits) / alpha) / (2 * shots))
    return {
        "status": "compared",
        "shots": shots,
        "counts": {str(k): v for k, v in sorted(counts.items())},
        "total_variation_distance": sum(errors.values()) / 2,
        "maximum_bin_difference": max(errors.values()),
        "simultaneous_hoeffding_epsilon": epsilon,
        "alpha": alpha,
        "ideal_sampling_compatible": max(errors.values()) <= epsilon,
        "assumption": "IID shots from the ideal predicted distribution; device noise/drift can violate this model",
        "scope": "statistical observation, not compiler equivalence or noise correction",
    }


def collect(client, directory, receipt_directory, output):
    manifest, snapshot, _, expected = load_bundle(directory)
    receipt = read_json(Path(receipt_directory) / "receipt.json")
    if (
        receipt.get("state") != "submitted"
        or receipt["bundle_sha256"]
        != digest((Path(directory) / "manifest.json").read_bytes())
        or receipt["backend"] != manifest["backend"]
    ):
        raise ValueError("submitted receipt does not bind this bundle")
    preflight = read_json(Path(receipt_directory) / "preflight.json")
    if preflight["crn_sha256"] != digest(client.crn.encode()) or snapshot["synthetic"]:
        raise ValueError("receipt instance or hardware origin mismatch")
    job = identifier(receipt["job_id"])
    details = client.call("GET", f"/jobs/{job}")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "job.json", details)
    if details.get("backend") != manifest["backend"]:
        raise ValueError("job backend mismatch")
    if details.get("id") != job:
        raise ValueError("job identity mismatch")
    state = details.get("state", {}).get("status", details.get("status"))
    if state != "Completed":
        write_json(
            output / "comparison.json",
            {
                "status": "not-compared",
                "job_status": state,
                "hardware_execution": False,
            },
        )
        return False
    result = client.call("GET", f"/jobs/{job}/results")
    write_json(output / "result.json", result)
    counts = counts_from_result(result, manifest)
    comparison = compare_counts(counts, expected, manifest)
    comparison.update(
        calibration_id=details.get("calibration_id"),
        preflight_properties_timestamp=preflight["properties"]["last_update_date"],
        calibration_scope="pre-submission snapshot; not necessarily the job calibration",
        reported_usage=details.get("usage"),
        job_id=job,
        backend=manifest["backend"],
        hardware_execution=True,
        execution_evidence="provider reports completed physical-backend job; not independent hardware attestation",
        bundle_sha256=receipt["bundle_sha256"],
        result_sha256=digest(encoded(result)),
        preflight_sha256=digest(
            (Path(receipt_directory) / "preflight.json").read_bytes()
        ),
    )
    write_json(output / "comparison.json", comparison)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("snapshot")
    capture.add_argument("--backend", required=True)
    capture.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("prepare")
    for name in ("fslc", "package", "snapshot", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--instruction", required=True)
    p.add_argument("--layout", required=True)
    p.add_argument("--initial-basis", type=int, required=True)
    p.add_argument("--axes", required=True)
    p.add_argument("--shots", type=int, default=1024)
    p.add_argument("--max-seconds", type=int, default=60)
    for command in ("submit", "collect"):
        p = sub.add_parser(command)
        p.add_argument("--bundle", type=Path, required=True)
        p.add_argument("--receipt", type=Path, required=True)
        if command == "collect":
            p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "snapshot":
        if args.output.exists():
            raise ValueError("snapshot output already exists")
        write_json(args.output, Client.from_env().snapshot(args.backend))
    elif args.command == "prepare":
        prepare(
            args.fslc,
            args.package,
            args.instruction,
            read_json(args.snapshot),
            [int(q) for q in args.layout.split(",")],
            args.initial_basis,
            args.axes,
            args.shots,
            args.max_seconds,
            args.output,
        )
    elif args.command == "submit":
        print(json.dumps(submit(Client.from_env(), args.bundle, args.receipt)))
    elif not collect(Client.from_env(), args.bundle, args.receipt, args.output):
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise SystemExit(f"ibm-quantum: {exc}") from None
