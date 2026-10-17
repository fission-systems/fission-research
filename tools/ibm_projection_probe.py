#!/usr/bin/env python3
"""Offline IBM lowering/oracle/codec evidence; never invokes a QPU or credentials."""

import argparse
import base64
from collections import Counter
import cmath
import itertools
import math
from pathlib import Path
import re
import shutil
import struct
import tempfile
import zlib

import ibm_quantum as adapter
import quantum_validate as dense

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/quantum/ibm-open-plan"
SOURCE = ROOT / "experiments/quantum/ideal-circuits/circuits.fsl"


def emitted_distribution(qasm, layout, trace_count):
    """Interpret only emitted physical instructions using unnormalized densities.

    This parser is a qualification oracle, not an IBM parser or a runtime path.
    Native gate matrices and reset channels are independent of the FIR executor.
    """
    n = len(layout)
    dimension = 1 << n
    rho = dense.zero(dimension)
    rho[0][0] = 1
    states = [([None] * trace_count, [None] * n, rho)]
    logical = {physical: i for i, physical in enumerate(layout)}
    for line in qasm.splitlines():
        if not line or line.startswith(("//", "OPENQASM", "include", "bit[")):
            continue
        condition = None
        if line.startswith("if "):
            match = re.fullmatch(r"if \(trace\[(\d+)\] == 1\) \{ (x \$\d+;) \}", line)
            if not match:
                raise ValueError("unsupported conditional in qualification oracle")
            condition = int(match[1])
            line = match[2]
        measured = re.fullmatch(r"(trace|out)\[(\d+)\] = measure \$(\d+);", line)
        gate = re.fullmatch(r"(x|sx|reset|rz\((?:-?pi/2|pi)\)) \$(\d+);", line)
        pair = re.fullmatch(r"(cx|cz) \$(\d+), \$(\d+);", line)
        if not (measured or gate or pair):
            raise ValueError("unknown physical instruction")
        updated = []
        for trace, final, rho in states:
            if condition is not None and trace[condition] != 1:
                updated.append((trace, final, rho))
                continue
            if measured:
                register, slot, q = (
                    measured[1],
                    int(measured[2]),
                    logical[int(measured[3])],
                )
                for bit in (0, 1):
                    projected = dense.conjugate(
                        dense.local_matrix(n, q, [[1 - bit, 0], [0, bit]]), rho
                    )
                    if sum(projected[i][i].real for i in range(dimension)) > 0:
                        t, o = trace[:], final[:]
                        (t if register == "trace" else o)[slot] = bit
                        updated.append((t, o, projected))
                continue
            if pair:
                a, b = logical[int(pair[2])], logical[int(pair[3])]
                if pair[1] == "cx":
                    unitary = dense.gate_matrix(n, ("cx", a, b))
                else:
                    unitary = dense.zero(dimension)
                    for i in range(dimension):
                        unitary[i][i] = -1 if i & (1 << a) and i & (1 << b) else 1
                updated.append((trace, final, dense.conjugate(unitary, rho)))
                continue
            kind, q = gate[1], logical[int(gate[2])]
            if kind == "reset":
                terms = [
                    dense.conjugate(dense.local_matrix(n, q, k), rho)
                    for k in ([[1, 0], [0, 0]], [[0, 1], [0, 0]])
                ]
                transformed = [
                    [sum(t[i][j] for t in terms) for j in range(dimension)]
                    for i in range(dimension)
                ]
            else:
                if kind == "sx":
                    local = [[(1 + 1j) / 2, (1 - 1j) / 2], [(1 - 1j) / 2, (1 + 1j) / 2]]
                elif kind == "x":
                    local = [[0, 1], [1, 0]]
                else:
                    angle = {
                        "rz(pi/2)": math.pi / 2,
                        "rz(-pi/2)": -math.pi / 2,
                        "rz(pi)": math.pi,
                    }[kind]
                    local = [
                        [cmath.exp(-1j * angle / 2), 0],
                        [0, cmath.exp(1j * angle / 2)],
                    ]
                transformed = dense.conjugate(dense.local_matrix(n, q, local), rho)
            updated.append((trace, final, transformed))
        states = updated
    probabilities = Counter()
    for trace, final, rho in states:
        if None in trace or None in final:
            raise ValueError("unmeasured output")
        outcome = sum(v << i for i, v in enumerate(trace + final))
        probabilities[outcome] += sum(rho[i][i].real for i in range(dimension))
    return probabilities


def mock_result(counts, trace_bits, qubits):
    """Modeled RuntimeEncoder framing, not a captured provider response."""
    rows = [k for k, count in sorted(counts.items()) for _ in range(count)]

    def array(values, bits):
        width = (bits + 7) // 8
        header = repr(
            {"descr": "|u1", "fortran_order": False, "shape": (len(values), width)}
        ).encode()
        header += b" " * ((64 - (10 + len(header) + 1) % 64) % 64) + b"\n"
        raw = (
            b"\x93NUMPY\x01\x00"
            + struct.pack("<H", len(header))
            + header
            + b"".join(v.to_bytes(width, "big") for v in values)
        )
        return {
            "__type__": "BitArray",
            "__value__": {
                "num_bits": bits,
                "array": {
                    "__type__": "ndarray",
                    "__value__": base64.b64encode(zlib.compress(raw)).decode(),
                },
            },
        }

    fields = {"out": array([k >> trace_bits for k in rows], qubits)}
    if trace_bits:
        fields["trace"] = array([k & ((1 << trace_bits) - 1) for k in rows], trace_bits)
    return {
        "__type__": "PrimitiveResult",
        "__value__": {
            "pub_results": [
                {
                    "__type__": "SamplerPubResult",
                    "__value__": {
                        "data": {
                            "__type__": "DataBin",
                            "__value__": {
                                "field_names": list(fields),
                                "shape": [],
                                "fields": fields,
                            },
                        },
                        "metadata": {},
                    },
                }
            ],
            "metadata": {"synthetic": True},
        },
    }


def deterministic_counts(expected, shots):
    probabilities = {int(k): p for k, p in expected.items()}
    counts = {k: math.floor(p * shots) for k, p in probabilities.items()}
    residual = shots - sum(counts.values())
    for k in sorted(
        probabilities, key=lambda k: (-(probabilities[k] * shots - counts[k]), k)
    )[:residual]:
        counts[k] += 1
    return Counter({k: v for k, v in counts.items() if v})


def validate(cli):
    lock = adapter.read_json(FIXTURE / "source.lock.json")
    for path, sha in lock["inputs"].items():
        if dense.digest(ROOT / path) != sha:
            raise ValueError("probe input hash mismatch")
    reports = []
    with tempfile.TemporaryDirectory(prefix="ibm-projection-") as directory:
        root = Path(directory)
        package = root / "circuits.fslc"
        dense.run([cli, "compile", SOURCE, package])
        if dense.digest(package) != lock["package_sha256"]:
            raise ValueError("source package hash changed")
        for entangler in ("cx", "cz"):
            snapshot = adapter.read_json(FIXTURE / "synthetic-snapshot.json")
            config = snapshot["configuration"]
            config["basis_gates"][-1] = entangler
            config["supported_instructions"][3] = entangler
            config["gates"][-1]["name"] = entangler
            for name, (qubits, _) in dense.CASES.items():
                maximum = 0
                comparisons = 0
                for initial in range(1 << qubits):
                    for axes in map("".join, itertools.product("XYZ", repeat=qubits)):
                        bundle = root / "bundle"
                        adapter.prepare(
                            cli,
                            package,
                            name,
                            snapshot,
                            [7, 3, 5][:qubits],
                            initial,
                            axes,
                            1024,
                            60,
                            bundle,
                        )
                        manifest, _, _, expected = adapter.load_bundle(bundle)
                        observed = emitted_distribution(
                            (bundle / "circuit.qasm").read_text(),
                            manifest["physical_qubits"],
                            len(manifest["trace_values"]),
                        )
                        error = max(
                            abs(observed.get(k, 0) - expected.get(str(k), 0))
                            for k in observed.keys() | {int(k) for k in expected}
                        )
                        if error > dense.TOLERANCE:
                            raise ValueError(
                                f"physical lowering changed instrument: {name}/{axes}: {error}"
                            )
                        counts = deterministic_counts(expected, manifest["shots"])
                        decoded = adapter.counts_from_result(
                            mock_result(counts, len(manifest["trace_values"]), qubits),
                            manifest,
                        )
                        if decoded != counts:
                            raise ValueError(
                                "joint shot codec changed trace/final correlation"
                            )
                        comparison = adapter.compare_counts(decoded, expected, manifest)
                        if not comparison["ideal_sampling_compatible"]:
                            raise ValueError("modeled sampling fixture inconsistent")
                        maximum = max(maximum, error)
                        comparisons += 1
                        shutil.rmtree(bundle)
                reports.append(
                    {
                        "entangler": entangler,
                        "instruction": name,
                        "comparisons": comparisons,
                        "maximum_absolute_error": maximum,
                    }
                )
        return {
            "status": "passed",
            "hardware_execution": False,
            "network_requests": 0,
            "comparisons": sum(r["comparisons"] for r in reports),
            "codec_comparisons": sum(r["comparisons"] for r in reports),
            "maximum_absolute_error": max(r["maximum_absolute_error"] for r in reports),
            "tolerance": dense.TOLERANCE,
            "source_sha256": dense.digest(SOURCE),
            "package_sha256": dense.digest(package),
            "compiler_executable_sha256": dense.digest(cli),
            "inventory": reports,
            "scope": "authored seven linear logical circuits, basis inputs and every X/Y/Z terminal observation; native CX/CZ lowering, independent dense physical-gate oracle and modeled Runtime codec. No IBM parser, live API acceptance, QPU or noise validation.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=Path, required=True)
    parser.add_argument("--compiler-root", type=Path, required=True)
    parser.add_argument(
        "--report", type=Path, default=ROOT / "artifacts/ibm-projection.json"
    )
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('{"status":"failed"}\n')
    paths = [
        Path(__file__),
        Path(adapter.__file__),
        Path(dense.__file__),
        SOURCE,
        FIXTURE / "synthetic-snapshot.json",
        FIXTURE / "source.lock.json",
    ]
    frozen = {p: dense.digest(p) for p in paths}
    before = (
        dense.run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"])
        .decode()
        .strip()
    )
    dirty = bool(
        dense.run(["git", "-C", args.compiler_root, "status", "--porcelain"]).strip()
    )
    with tempfile.TemporaryDirectory(prefix="ibm-frozen-engine-") as directory:
        cli = Path(directory) / "fslc"
        original = dense.digest(args.fslc)
        shutil.copy2(args.fslc, cli)
        if dense.digest(cli) != original:
            raise ValueError("compiler changed during snapshot")
        report = validate(cli)
    if before != dense.run(
        ["git", "-C", args.compiler_root, "rev-parse", "HEAD"]
    ).decode().strip() or any(dense.digest(p) != sha for p, sha in frozen.items()):
        raise ValueError("probe inputs changed during run")
    report.update(
        compiler_commit=before,
        compiler_dirty=dirty
        or bool(
            dense.run(
                ["git", "-C", args.compiler_root, "status", "--porcelain"]
            ).strip()
        ),
        validator_sha256=dense.digest(Path(__file__)),
        adapter_sha256=dense.digest(Path(adapter.__file__)),
    )
    adapter.write_json(args.report, report)
    print(
        f"IBM offline projection: {report['comparisons']} instrument / {report['codec_comparisons']} modeled codec comparisons passed; no QPU"
    )


if __name__ == "__main__":
    main()
