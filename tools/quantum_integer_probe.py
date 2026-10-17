#!/usr/bin/env python3
"""Integer-controlled quantum CFG on authored FIR, with a dense-matrix oracle.

No QPU connection, device calibration, binary decoding or formal equivalence.
Python integers and closed-form loop summaries are independent of native FIR
integer helpers; quantum states use unnormalized dense density operators.
"""

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

import quantum_validate as dense

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/quantum/integer-cfg"


def cases():
    result = {}
    for bits in (8, 16, 32, 64):
        for count in (0, 1, 3, 6):
            text = f"""block entry() {{ %count:u{bits}=int.const {count}; branch head(%count); }}
block head(%i:u{bits}) {{ %zero:u{bits}=int.const 0; %done:u1=int.eq %i,%zero; branch.if %done, exit(%i), step(%i); }}
block step(%j:u{bits}) {{ quantum.x 0; %one:u{bits}=int.const 1; %next:u{bits}=u{bits}.sub %j,%one; branch head(%next); }}
block exit(%out:u{bits}) {{ return; }}"""
            result[f"counter_u{bits}_{count}"] = ("counter", (count,), text, 8)
    for bits in (8, 64):
        start = (1 << bits) - 2  # signed -2; increments through -1, 0 to 1.
        text = f"""block entry() {{ %start:i{bits}=int.const {start}; branch head(%start); }}
block head(%i:i{bits}) {{ %limit:i{bits}=int.const 1; %more:u1=int.slt %i,%limit; branch.if %more, step(%i), exit(%i); }}
block step(%j:i{bits}) {{ quantum.x 0; %one:i{bits}=int.const 1; %next:i{bits}=i{bits}.add.wrap %j,%one; branch head(%next); }}
block exit(%out:i{bits}) {{ return; }}"""
        result[f"signed_loop_i{bits}"] = ("signed_loop", (start,), text, 8)
    for ty in ("u1", "u8", "u32", "u64", "i8", "i64"):
        bits = int(ty[1:])
        mask = (1 << bits) - 1
        for index, (a, b) in enumerate(((mask, 1), (1 << (bits - 1), mask), (0, 0))):
            predicate = "slt" if ty[0] == "i" else "ult"
            text = f"""%a:{ty}=int.const {a}; %b:{ty}=int.const {b};
%sum:{ty}={ty}.add.wrap %a,%b; %sub:{ty}={ty}.sub %a,%b;
%and:{ty}={ty}.and %a,%b; %or:{ty}={ty}.or %a,%b; %xor:{ty}={ty}.xor %a,%b;
%less:u1=int.{predicate} %a,%b; %eq:u1=int.eq %a,%b;
quantum.x_if 0,%less; quantum.cx 0,1;"""
            result[f"arithmetic_{ty}_{index}"] = ("arithmetic", (ty, a, b), text, 9)
    for sign in ("u", "i"):
        for a in (128, 255):
            text = f"""%a:{sign}8=int.const {a};
%wide:{sign}64=int.{'zext' if sign == 'u' else 'sext'} %a;
%middle:{sign}16=int.trunc %wide; %back:{sign}8=int.trunc %middle;
%eq:u1=int.eq %a,%back; quantum.x_if 0,%eq; quantum.cx 0,1;"""
            result[f"conversion_{sign}_{a}"] = ("conversion", (sign, a), text, 5)
    result["adaptive_count"] = (
        "adaptive",
        (),
        """block entry() { %m:u1=quantum.measure_z 0; %count:u8=int.zext %m; branch head(%count); }
block head(%i:u8) { %zero:u8=int.const 0; %done:u1=int.eq %i,%zero; branch.if %done, exit(%i), step(%i); }
block step(%j:u8) { quantum.x 1; %one:u8=int.const 1; %next:u8=u8.sub %j,%one; branch head(%next); }
block exit(%out:u8) { return; }""",
        9,
    )
    result["two_entry_cycle"] = (
        "irreducible",
        (),
        """block entry() { %m:u1=quantum.measure_z 0; %count:u8=int.const 3; branch.if %m, left(%count), right(%count); }
block left(%a:u8) { quantum.x 1; %za:u8=int.const 0; %da:u1=int.eq %a,%za; %oa:u8=int.const 1; %na:u8=u8.sub %a,%oa; branch.if %da, exit(%a), right(%na); }
block right(%b:u8) { quantum.z 1; %zb:u8=int.const 0; %db:u1=int.eq %b,%zb; %ob:u8=int.const 1; %nb:u8=u8.sub %b,%ob; branch.if %db, exit(%b), left(%nb); }
block exit(%out:u8) { return; }""",
        13,
    )
    return result


CASES = cases()


def source():
    rows = [
        "language quantum.integer.reference { byte_order little; address_unit byte;"
    ]
    for selector, (name, (_, _, text, _)) in enumerate(CASES.items(), 1):
        rows.append(
            f'instruction {name} {{ opcode {selector}; mnemonic "{name}"; '
            'evidence "self-authored" "synthetic" "integer-cfg-v1" '
            '"Authored logical selector; integer-controlled quantum CFG on a classical host."; '
            f"semantics {{ {text} }} }}"
        )
    return "\n".join(rows) + "\n}\n"


def transform(rho, gate):
    return dense.conjugate(dense.gate_matrix(2, gate), rho)


def oracle(case, vector):
    kind, args, _, value_count = case
    rho = [[a * b.conjugate() for b in vector] for a in vector]
    if kind == "counter":
        (count,) = args
        values = (
            count,
            0,
            0,
            1,
            1 if count else None,
            1 if count else None,
            0 if count else None,
            0,
        )
        if count % 2:
            rho = transform(rho, ("x", 0))
    elif kind == "signed_loop":
        values = (args[0], 1, 1, 0, 0, 1, 1, 1)
        rho = transform(rho, ("x", 0))  # three X operations.
    elif kind == "arithmetic":
        ty, a, b = args
        bits = int(ty[1:])
        modulus = 1 << bits
        signed = lambda x: x - modulus if x >= modulus // 2 else x
        less = int(signed(a) < signed(b) if ty[0] == "i" else a < b)
        values = (
            a,
            b,
            (a + b) % modulus,
            (a - b) % modulus,
            a & b,
            a | b,
            a ^ b,
            less,
            int(a == b),
        )
        if less:
            rho = transform(rho, ("x", 0))
        rho = transform(rho, ("cx", 0, 1))
    elif kind == "conversion":
        sign, a = args
        wide = (a - 256) % (1 << 64) if sign == "i" else a
        values = (a, wide, wide % (1 << 16), a, 1)
        rho = transform(transform(rho, ("x", 0)), ("cx", 0, 1))
    else:
        result = []
        for bit in (0, 1):
            projected = dense.conjugate(
                dense.local_matrix(2, 0, [[1 - bit, 0], [0, bit]]), rho
            )
            if sum(projected[i][i].real for i in range(4)) == 0:
                continue
            if kind == "adaptive":
                values = (
                    bit,
                    bit,
                    0,
                    0,
                    1,
                    1 if bit else None,
                    1 if bit else None,
                    0 if bit else None,
                    0,
                )
                if bit:
                    projected = transform(projected, ("x", 1))
            else:
                # Two entries into one SCC. Four alternating visits with counters
                # 3,2,1,0; record latest definitions even on the final exit edge.
                values = [None] * value_count
                values[0:2] = [bit, 3]
                for visit, count in enumerate((3, 2, 1, 0)):
                    left = bool(bit) == (visit % 2 == 0)
                    start = 2 if left else 7
                    values[start : start + 5] = [
                        count,
                        0,
                        int(count == 0),
                        1,
                        (count - 1) % 256,
                    ]
                    projected = transform(projected, ("x" if left else "z", 1))
                values[-1] = 0
            result.append((((0, bit),), tuple(values), projected))
        return result
    return [((), tuple(values), rho)]


def compare(observed, expected, value_count):
    """Compare full instruments, grouping hidden alternatives by exact SSA/trace."""
    if observed.get("hardware_execution") is not False or observed.get("qubits") != 2:
        raise ValueError("invalid execution identity")
    actual = defaultdict(lambda: [0j] * 16)
    wanted = defaultdict(lambda: [0j] * 16)
    for record, values, rho in expected:
        key = (record, values)
        wanted[key] = [a + b for a, b in zip(wanted[key], sum(rho, []))]
    for branch in observed["branches"]:
        p = branch["probability"]
        vector = [complex(*v) for v in branch["amplitudes"]]
        values = tuple(branch["values"])
        record = tuple(tuple(v) for v in branch["measurements"])
        if (
            not math.isfinite(p)
            or not 0 < p <= 1 + dense.TOLERANCE
            or len(vector) != 4
            or any(
                not math.isfinite(v.real) or not math.isfinite(v.imag) for v in vector
            )
            or abs(sum(abs(v) ** 2 for v in vector) - 1) > dense.TOLERANCE
            or len(values) != value_count
            or any(
                v is not None and (type(v) is not int or not 0 <= v < 1 << 64)
                for v in values
            )
            or any(
                len(v) != 2 or not 0 <= v[0] < value_count or v[1] not in (0, 1)
                for v in record
            )
        ):
            raise ValueError("invalid integer/quantum branch")
        key = (record, values)
        actual[key] = [
            a + p * x * y.conjugate()
            for a, (x, y) in zip(actual[key], ((x, y) for x in vector for y in vector))
        ]
    if actual.keys() != wanted.keys():
        raise ValueError("SSA slots or measurement history differ")
    maximum = max(
        abs(a - b) for key in wanted for a, b in zip(actual[key], wanted[key])
    )
    total = [sum(row[i] for row in actual.values()) for i in range(16)]
    reported = [complex(*v) for v in observed["density_matrix"]]
    if len(reported) != 16 or not math.isfinite(observed["total_probability"]):
        raise ValueError("invalid aggregate diagnostics")
    if any(not math.isfinite(v.real) or not math.isfinite(v.imag) for v in reported):
        raise ValueError("nonfinite density")
    maximum = max(
        maximum,
        max(abs(a - b) for a, b in zip(total, reported)),
        abs(sum(total[i].real for i in (0, 5, 10, 15)) - 1),
        abs(observed["total_probability"] - 1),
    )
    if maximum > dense.TOLERANCE:
        raise ValueError(f"integer/quantum instrument differs by {maximum}")
    return maximum


def validate(cli):
    if (FIXTURE / "circuits.fsl").read_text() != source():
        raise ValueError("authored fixture differs from case inventory")
    lock = json.loads((FIXTURE / "source.lock.json").read_text())
    for name, digest in lock["files"].items():
        if dense.digest(FIXTURE / name) != digest:
            raise ValueError("archived experiment input hash mismatch")
    if (
        dense.digest(Path(__file__)) != lock["validator_sha256"]
        or dense.digest(Path(dense.__file__)) != lock["dense_oracle_sha256"]
    ):
        raise ValueError("oracle source hash mismatch")
    reports = []
    refused = 0
    with tempfile.TemporaryDirectory(prefix="quantum-integer-") as directory:
        package = Path(directory) / "circuits.fslc"
        dense.run([cli, "compile", FIXTURE / "circuits.fsl", package])
        if dense.digest(package) != lock["package_sha256"]:
            raise ValueError("portable package hash mismatch")
        for name, case in CASES.items():
            maximum = 0.0
            comparisons = 0
            for initial, vector in dense.inputs(2):
                envelope = json.loads(
                    dense.run(
                        [
                            cli,
                            "simulate-quantum-bounded",
                            package,
                            name,
                            2,
                            initial,
                            65536,
                            12,
                            4096,
                        ]
                    )
                )
                if (
                    envelope["status"] != "complete"
                    or envelope["frontier"]
                    or envelope["result"] is None
                ):
                    raise ValueError("finite counter CFG did not complete")
                expected = oracle(case, vector)
                maximum = max(maximum, compare(envelope["result"], expected, case[3]))
                comparisons += 1
                if case[0] in ("arithmetic", "conversion"):
                    strict = json.loads(
                        dense.run([cli, "simulate-quantum", package, name, 2, initial])
                    )
                    maximum = max(maximum, compare(strict, expected, case[3]))
                    comparisons += 1
            projection = subprocess.run(
                [
                    str(cli),
                    "emit-qasm",
                    str(package),
                    name,
                    "2",
                    str(Path(directory) / "output.qasm"),
                ],
                capture_output=True,
                timeout=30,
            )
            if not projection.returncode or (Path(directory) / "output.qasm").exists():
                raise ValueError("unsupported projection was emitted")
            refused += 1
            reports.append(
                {
                    "name": name,
                    "inputs": 21,
                    "comparisons": comparisons,
                    "maximum_absolute_error": maximum,
                }
            )
        # Explicit zero step stop preserves u64 values before the next quantum effect.
        stopped = subprocess.run(
            [
                str(cli),
                "simulate-quantum-bounded",
                str(package),
                "counter_u64_6",
                "2",
                "basis:0",
                "1",
                "12",
                "4096",
            ],
            capture_output=True,
            timeout=30,
        )
        partial = json.loads(stopped.stdout)
        if (
            stopped.returncode != 1
            or partial["status"] != "incomplete"
            or partial["result"] is not None
            or partial["limit"] != "steps"
            or partial["completed_probability"] != 0
            or partial["frontier_probability"] != 1
            or partial["frontier"][0]["branch"]["values"] != [6] + [None] * 7
        ):
            raise ValueError(
                "stopped integer CFG lost frontier or became a terminal result"
            )
        return {
            "status": "passed",
            "cases": len(reports),
            "inputs": sum(r["inputs"] for r in reports),
            "comparisons": sum(r["comparisons"] for r in reports),
            "projection_refusals": refused,
            "partial_checks": 1,
            "maximum_absolute_error": max(r["maximum_absolute_error"] for r in reports),
            "tolerance": dense.TOLERANCE,
            "source_sha256": dense.digest(FIXTURE / "circuits.fsl"),
            "package_sha256": dense.digest(package),
            "compiler_executable_sha256": dense.digest(cli),
            "inventory": reports,
            "scope": "Authored 1..64 bit integer-controlled quantum CFG; finite counters, measurement-selected count and a two-entry cycle. No QPU, current calibration, general OpenQASM, memory/CPU/GPU effects, QPU binary execution or formal equivalence.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=Path, required=True)
    parser.add_argument("--compiler-root", type=Path, required=True)
    parser.add_argument(
        "--report", type=Path, default=ROOT / "artifacts/quantum-integer.json"
    )
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('{"status":"failed"}\n')
    paths = [
        Path(__file__),
        Path(dense.__file__),
        FIXTURE / "circuits.fsl",
        FIXTURE / "source.lock.json",
    ]
    frozen_hashes = {p: dense.digest(p) for p in paths}
    before = (
        dense.run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"])
        .decode()
        .strip()
    )
    dirty = bool(
        dense.run(["git", "-C", args.compiler_root, "status", "--porcelain"]).strip()
    )
    with tempfile.TemporaryDirectory(prefix="quantum-integer-engine-") as directory:
        frozen = Path(directory) / "fslc"
        original = dense.digest(args.fslc)
        shutil.copy2(args.fslc, frozen)
        if dense.digest(frozen) != original:
            raise ValueError("compiler changed during snapshot")
        report = validate(frozen)
    if (
        before
        != dense.run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"])
        .decode()
        .strip()
    ):
        raise ValueError("compiler revision changed")
    report.update(
        compiler_commit=before,
        compiler_dirty=dirty
        or bool(
            dense.run(
                ["git", "-C", args.compiler_root, "status", "--porcelain"]
            ).strip()
        ),
        validator_sha256=dense.digest(Path(__file__)),
    )
    if any(dense.digest(p) != h for p, h in frozen_hashes.items()):
        raise ValueError("probe input changed during run")
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"Quantum integer CFG: {report['cases']} cases / {report['comparisons']} instrument comparisons passed"
    )


if __name__ == "__main__":
    main()
