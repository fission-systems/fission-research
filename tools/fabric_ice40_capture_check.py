#!/usr/bin/env python3
"""Validate frozen iCE40 research evidence and optionally compare a new run."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "experiments/fabric/ice40-hx8k"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    require(path.resolve().is_relative_to(ROOT), "Frozen path outside repository")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(report_path=None):
    lock = json.loads((CAPTURE / "source.lock.json").read_text())
    for name, expected in lock["files"].items():
        require(digest(ROOT / name) == expected, f"Frozen artifact differs: {name}")
    recorded = json.loads((CAPTURE / "validation-local.json").read_text())
    for name, expected in recorded["inputs"].items():
        require(digest(ROOT / name) == expected, f"Experiment input differs: {name}")
    for report in [recorded] + (
        [json.loads(report_path.read_text())] if report_path else []
    ):
        require(
            report["proofs"]
            == report["counterexample_controls"]
            == report["bitstreams_created"]
            == 8,
            "Expected eight proofs, SAT counterexamples and bitstreams",
        )
        require(
            not report["device_execution"]
            and not report["board_pin_constraints"]
            and not report["compiler_dirty"],
            "Execution scope or compiler state differs",
        )
        require(report["mapped_simulation_cases"] == 145336, "Case count differs")
        require(
            report["package_sha256"]
            == digest(ROOT / "experiments/fabric/initial-slices/kernels.fslc"),
            "Canonical package differs",
        )
    if report_path:
        reproduced = json.loads(report_path.read_text())
        for key in [
            "schema",
            "compiler_commit",
            "compiler_dirty",
            "package_sha256",
            "inputs",
            "tools",
            "formal_scope",
            "timing_scope",
        ]:
            require(reproduced[key] == recorded[key], f"Reproduction differs: {key}")
        old = {r["kernel"]: r for r in recorded["results"]}
        new = {r["kernel"]: r for r in reproduced["results"]}
        require(
            len(old) == len(new) == 8 and old.keys() == new.keys(), "Kernel set differs"
        )
        for name, row in old.items():
            candidate = new[name]
            for key in row.keys() - {"files"}:
                require(
                    candidate[key] == row[key], f"Reproduction differs: {name}/{key}"
                )
            # The pinned Wasm flow + fixed seed should reproduce the actual configuration.
            # CPU timings/logs and synthesis-generated temporary names are not compared.
            for artifact in [
                "design.v",
                "adapter.v",
                "oracle-proof.ys",
                "mutation.ys",
                "mutant.v",
                "synthesis.ys",
                "input.csv",
                "reference.csv",
                "tb.v",
                "design.bin",
            ]:
                require(
                    candidate["files"][artifact] == row["files"][artifact],
                    f"Reproduced artifact differs: {name}/{artifact}",
                )
    return {
        "status": "matched",
        "frozen_files": len(lock["files"]),
        "reproduction_compared": report_path is not None,
        "proofs": 8,
        "bitstreams_created": 8,
        "device_execution": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.report), indent=2))


if __name__ == "__main__":
    main()
