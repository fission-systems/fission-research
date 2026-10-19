#!/usr/bin/env python3
"""Audit frozen scalar-function evidence; no fresh execution is claimed here."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/pipeline/scalar-functions"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lock = json.loads((BASE / "source.lock.json").read_text())
    for name, expected in lock["files"].items():
        path = BASE / name
        if path.resolve().is_relative_to(BASE.resolve()) is False:
            raise ValueError("capture path leaves experiment")
        if digest(path) != expected:
            raise ValueError("capture hash mismatch: " + name)
    report = json.loads((BASE / "validation-macos.json").read_text())
    if report["native_commit"] != lock["native_commit"] or report["native_dirty"]:
        raise ValueError("capture did not use the clean pinned compiler")
    if report["status"] != "passed" or report["recompiled_comparisons"] != 24576:
        raise ValueError("unexpected captured comparison result")
    if report["source_reference_comparisons"] != 12288:
        raise ValueError("unexpected source-reference count")
    if digest(BASE / "inputs.bin") != report["input_sha256"]:
        raise ValueError("input corpus differs")
    if digest(BASE / "elf.fslpc") != report["catalog_sha256"]:
        raise ValueError("catalog differs")
    expected_cases = {
        (name, opt) for name in ("arithmetic", "choice", "masked") for opt in (1, 2)
    }
    if {
        (r["name"], r["original_optimization"]) for r in report["functions"]
    } != expected_cases or len(report["functions"]) != 6:
        raise ValueError("unexpected compilation cases")
    for row in report["functions"]:
        folder = BASE / "capture" / f"{row['name']}-O{row['original_optimization']}"
        for name, key in [
            ("original.c", "source_sha256"),
            ("original.elf", "elf_sha256"),
            ("decompiled/output.c", "c_sha256"),
            ("decompiled/output.fir", "fir_sha256"),
        ]:
            if digest(folder / name) != row[key]:
                raise ValueError("report/capture hash mismatch: " + name)
        if (folder / "text.bin").read_bytes()[: row["size"]].hex() != row["raw_hex"]:
            raise ValueError("original byte span differs")
        evidence = (folder / "decompiled/projection.txt").read_text()
        pipeline = (folder / "decompiled/pipeline.txt").read_text()
        source = (folder / "decompiled/output.c").read_text()
        if (
            "loader-route=owned-catalog" not in pipeline
            or "legacy-fallback=none" not in pipeline
        ):
            raise ValueError("missing owned route identity")
        if (
            "scalar-function-contract=1" not in evidence
            or "uint64_t recovered_candidate(" not in source
        ):
            raise ValueError("missing scalar function admission")
        for observed in row["executions"]:
            name = f"recompiled-O{observed['optimization']}-results.bin"
            result = folder / name
            if observed["cases"] != 2048 or digest(result) != observed["result_sha256"]:
                raise ValueError("recorded result differs")
            if result.read_bytes() != (folder / "original-results.bin").read_bytes():
                raise ValueError("captured original/recompiled outputs differ")
    print(f"verified {len(lock['files'])} captured files; historical comparisons=24576")


if __name__ == "__main__":
    main()
