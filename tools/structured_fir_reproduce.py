#!/usr/bin/env python3
"""Reproduce owned structured FIR artifacts and bounded native CLI behavior."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def checked(fslc, *args):
    return subprocess.run([str(fslc), *map(str, args)], capture_output=True,
                          text=True, check=True, timeout=60).stdout


def reproduce(fslc, golden, work, lock):
    source = golden / "stack-branch-join.fsl"
    if hashlib.sha256(source.read_bytes()).hexdigest() != lock["source_sha256"]:
        raise ValueError("structured FIR source hash mismatch")
    package = work / "stack-branch-join.fslc"
    checked(fslc, "compile", source, package)
    if hashlib.sha256(package.read_bytes()).hexdigest() != lock["package_sha256"]:
        raise ValueError("structured FIR package hash mismatch")
    for layer, suffix in [("fir", "fir"), ("c", "c"), ("rust", "rs")]:
        output = work / f"stack-branch-join.{suffix}"
        checked(fslc, "emit", package, "70", layer, output)
        if output.read_bytes() != (golden / output.name).read_bytes():
            raise ValueError(f"structured FIR output mismatch: {layer}")
        if hashlib.sha256(output.read_bytes()).hexdigest() != lock["outputs"][suffix]:
            raise ValueError(f"structured FIR output hash mismatch: {layer}")
    values = [0, 1, 8, 9, 10, 11, 255, 65535, 0x7fffffff, 0x80000000, 0xffffffff, 0x100000000]
    for value in values:
        raw = value & 0xffffffff
        result = (raw + (1 if raw < 10 else 2)) & 0xffffffff
        output = checked(fslc, "execute", package, "70", "2", "77", value)
        if output.strip() != f"status=Success stack=[77, {result}]":
            raise ValueError("structured FIR independent CLI oracle mismatch")
    for args, expected in [(["0", "9"], "status=InvalidState stack=[9]"),
                           (["1"], "status=StackUnderflow stack=[]")]:
        if checked(fslc, "execute", package, "70", *args).strip() != expected:
            raise ValueError("structured FIR failure changed active state")
    return {"status": "passed", "scope": "self-authored semantic-body CFG; no binary function lifting claim",
            "package_sha256": lock["package_sha256"], "artifacts_identical": 3,
            "native_cli_oracle_cases": len(values), "native_cli_failure_cases": 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, default=ROOT / "artifacts/structured-fir.json")
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"status": "failed"}, indent=2) + "\n")
    golden = ROOT / "experiments/fir/structured-control"
    lock = tomllib.loads((golden / "control.lock.toml").read_text())
    with tempfile.TemporaryDirectory(prefix="fir-control-") as directory:
        report = reproduce(args.fslc.resolve(), golden, pathlib.Path(directory), lock)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("structured FIR: 3 outputs/package hash identical; 12 CLI oracle and 2 failure cases passed")


if __name__ == "__main__":
    main()
