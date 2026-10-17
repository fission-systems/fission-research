#!/usr/bin/env python3
"""Check frozen fabric evidence and optionally a new offline reproduction report."""

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "experiments/fabric/initial-slices"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    require(path.resolve().is_relative_to(ROOT), "capture path outside repository")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(report_path=None):
    lock = json.loads((CAPTURE / "source.lock.json").read_text())
    for name, expected in lock["inputs"].items():
        require(digest(ROOT / name) == expected, f"input hash differs: {name}")
    for name, expected in lock["files"].items():
        require(digest(CAPTURE / name) == expected, f"artifact hash differs: {name}")
    if report_path:
        recorded = json.loads((CAPTURE / "validation-local.json").read_text())
        reproduced = json.loads(report_path.read_text())
        for key in [
            "schema",
            "compiler_commit",
            "compiler_dirty",
            "source_sha256",
            "package_sha256",
            "probe_sha256",
            "axes_sha256",
            "axes",
            "refusal_checks",
            "total_cases",
            "host_executions",
            "c_undefined_sanitizer",
            "generic_synthesis_count",
            "target_hardware_execution",
            "bitstreams_created",
            "scope",
        ]:
            require(reproduced[key] == recorded[key], f"reproduction differs: {key}")
        old = {row["kernel"]: row for row in recorded["results"]}
        new = {row["kernel"]: row for row in reproduced["results"]}
        require(old.keys() == new.keys(), "reproduced kernel set differs")
        for name, row in old.items():
            candidate = new[name]
            for key in [
                "cases",
                "input_slots",
                "output_slots",
                "fir_oracle",
                "rtl_oracle",
                "host_builds",
                "host_executions",
                "generic_synthesis",
                "synthesized_netlist_oracle",
                "generic_cells",
                "target_hardware_execution",
            ]:
                require(
                    candidate[key] == row[key], f"reproduction differs: {name}/{key}"
                )
            for key in [
                "design.v",
                "dependencies.dot",
                "input.csv",
                "reference.csv",
                "projection.c",
                "projection.rs",
                "tb.v",
            ]:
                require(
                    candidate["files"][key] == row["files"][key],
                    f"reproduced artifact differs: {name}/{key}",
                )
        analog = recorded["analog_approximation"]
        for key, expected in analog.items():
            actual = reproduced["analog_approximation"][key]
            require(
                math.isclose(actual, expected, rel_tol=0, abs_tol=1e-10)
                if type(expected) is float
                else actual == expected,
                f"analog reproduction differs: {key}",
            )
    return {
        "status": "matched",
        "frozen_files": len(lock["files"]),
        "reproduction_compared": report_path is not None,
        "target_hardware_execution": False,
        "scope": "Frozen authored evidence integrity; optional offline regeneration, not physical execution or formal equivalence.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.report), indent=2))


if __name__ == "__main__":
    main()
