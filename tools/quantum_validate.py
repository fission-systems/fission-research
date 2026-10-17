#!/usr/bin/env python3
"""Compare canonical FIR quantum execution with a separate dense-matrix oracle.

Own logical fixtures only. No QPU/hardware, physical binary, noise, performance
or formal equivalence claim. Python stdlib only; native engine has no new deps.
"""

import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/quantum/ideal-circuits/circuits.fsl"
LOCK = FIXTURE.parent / "source.lock.json"
CASES = {
    "bell": (2, [("h", 0), ("cx", 0, 1), ("measure", 0), ("measure", 1)]),
    "bell_coherent": (2, [("h", 0), ("cx", 0, 1)]),
    "hh": (1, [("h", 0), ("h", 0)]),
    "hzh": (1, [("h", 0), ("z", 0), ("h", 0)]),
    "feedforward": (1, [("h", 0), ("measure", 0), ("x_if", 0, 0), ("measure", 0)]),
    "reset_entangled": (2, [("h", 0), ("cx", 0, 1), ("reset", 0)]),
    "ghz": (
        3,
        [
            ("h", 0),
            ("cx", 0, 1),
            ("cx", 1, 2),
            ("measure", 0),
            ("measure", 1),
            ("measure", 2),
        ],
    ),
}
TOLERANCE = 2e-10


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace"))
    return result.stdout


def zero(n):
    return [[0j for _ in range(n)] for _ in range(n)]


def multiply(a, b):
    n = len(a)
    return [
        [sum(a[i][k] * b[k][j] for k in range(n)) for j in range(n)] for i in range(n)
    ]


def conjugate(a, rho):
    adjoint = [[complex(v).conjugate() for v in row] for row in zip(*a)]
    return multiply(multiply(a, rho), adjoint)


def local_matrix(qubits, target, local):
    # Tensor embedding by explicit input/output bit indices, rather than the
    # native engine's in-place amplitude-pair updates.
    n = 1 << qubits
    result = zero(n)
    for row in range(n):
        for col in range(n):
            if (row & ~(1 << target)) == (col & ~(1 << target)):
                result[row][col] = local[(row >> target) & 1][(col >> target) & 1]
    return result


def gate_matrix(qubits, op):
    h = 1 / math.sqrt(2)
    local = {"h": [[h, h], [h, -h]], "x": [[0, 1], [1, 0]], "z": [[1, 0], [0, -1]]}
    if op[0] != "cx":
        return local_matrix(qubits, op[1], local[op[0]])
    n = 1 << qubits
    result = zero(n)
    for col in range(n):
        row = col ^ (1 << op[2]) if col & (1 << op[1]) else col
        result[row][col] = 1
    return result


def oracle(qubits, ops, initial):
    rho = [[a * b.conjugate() for b in initial] for a in initial]
    # Each density is unnormalized: its trace is that measurement record's
    # probability. Reset sums Kraus channels, without exposing hidden outcomes.
    records = {(): rho}
    for op in ops:
        updated = {}
        for record, density in records.items():
            if op[0] == "measure":
                for bit in [0, 1]:
                    projector = [[1 - bit, 0], [0, bit]]
                    branch = conjugate(local_matrix(qubits, op[1], projector), density)
                    probability = sum(branch[i][i].real for i in range(len(branch)))
                    if probability > 0:
                        updated[record + (bit,)] = branch
            elif op[0] == "reset":
                k0 = local_matrix(qubits, op[1], [[1, 0], [0, 0]])
                k1 = local_matrix(qubits, op[1], [[0, 1], [0, 0]])
                left, right = conjugate(k0, density), conjugate(k1, density)
                updated[record] = [
                    [a + b for a, b in zip(ra, rb)] for ra, rb in zip(left, right)
                ]
            else:
                gate = op
                if op[0] == "x_if":
                    if record[op[2]] == 0:
                        updated[record] = density
                        continue
                    gate = ("x", op[1])
                updated[record] = conjugate(gate_matrix(qubits, gate), density)
        records = updated
    return records


def compare(observed, expected, n):
    if (
        not observed["branches"]
        or len(observed["density_matrix"]) != n * n
        or not math.isfinite(observed["total_probability"])
        or any(
            not all(math.isfinite(v) for v in pair)
            for pair in observed["density_matrix"]
        )
        or observed["qubits"] != n.bit_length() - 1
    ):
        raise ValueError("invalid diagnostic state shape or nonfinite values")
    if abs(observed["total_probability"] - 1) > TOLERANCE:
        raise ValueError("total probability drift")
    matrices = defaultdict(lambda: [0j] * (n * n))
    probabilities = defaultdict(float)
    for branch in observed["branches"]:
        record = tuple(bit for _, bit in branch["measurements"])
        amplitudes = [complex(*a) for a in branch["amplitudes"]]
        probability = branch["probability"]
        if (
            not 0 <= probability <= 1 + TOLERANCE
            or len(amplitudes) != n
            or any(
                not math.isfinite(a.real) or not math.isfinite(a.imag)
                for a in amplitudes
            )
            or [id for id, _ in branch["measurements"]] != list(range(len(record)))
            or any(bit not in (0, 1) for bit in record)
        ):
            raise ValueError("invalid state/probability")
        if abs(sum(abs(a) ** 2 for a in amplitudes) - 1) > TOLERANCE:
            raise ValueError("post-measurement state not normalized")
        if branch["values"] != list(record):
            raise ValueError("measurement SSA values differ from observable record")
        probabilities[record] += probability
        for i, a in enumerate(amplitudes):
            for j, b in enumerate(amplitudes):
                matrices[record][i * n + j] += probability * a * b.conjugate()
    expected_flat = {
        key: [x for row in value for x in row] for key, value in expected.items()
    }
    # Values below tolerance can have support differences from f64 cancellation;
    # compare the union, never silently drop an actual nonzero probability.
    error = 0.0
    for record in set(matrices) | set(expected_flat):
        a = matrices.get(record, [0j] * (n * n))
        b = expected_flat.get(record, [0j] * (n * n))
        error = max(error, max(abs(x - y) for x, y in zip(a, b)))
        wanted = sum(b[i * n + i].real for i in range(n))
        error = max(error, abs(probabilities.get(record, 0) - wanted))
    total = [sum(m[i] for m in matrices.values()) for i in range(n * n)]
    error = max(
        error,
        max(abs(complex(*a) - b) for a, b in zip(observed["density_matrix"], total)),
    )
    if error > TOLERANCE:
        raise ValueError(f"conditional quantum channel mismatch: {error}")
    return error


def inputs(qubits):
    n = 1 << qubits
    for index in range(n):
        vector = [0j] * n
        vector[index] = 1 + 0j
        yield f"basis:{index}", vector
    # Complex product states, including relative imaginary phase. These exercise
    # off-diagonal density entries, not just computational-basis histograms.
    h = 1 / math.sqrt(2)
    single = [[h, h], [h, -h], [h, 1j * h], [h, -1j * h]]
    for factors in itertools.product(single, repeat=qubits):
        vector = [
            math.prod(factors[q][(index >> q) & 1] for q in range(qubits))
            for index in range(n)
        ]
        yield "vector:" + ",".join(
            f"{a.real:.17g}:{a.imag:.17g}" for a in vector
        ), vector
    if qubits > 1:
        vector = [0j] * n
        vector[0], vector[-1] = h, 1j * h
        yield "vector:" + ",".join(
            f"{a.real:.17g}:{a.imag:.17g}" for a in vector
        ), vector


def validate(cli):
    lock = json.loads(LOCK.read_text())
    if digest(FIXTURE) != lock["source_sha256"]:
        raise ValueError("quantum fixture hash mismatch")
    reports = []
    with tempfile.TemporaryDirectory(prefix="fir-quantum-") as directory:
        work = Path(directory)
        package = work / "circuits.fslc"
        run([cli, "compile", FIXTURE, package])
        if digest(package) != lock["package_sha256"]:
            raise ValueError("quantum package hash mismatch")
        for name, (qubits, ops) in CASES.items():
            qasm, rebuilt = work / f"{name}.qasm", work / f"{name}.fslc"
            run([cli, "emit-qasm", package, name, qubits, qasm])
            run([cli, "import-qasm", qasm, rebuilt])
            if digest(qasm) != lock["qasm_sha256"][name]:
                raise ValueError("quantum QASM output changed")
            maximum, count = 0.0, 0
            for initial, vector in inputs(qubits):
                expected = oracle(qubits, ops, vector)
                original = json.loads(
                    run([cli, "simulate-quantum", package, name, qubits, initial])
                )
                projected = json.loads(
                    run([cli, "simulate-quantum", rebuilt, "circuit", qubits, initial])
                )
                maximum = max(maximum, compare(original, expected, 1 << qubits))
                maximum = max(maximum, compare(projected, expected, 1 << qubits))
                if original != projected:
                    raise ValueError("OpenQASM round-trip changed quantum execution")
                count += 1
            reports.append(
                {
                    "circuit": name,
                    "qubits": qubits,
                    "input_states": count,
                    "native_and_roundtrip_comparisons": 2 * count,
                    "maximum_absolute_error": maximum,
                    "qasm_sha256": digest(qasm),
                }
            )
        return {
            "status": "passed",
            "fixture_sha256": digest(FIXTURE),
            "package_sha256": digest(package),
            "package_version": 12,
            "tolerance": TOLERANCE,
            "circuits": reports,
            "input_states": sum(r["input_states"] for r in reports),
            "comparisons": sum(r["native_and_roundtrip_comparisons"] for r in reports),
            "scope": "authored ideal logical circuits; independent dense-density/Kraus calculation; own restricted QASM roundtrip; f64 finite-corpus evidence, not full equivalence or hardware execution",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=Path, required=True)
    parser.add_argument("--compiler-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=ROOT / "artifacts/quantum.json")
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('{"status":"failed"}\n')
    revision = (
        run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"]).decode().strip()
    )
    dirty = bool(
        run(["git", "-C", args.compiler_root, "status", "--porcelain"]).strip()
    )
    validator_sha = digest(Path(__file__))
    original_sha = digest(args.fslc)
    with tempfile.TemporaryDirectory(prefix="quantum-engine-") as temporary:
        frozen = Path(temporary) / "fslc"
        shutil.copy2(args.fslc, frozen)
        if digest(frozen) != original_sha:
            raise ValueError("compiler changed while taking executable snapshot")
        r = validate(frozen)
        r["compiler_executable_sha256"] = digest(frozen)
    if (
        digest(Path(__file__)) != validator_sha
        or revision
        != run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"]).decode().strip()
    ):
        raise ValueError("validator or compiler revision changed during run")
    r["validator_sha256"] = validator_sha
    r["compiler_commit"] = revision
    r["compiler_dirty"] = dirty or bool(
        run(["git", "-C", args.compiler_root, "status", "--porcelain"]).strip()
    )
    args.report.write_text(json.dumps(r, indent=2) + "\n")
    print(
        f"Quantum: {r['input_states']} input states / {r['comparisons']} conditional-state comparisons passed"
    )


if __name__ == "__main__":
    main()
