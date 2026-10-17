#!/usr/bin/env python3
"""Bounded quantum loops and historical calibration-parameter transfer.

No live QPU or noise-correction claim. External JSON is archived source evidence;
the owned executable description remains textual FSL and binary FSLC.
"""

import argparse
from decimal import Decimal, ROUND_HALF_EVEN
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

import quantum_validate as common
import quantum_channels_validate as channels

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/quantum/bounded-calibration"


def picoseconds(value, unit):
    factors = {
        "s": Decimal(10) ** 12,
        "ms": Decimal(10) ** 9,
        "us": Decimal(10) ** 6,
        "ns": Decimal(1000),
    }
    if unit not in factors or not value.is_finite() or value < 0:
        raise ValueError("unsupported calibration quantity/unit")
    exact = value * factors[unit]
    rounded = exact.to_integral_value(rounding=ROUND_HALF_EVEN)
    if abs(exact - rounded) > Decimal("0.5") or not 0 <= rounded < 2**64:
        raise ValueError("calibration time cannot be represented with <=0.5 ps error")
    return int(rounded), str(exact - rounded)


LOOP = "block entry() { branch loop(); } block loop() { quantum.x 0; %m:u1=quantum.measure_z 0; branch.if %m, loop(), done(%m); } block done(%out:u1) { return; }"
RETRY = "block entry() { branch loop(); } block loop() { quantum.h 0; %m:u1=quantum.measure_z 0; branch.if %m, loop(), done(); } block done() { return; }"


def inventory():
    props = json.loads((FIXTURE / "props_manila.json").read_text(), parse_float=Decimal)
    rows = []
    for physical, entries in enumerate(props["qubits"]):
        metrics = {entry["name"]: entry for entry in entries}
        times = {}
        errors = {}
        for name in ("T1", "T2"):
            e = metrics[name]
            times[name], errors[name] = picoseconds(Decimal(e["value"]), e["unit"])
        if not times["T1"] or not times["T2"] or times["T2"] > 2 * times["T1"]:
            raise ValueError("unphysical T1/T2 snapshot row; no silent clipping")
        gate = next(
            g for g in props["gates"] if g["gate"] == "id" and g["qubits"] == [physical]
        )
        length = next(p for p in gate["parameters"] if p["name"] == "gate_length")
        gate_ps, gate_error = picoseconds(Decimal(length["value"]), length["unit"])
        for duration in (0, gate_ps, 100_000, 100_000_000):
            rows.append(
                {
                    "name": f"idle_q{physical}_{duration}",
                    "physical_qubit": physical,
                    "logical_model_slot": 0,
                    "duration_ps": duration,
                    "t1_ps": times["T1"],
                    "t2_ps": times["T2"],
                    "rounding_residual_ps": errors,
                    "gate_length_residual_ps": gate_error,
                    "snapshot_date": props["last_update_date"],
                    "raw_t1_seconds": float(
                        (Decimal(times["T1"]) + Decimal(errors["T1"]))
                        / Decimal(10) ** 12
                    ),
                    "raw_t2_seconds": float(
                        (Decimal(times["T2"]) + Decimal(errors["T2"]))
                        / Decimal(10) ** 12
                    ),
                    "raw_duration_seconds": float(
                        (
                            Decimal(duration)
                            + (Decimal(gate_error) if duration == gate_ps else 0)
                        )
                        / Decimal(10) ** 12
                    ),
                }
            )
    return props, rows


def source():
    _, rows = inventory()
    bodies = [("terminating_loop", LOOP), ("retry_loop", RETRY)]
    bodies.extend(
        (
            r["name"],
            f"quantum.relaxation 0,{r['duration_ps']},{r['t1_ps']},{r['t2_ps']};",
        )
        for r in rows
    )
    text = [
        "language quantum.execution.reference { byte_order little; address_unit byte;"
    ]
    for selector, (name, body) in enumerate(bodies, 1):
        text.append(
            f'instruction {name} {{ opcode {selector}; mnemonic "{name}"; evidence "authored-model" "https://github.com/Qiskit/qiskit-ibm-runtime/blob/7a7fa0f6d5fd2d284611b62d5546e12112a1985a/qiskit_ibm_runtime/fake_provider/backends/manila/props_manila.json" "7a7fa0f6d5fd2d284611b62d5546e12112a1985a" "Logical reference only; physical qubit to logical model slot 0 mapping is in the experiment inventory; no device calibration/correction execution."; semantics {{ {body} }} }}'
        )
    return "\n".join(text) + "\n}\n"


def relaxation_density(vector, duration, t1, t2):
    # Direct exponential action on density blocks, independent of the native
    # amplitude-damping/phase-flip Kraus decomposition and branch enumeration.
    rho = [[a * b.conjugate() for b in vector] for a in vector]
    population = math.exp(-duration / t1)
    coherence = math.exp(-duration / t2)
    n = len(rho)
    return [
        [
            (
                rho[i][j] + (1 - population) * rho[i | 1][j | 1]
                if i % 2 == 0 and j % 2 == 0
                else (
                    population * rho[i][j]
                    if i % 2 == 1 and j % 2 == 1
                    else coherence * rho[i][j]
                )
            )
            for j in range(n)
        ]
        for i in range(n)
    ]


def validate(cli):
    lock = json.loads((FIXTURE / "source.lock.json").read_text())
    if common.digest(Path(__file__)) != lock["validator_sha256"]:
        raise ValueError("validator hash mismatch")
    for name, digest in lock["dependencies"].items():
        if common.digest(ROOT / "tools" / name) != digest:
            raise ValueError("oracle dependency hash mismatch")
    for name in ["execution.fsl", "props_manila.json", "LICENSE.txt"]:
        if common.digest(FIXTURE / name) != lock[name + "_sha256"]:
            raise ValueError("locked input hash mismatch")
    if (FIXTURE / "execution.fsl").read_text() != source():
        raise ValueError("FSL/inventory mismatch")
    reports = []
    maximum = 0.0
    conversion = 0.0
    with tempfile.TemporaryDirectory(prefix="quantum-execution-") as directory:
        package = Path(directory) / "execution.fslc"
        common.run([cli, "compile", FIXTURE / "execution.fsl", package])
        if common.digest(package) != lock["package_sha256"]:
            raise ValueError("package hash mismatch")
        for initial, vector in common.inputs(1):
            run = json.loads(
                common.run(
                    [
                        cli,
                        "simulate-quantum-bounded",
                        package,
                        "terminating_loop",
                        1,
                        initial,
                        1000,
                        12,
                        4096,
                    ]
                )
            )
            if run["status"] != "complete" or run["frontier"] or run["result"] is None:
                raise ValueError("terminating loop failed to complete")
            expected = []
            for bit, p in [(0, abs(vector[1]) ** 2), (1, abs(vector[0]) ** 2)]:
                if p == 0:
                    continue
                record = ((0, 0),) if bit == 0 else ((0, 1), (0, 0))
                expected.append((record, (0, 0), [[p + 0j, 0j], [0j, 0j]]))
            maximum = max(maximum, channels.compare(run["result"], expected, 1, 2))
        stopped = subprocess.run(
            list(
                map(
                    str,
                    [
                        cli,
                        "simulate-quantum-bounded",
                        package,
                        "retry_loop",
                        1,
                        "basis:0",
                        1000,
                        4,
                        4096,
                    ],
                )
            ),
            capture_output=True,
            timeout=30,
        )
        if (
            stopped.returncode != 1
            or b"incomplete quantum execution" not in stopped.stderr
        ):
            raise ValueError("incomplete CLI run must signal nonzero failure")
        partial = json.loads(stopped.stdout)
        if (
            partial["status"] != "incomplete"
            or partial["result"] is not None
            or partial["limit"] != "splits"
        ):
            raise ValueError("retry frontier was reported as terminal output")
        if (
            abs(partial["completed_probability"] - 15 / 16) > 1e-12
            or abs(partial["frontier_probability"] - 1 / 16) > 1e-12
        ):
            raise ValueError("retry probability mass lost or normalized")
        # The pending state is just before the refused next measurement.
        if (
            len(partial["frontier"]) != 1
            or len(partial["frontier"][0]["branch"]["measurements"]) != 4
        ):
            raise ValueError("retry frontier history/location lost")
        _, rows = inventory()
        for row in rows:
            maximum_row = 0.0
            for initial, vector in common.inputs(2):
                duration = row["duration_ps"]
                rho = relaxation_density(vector, duration, row["t1_ps"], row["t2_ps"])
                observed = json.loads(
                    common.run(
                        [cli, "simulate-quantum", package, row["name"], 2, initial]
                    )
                )
                maximum_row = max(
                    maximum_row, channels.compare(observed, [((), (), rho)], 2, 0)
                )
                raw = relaxation_density(
                    vector,
                    row["raw_duration_seconds"],
                    row["raw_t1_seconds"],
                    row["raw_t2_seconds"],
                )
                conversion = max(
                    conversion,
                    max(abs(a - b) for ra, rb in zip(rho, raw) for a, b in zip(ra, rb)),
                )
            reports.append(
                {**row, "comparisons": 21, "maximum_absolute_error": maximum_row}
            )
            maximum = max(maximum, maximum_row)
        if conversion > 1e-7:
            raise ValueError(
                "calibration parameter quantization exceeds declared model bound"
            )
        return {
            "status": "passed",
            "calibration_comparisons": sum(r["comparisons"] for r in reports),
            "loop_inputs": 6,
            "partial_retry_checks": 1,
            "maximum_absolute_error": maximum,
            "maximum_time_quantization_density_error": conversion,
            "tolerance": common.TOLERANCE,
            "source_sha256": common.digest(FIXTURE / "execution.fsl"),
            "package_sha256": common.digest(package),
            "package_version": 14,
            "compiler_executable_sha256": common.digest(cli),
            "inventory": reports,
            "scope": "bounded u1 measurement loops and zero-temperature Markovian idle models from a historical snapshot; no QPU binary execution, live calibration, readout/gate/crosstalk fitting, correction or hardware equivalence",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=Path, required=True)
    parser.add_argument("--compiler-root", type=Path, required=True)
    parser.add_argument(
        "--report", type=Path, default=ROOT / "artifacts/quantum-execution.json"
    )
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('{"status":"failed"}\n')
    frozen_hashes = {
        p: common.digest(p)
        for p in [
            Path(__file__),
            Path(common.__file__),
            Path(channels.__file__),
            FIXTURE / "execution.fsl",
            FIXTURE / "source.lock.json",
            FIXTURE / "props_manila.json",
            FIXTURE / "LICENSE.txt",
        ]
    }
    before = (
        common.run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"])
        .decode()
        .strip()
    )
    dirty = bool(
        common.run(["git", "-C", args.compiler_root, "status", "--porcelain"]).strip()
    )
    with tempfile.TemporaryDirectory(prefix="quantum-execution-engine-") as directory:
        frozen = Path(directory) / "fslc"
        original_sha = common.digest(args.fslc)
        shutil.copy2(args.fslc, frozen)
        if common.digest(frozen) != original_sha:
            raise ValueError("compiler changed during snapshot")
        r = validate(frozen)
    if (
        before
        != common.run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"])
        .decode()
        .strip()
    ):
        raise ValueError("compiler revision changed")
    r.update(
        compiler_commit=before,
        compiler_dirty=dirty
        or bool(
            common.run(
                ["git", "-C", args.compiler_root, "status", "--porcelain"]
            ).strip()
        ),
        validator_sha256=common.digest(Path(__file__)),
    )
    if any(common.digest(path) != digest for path, digest in frozen_hashes.items()):
        raise ValueError("probe inputs or oracle source changed during run")
    args.report.write_text(json.dumps(r, indent=2) + "\n")
    print(
        f"Quantum execution: {r['calibration_comparisons']} idle-model comparisons / {r['loop_inputs']} terminating inputs / partial retry passed"
    )


if __name__ == "__main__":
    main()
