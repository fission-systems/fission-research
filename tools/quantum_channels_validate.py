#!/usr/bin/env python3
"""Authored noisy/acyclic FIR fixtures against an independent density oracle.

No SDK dependency, QPU execution, calibration, or formal equivalence claim.
The earlier ideal-circuits experiment and its hashes remain immutable.
"""

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import shutil
import tempfile

import quantum_validate as dense

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/quantum/channels-cfg/circuits.fsl"
LOCK = FIXTURE.parent / "source.lock.json"


def cases():
    result = {}
    for channel in ("bit_flip", "phase_flip", "amplitude_damping"):
        for n, d in ((0, 1), (1, 1), (1, 2), (1, 255), (254, 255)):
            for target in (0, 1):
                name = f"{channel}_{n}_{d}_q{target}"
                text = (
                    f"quantum.h 0; quantum.cx 0,1; quantum.{channel} {target},{n},{d};"
                )
                result[name] = (
                    2,
                    0,
                    text,
                    [("h", 0), ("cx", 0, 1), (channel, target, n / d)],
                )
    result["cfg_correct"] = (
        2,
        5,
        "block entry() { quantum.h 0; quantum.cx 0,1; %a:u1=quantum.measure_z 0; branch.if %a, yes(%a), no(%a); } "
        "block yes(%b:u1) { quantum.x 1; branch join(%b); } "
        "block no(%c:u1) { branch join(%c); } "
        "block join(%d:u1) { %out:u1=quantum.measure_z 1; return; }",
        [
            ("h", 0),
            ("cx", 0, 1),
            ("measure", 0, 0),
            (
                "if",
                0,
                [("copy", 1, 0), ("x", 1), ("copy", 3, 1)],
                [("copy", 2, 0), ("copy", 3, 2)],
            ),
            ("measure", 1, 4),
        ],
    )
    # A second measurement is present only on one path. Noise is not observable
    # as a measurement, but its effect changes the later conditional density.
    result["cfg_noise"] = (
        2,
        6,
        "block entry() { quantum.h 0; %a:u1=quantum.measure_z 0; branch.if %a, noisy(%a), quiet(%a); } "
        "block noisy(%b:u1) { quantum.amplitude_damping 1,1,3; %m:u1=quantum.measure_z 1; branch join(%m); } "
        "block quiet(%c:u1) { quantum.phase_flip 1,1,2; branch join(%c); } "
        "block join(%d:u1) { quantum.x_if 0,%d; %out:u1=quantum.measure_z 0; return; }",
        [
            ("h", 0),
            ("measure", 0, 0),
            (
                "if",
                0,
                [
                    ("copy", 1, 0),
                    ("amplitude_damping", 1, 1 / 3),
                    ("measure", 1, 2),
                    ("copy", 4, 2),
                ],
                [("copy", 3, 0), ("phase_flip", 1, 0.5), ("copy", 4, 3)],
            ),
            ("if", 4, [("x", 0)], []),
            ("measure", 0, 5),
        ],
    )
    # Canonical block arguments must be transferred simultaneously.
    result["cfg_parameters"] = (
        1,
        4,
        "block entry() { %a:u1=int.const 0; %b:u1=int.const 1; quantum.h 0; branch swap(%b,%a); } "
        "block swap(%c:u1,%d:u1) { quantum.x_if 0,%c; quantum.bit_flip 0,1,3; branch.if %d, yes(), no(); } "
        "block yes() { quantum.x 0; return; } block no() { quantum.z 0; return; }",
        [
            ("const", 0, 0),
            ("const", 1, 1),
            ("h", 0),
            ("copy", 2, 1),
            ("copy", 3, 0),
            ("if", 2, [("x", 0)], []),
            ("bit_flip", 0, 1 / 3),
            ("if", 3, [("x", 0)], [("z", 0)]),
        ],
    )
    return result


CASES = cases()


def fixture_source():
    rows = [
        "language quantum.channels.reference { byte_order little; address_unit byte;"
    ]
    for selector, (name, (_, _, text, _)) in enumerate(CASES.items(), 1):
        rows.append(
            f'instruction {name} {{ opcode {selector}; mnemonic "{name}"; '
            'evidence "authored" "https://github.com/Qiskit/qiskit-aer/blob/main/qiskit_aer/noise/errors/standard_errors.py" "channels-v1" '
            '"Synthetic logical selector, not a physical QPU opcode or calibrated noise."; '
            f"semantics {{ {text} }} }}"
        )
    return "\n".join(rows) + "\n}\n"


def channel(qubits, op, rho):
    kind, target, p = op
    if kind == "amplitude_damping":
        matrices = ([[1, 0], [0, math.sqrt(1 - p)]], [[0, math.sqrt(p)], [0, 0]])
    else:
        unitary = [[0, 1], [1, 0]] if kind == "bit_flip" else [[1, 0], [0, -1]]
        matrices = (
            [[math.sqrt(1 - p), 0], [0, math.sqrt(1 - p)]],
            [[math.sqrt(p) * v for v in row] for row in unitary],
        )
    terms = [
        dense.conjugate(dense.local_matrix(qubits, target, k), rho) for k in matrices
    ]
    return [
        [sum(t[i][j] for t in terms) for j in range(len(rho))] for i in range(len(rho))
    ]


def execute(qubits, ops, states):
    # Unnormalized density operators, grouped by observable measurement history
    # and classical SSA slots. Hidden environment alternatives are summed here.
    for op in ops:
        updated = []
        for record, values, rho in states:
            kind = op[0]
            if kind == "if":
                updated.extend(
                    execute(
                        qubits,
                        op[2] if values[op[1]] else op[3],
                        [(record, values, rho)],
                    )
                )
            elif kind in ("const", "copy"):
                v = list(values)
                v[op[1]] = op[2] if kind == "const" else v[op[2]]
                updated.append((record, tuple(v), rho))
            elif kind == "measure":
                for bit in (0, 1):
                    projected = dense.conjugate(
                        dense.local_matrix(qubits, op[1], [[1 - bit, 0], [0, bit]]), rho
                    )
                    if sum(projected[i][i].real for i in range(len(rho))) > 0:
                        v = list(values)
                        v[op[2]] = bit
                        updated.append((record + ((op[2], bit),), tuple(v), projected))
            elif kind in ("bit_flip", "phase_flip", "amplitude_damping"):
                updated.append((record, values, channel(qubits, op, rho)))
            else:
                updated.append(
                    (
                        record,
                        values,
                        dense.conjugate(dense.gate_matrix(qubits, op), rho),
                    )
                )
        states = updated
    return states


def oracle(qubits, value_count, ops, initial):
    rho = [[a * b.conjugate() for b in initial] for a in initial]
    return execute(qubits, ops, [((), (None,) * value_count, rho)])


def compare(observed, expected, qubits, value_count):
    n = 1 << qubits
    if (
        observed["hardware_execution"] is not False
        or observed["qubits"] != qubits
        or not observed["branches"]
    ):
        raise ValueError("invalid quantum diagnostics")
    actual = defaultdict(lambda: [0j] * (n * n))
    wanted = defaultdict(lambda: [0j] * (n * n))
    for record, values, rho in expected:
        key = (record, values)
        wanted[key] = [a + b for a, b in zip(wanted[key], sum(rho, []))]
    for branch in observed["branches"]:
        p = branch["probability"]
        vector = [complex(*a) for a in branch["amplitudes"]]
        values = branch["values"]
        record = tuple(tuple(v) for v in branch["measurements"])
        if (
            not math.isfinite(p)
            or not 0 < p <= 1 + dense.TOLERANCE
            or len(vector) != n
            or any(
                not math.isfinite(v.real) or not math.isfinite(v.imag) for v in vector
            )
            or abs(sum(abs(v) ** 2 for v in vector) - 1) > dense.TOLERANCE
            or len(values) != value_count
            or any(v not in (None, 0, 1) for v in values)
            or any(
                len(v) != 2 or not 0 <= v[0] < value_count or v[1] not in (0, 1)
                for v in record
            )
        ):
            raise ValueError("invalid branch state")
        key = (record, tuple(values))
        actual[key] = [
            a + p * x * y.conjugate()
            for a, (x, y) in zip(actual[key], ((x, y) for x in vector for y in vector))
        ]
    error = 0.0
    for key in actual.keys() | wanted.keys():
        error = max(error, max(abs(a - b) for a, b in zip(actual[key], wanted[key])))
    total = [sum(a[i] for a in actual.values()) for i in range(n * n)]
    reported = observed["density_matrix"]
    if len(reported) != n * n or any(not math.isfinite(x) for a in reported for x in a):
        raise ValueError("invalid density matrix")
    error = max(error, max(abs(complex(*a) - b) for a, b in zip(reported, total)))
    p = observed["total_probability"]
    trace = sum(total[i * n + i].real for i in range(n))
    if (
        not math.isfinite(p)
        or abs(p - 1) > dense.TOLERANCE
        or abs(trace - p) > dense.TOLERANCE
        or error > dense.TOLERANCE
    ):
        raise ValueError(f"channel/CFG mismatch: {error}")
    return error


def validate(cli):
    if FIXTURE.read_text() != fixture_source():
        raise ValueError("fixture and independent case inventory disagree")
    lock = json.loads(LOCK.read_text())
    if dense.digest(FIXTURE) != lock["source_sha256"]:
        raise ValueError("fixture hash mismatch")
    if (
        dense.digest(Path(__file__)) != lock["validator_sha256"]
        or dense.digest(Path(dense.__file__)) != lock["dense_oracle_sha256"]
    ):
        raise ValueError("oracle source hash mismatch")
    reports = []
    with tempfile.TemporaryDirectory(prefix="fir-channels-") as directory:
        package = Path(directory) / "circuits.fslc"
        dense.run([cli, "compile", FIXTURE, package])
        if dense.digest(package) != lock["package_sha256"]:
            raise ValueError("package hash mismatch")
        for name, (qubits, count, _, ops) in CASES.items():
            maximum, comparisons = 0.0, 0
            for initial, vector in dense.inputs(qubits):
                observed = json.loads(
                    dense.run([cli, "simulate-quantum", package, name, qubits, initial])
                )
                maximum = max(
                    maximum,
                    compare(
                        observed, oracle(qubits, count, ops, vector), qubits, count
                    ),
                )
                comparisons += 1
            reports.append(
                {
                    "circuit": name,
                    "comparisons": comparisons,
                    "maximum_absolute_error": maximum,
                }
            )
        return {
            "status": "passed",
            "source_sha256": dense.digest(FIXTURE),
            "package_sha256": dense.digest(package),
            "package_version": 13,
            "tolerance": dense.TOLERANCE,
            "cases": reports,
            "comparisons": sum(r["comparisons"] for r in reports),
            "scope": "authored rational noise channels and acyclic u1 CFG; conditional density and SSA comparison; no hardware/calibration/binary/formal-equivalence claim",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=Path, required=True)
    parser.add_argument("--compiler-root", type=Path, required=True)
    parser.add_argument(
        "--report", type=Path, default=ROOT / "artifacts/quantum-channels.json"
    )
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('{"status":"failed"}\n')

    def revision():
        return (
            dense.run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"])
            .decode()
            .strip()
        )

    def dirty():
        return bool(
            dense.run(
                ["git", "-C", args.compiler_root, "status", "--porcelain"]
            ).strip()
        )

    before, was_dirty = revision(), dirty()
    hashes = {
        p: dense.digest(p)
        for p in (Path(__file__), Path(dense.__file__), FIXTURE, LOCK)
    }
    original_sha = dense.digest(args.fslc)
    with tempfile.TemporaryDirectory(prefix="channels-engine-") as directory:
        frozen = Path(directory) / "fslc"
        shutil.copy2(args.fslc, frozen)
        if dense.digest(frozen) != original_sha:
            raise ValueError("compiler changed during snapshot")
        result = validate(frozen)
        result["compiler_executable_sha256"] = dense.digest(frozen)
    if revision() != before or any(dense.digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("source changed during validation")
    result.update(
        compiler_commit=before,
        compiler_dirty=was_dirty or dirty(),
        validator_sha256=hashes[Path(__file__)],
        dense_oracle_sha256=hashes[Path(dense.__file__)],
    )
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(
        f"Quantum channels/CFG: {len(result['cases'])} cases / {result['comparisons']} comparisons passed"
    )


if __name__ == "__main__":
    main()
