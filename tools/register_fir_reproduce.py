#!/usr/bin/env python3
"""Reproduce owned integer conversion/register CFG artifacts with native CLI oracles."""
import argparse
import hashlib
import json
import pathlib
import tempfile
import tomllib

from structured_fir_reproduce import checked

ROOT = pathlib.Path(__file__).resolve().parents[1]


def reproduce(fslc, golden, work, lock):
    name = "register-branch-convert"
    source = golden / f"{name}.fsl"
    if hashlib.sha256(source.read_bytes()).hexdigest() != lock["source_sha256"]:
        raise ValueError("register FIR source hash mismatch")
    package = work / f"{name}.fslc"
    checked(fslc, "compile", source, package)
    if hashlib.sha256(package.read_bytes()).hexdigest() != lock["package_sha256"]:
        raise ValueError("register FIR package hash mismatch")
    for layer, suffix in [("fir", "fir"), ("c", "c"), ("rust", "rs")]:
        output = work / f"{name}.{suffix}"
        checked(fslc, "emit-bytes", package, "register.branch.convert", "10a20000", layer, output)
        if output.read_bytes() != (golden / output.name).read_bytes():
            raise ValueError(f"register FIR output mismatch: {layer}")
        if hashlib.sha256(output.read_bytes()).hexdigest() != lock["outputs"][suffix]:
            raise ValueError(f"register FIR output hash mismatch: {layer}")
    count = 0
    for value in [0, 1, 7, 127, 128, 129, 254, 255, 256, 0xffffffff, 0xffffffffffffffff]:
        for source_index, destination, auxiliary in [(0, 1, 2), (0, 0, 0), (0, 1, 0), (0, 1, 1)]:
            registers = [value, 77, 88]
            raw = registers[source_index] % 256
            signed = raw if raw < 128 else raw - 256
            expected = registers.copy()
            expected[auxiliary] = raw
            expected[destination] = signed % (1 << 32)
            negative = int(signed < 0)
            word = 0xa000 | source_index | (destination << 4) | (auxiliary << 8)
            encoded = word.to_bytes(4, "little").hex()
            output = checked(fslc, "execute-state", package, "register.branch.convert", encoded,
                             ",".join(map(str, registers)), "1,0,1")
            if output.strip() != f"status=Success registers={expected} flags={[negative, 1, negative]}":
                raise ValueError("register FIR independent CLI oracle mismatch")
            count += 1
    failures = [("f0a20000", "9,10,11", "0,0,0"),
                ("f0a20000", "9,10,11", "0,2,0"),
                ("10a20000", "9,10,11", "0,0")]
    for encoded, registers, flags in failures:
        expected_registers = list(map(int, registers.split(",")))
        expected_flags = list(map(int, flags.split(",")))
        output = checked(fslc, "execute-state", package, "register.branch.convert", encoded, registers, flags)
        if output.strip() != f"status=InvalidState registers={expected_registers} flags={expected_flags}":
            raise ValueError("register FIR failure changed state")
    return {"status": "passed", "scope": "self-authored register/flag semantic-body CFG; no ISA/function/hardware oracle claim",
            "package_sha256": lock["package_sha256"], "artifacts_identical": 3,
            "native_cli_oracle_cases": count, "native_cli_failure_cases": len(failures)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, default=ROOT / "artifacts/register-fir.json")
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"status": "failed"}, indent=2) + "\n")
    golden = ROOT / "experiments/fir/register-control"
    lock = tomllib.loads((golden / "register.lock.toml").read_text())
    with tempfile.TemporaryDirectory(prefix="fir-register-") as directory:
        report = reproduce(args.fslc.resolve(), golden, pathlib.Path(directory), lock)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("register FIR: package/3 output hashes identical; 44 CLI oracle and 3 failure cases passed")


if __name__ == "__main__":
    main()
