#!/usr/bin/env python3
"""Regenerate the owned x86 package, projections and five locked executions.

These are artifact reproducibility checks, not an independent ISA oracle or
proof that the emitted sources behave like arbitrary x86 programs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "experiments/x86"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(*args: object) -> str:
    result = subprocess.run([str(arg) for arg in args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"command failed: {args[0]}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def reproduce(cli: Path, work: Path, cc: list[str], rustc: list[str]) -> dict:
    lock = json.loads((FIXTURES / "reproduction.lock.json").read_text())
    for name, expected in lock["input_sha256"].items():
        if digest(FIXTURES / name) != expected:
            raise ValueError(f"locked input hash mismatch: {name}")
    package = work / "scalar.fslxc"
    checked(cli, "compile", FIXTURES / "specs/scalar.fslx",
            FIXTURES / "specs/scalar-bodies.fsl", package)
    if digest(package) != lock["package_sha256"]:
        raise ValueError("owned x86 package hash mismatch")
    rows = []
    for fixture in lock["fixtures"]:
        name = fixture["name"]
        binary = fixture["kind"] == "binary"
        context = ([package, FIXTURES / fixture["binary"], fixture["address"], fixture["size"]]
                   if binary else [package, fixture["mode"], fixture["address"], fixture["hex"]])
        projections = {}
        for layer, suffix in (("fir", "fir"), ("c", "c"), ("rust", "rs")):
            output = work / f"{name}.{suffix}"
            checked(cli, "decompile-binary" if binary else "decompile", *context, layer, output)
            golden = FIXTURES / "outputs" / output.name
            if output.read_bytes() != golden.read_bytes() or digest(output) != fixture["output_sha256"][suffix]:
                raise ValueError(f"projection mismatch: {name}/{layer}")
            projections[layer] = digest(output)
            if suffix == "c" and cc:
                checked(*cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", "-c", output,
                        "-o", work / f"{name}.o")
            if suffix == "rs" and rustc:
                checked(*rustc, "--crate-name", "fsl_x86", "--crate-type", "lib", "--edition=2021",
                        "-D", "warnings", output, "-o", work / f"{name}.rlib")
        observed = checked(cli, "execute-binary" if binary else "execute", *context,
                           fixture["registers"], lock["flags"], lock["memory_base"],
                           lock["memory_hex"], lock["budget"])
        execution = FIXTURES / "outputs" / f"{name}.execution.txt"
        if observed != execution.read_text() or digest(execution) != fixture["output_sha256"]["execution.txt"]:
            raise ValueError(f"locked FIR execution mismatch: {name}")
        rows.append({"name": name, "projection_sha256": projections,
                     "execution": observed.strip()})
    return {"status": "passed", "expected_native_compiler_commit": lock["native_compiler_commit"],
            "package_sha256": digest(package), "fixtures": rows,
            "source_compilation": {"c": len(rows) if cc else "not requested",
                                   "rust": len(rows) if rustc else "not requested"},
            "scope": "five selected windows; FIR reference execution and deterministic source generation; no independent ISA execution oracle, emitted-source runtime parity or full x86 migration claim"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fsl-x86", type=Path, required=True)
    parser.add_argument("--cc", help="optional source compiler command, e.g. clang")
    parser.add_argument("--rustc", help="optional compiler command, e.g. rustup run stable rustc")
    parser.add_argument("--report", type=Path, default=ROOT / "artifacts/x86-reproduction.json")
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"status": "failed"}, indent=2) + "\n")
    with tempfile.TemporaryDirectory(prefix="fsl-x86-") as directory:
        report = reproduce(args.fsl_x86.resolve(), Path(directory),
                           shlex.split(args.cc) if args.cc else [],
                           shlex.split(args.rustc) if args.rustc else [])
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("Owned x86: package and 15 projections reproduced; five locked FIR executions reproduced")


if __name__ == "__main__":
    main()
