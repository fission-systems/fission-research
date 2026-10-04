#!/usr/bin/env python3
"""Reproduce bounded canonical FIR sequences, byte origins, and state handoff."""
import argparse
import hashlib
import json
import pathlib
import struct
import tempfile
import tomllib

from structured_fir_reproduce import checked

ROOT = pathlib.Path(__file__).resolve().parents[1]


def verify_envelope(data, package, raw, base, registers, flags):
    if len(data) < 96 or data[:8] != b"FSLSEQ\0\x01":
        raise ValueError("sequence envelope header mismatch")
    actual = struct.unpack_from("<QIIII", data, 8)
    if actual != (base, registers, flags, len(package), len(raw)):
        raise ValueError("sequence envelope contract/length mismatch")
    if data[96:] != package + raw:
        raise ValueError("sequence envelope byte window/package mismatch")
    if data[32:64] != hashlib.sha256(package).digest() or data[64:96] != hashlib.sha256(raw).digest():
        raise ValueError("sequence envelope origin hash mismatch")


def reproduce(fslc, golden, work, lock):
    reports = []
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    for fixture in lock["fixtures"]:
        name = fixture["name"]
        source = golden / fixture["source"]
        if digest(source) != fixture["source_sha256"]:
            raise ValueError("sequence source hash mismatch")
        package = work / f"{name}.fslc"
        sequence = work / f"{name}.fslseq"
        checked(fslc, "compile", source, package)
        if digest(package) != fixture["package_sha256"]:
            raise ValueError("sequence package hash mismatch")
        checked(fslc, "compose-sequence", package, fixture["profile"], fixture["base_address"],
                fixture["register_count"], fixture["flag_count"], fixture["input_hex"], sequence)
        if digest(sequence) != fixture["sequence_sha256"]:
            raise ValueError("sequence container hash mismatch")
        verify_envelope(sequence.read_bytes(), package.read_bytes(), bytes.fromhex(fixture["input_hex"]),
                        fixture["base_address"], fixture["register_count"], fixture["flag_count"])
        for layer, suffix in [("fir", "fir"), ("c", "c"), ("rust", "rs")]:
            output = work / f"{name}.{suffix}"
            checked(fslc, "emit-sequence", sequence, layer, output)
            if output.read_bytes() != (golden / output.name).read_bytes() or digest(output) != fixture[f"{suffix}_sha256"]:
                raise ValueError(f"sequence output mismatch: {name}/{layer}")
        values = [0, 1, 0xffffffff, 0x100000000, 0xffffffffffffffff, 0x7fffffffffffffff]
        if name == "scalar-chain":
            inputs = [(a, b) for a in values for b in values]
            seed = 0x1a29b45c667788
            for _ in range(64):
                seed = (seed*6364136223846793005+1) % (1 << 64)
                a = seed
                seed = (seed*6364136223846793005+1) % (1 << 64)
                inputs.append((a, seed))
            for a, b in inputs:
                registers = [a % (1 << 32), a >> 32, b % (1 << 32), b >> 32, 99, 99, 77]
                full = a + b
                expected = registers.copy()
                expected[4] = full % (1 << 32)
                expected[5] = (full >> 32) % (1 << 32)
                flags = [full >> 64, 1]
                observed = checked(fslc, "execute-sequence", sequence, ",".join(map(str, registers)), "1,1")
                if observed.strip() != f"status=Success registers={expected} flags={flags}":
                    raise ValueError("sequence independent scalar oracle mismatch")
            failure_inputs = [("9,10,11,12,13,14", "0,1"), ("9,10,11,12,13,14,15", "0,2")]
        elif name == "register-chain":
            inputs = [0, 1, 7, 126, 127, 128, 129, 254, 255, 256, 0xffffffff, 0xffffffffffffffff]
            for value in inputs:
                expected = [value, 77, 88]
                flags = [0, 0, 0]
                for src, dst, aux in [(0, 1, 2), (1, 2, 0), (2, 0, 1)]:
                    raw = expected[src] % 256
                    signed = raw if raw < 128 else raw - 256
                    expected[aux] = raw
                    expected[dst] = signed % (1 << 32)
                    flags = [int(signed < 0), 1, int(signed < 0)]
                observed = checked(fslc, "execute-sequence", sequence, f"{value},77,88", "0,0,0")
                if observed.strip() != f"status=Success registers={expected} flags={flags}":
                    raise ValueError("sequence independent structured state oracle mismatch")
            failure_inputs = [("9,10", "0,0,0"), ("9,10,11", "0,0,2")]
        else:
            raise ValueError("unknown locked oracle fixture")
        for registers, flags in failure_inputs:
            saved_r = list(map(int, registers.split(",")))
            saved_f = list(map(int, flags.split(",")))
            observed = checked(fslc, "execute-sequence", sequence, registers, flags)
            if observed.strip() != f"status=InvalidState registers={saved_r} flags={saved_f}":
                raise ValueError("sequence failure changed state")
        reports.append({"name": name, "sequence_sha256": fixture["sequence_sha256"],
                        "outputs_identical": 3, "origin_envelope": "independently verified",
                        "native_cli_oracle_cases": len(inputs), "native_cli_failure_cases": len(failure_inputs)})
    return {"status": "passed", "scope": "explicit sequential instruction window; no binary function lifting or GPU CFG claim", "fixtures": reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, default=ROOT / "artifacts/sequence-fir.json")
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"status": "failed"}, indent=2)+"\n")
    golden = ROOT / "experiments/fir/sequence"
    lock = tomllib.loads((golden / "sequence.lock.toml").read_text())
    with tempfile.TemporaryDirectory(prefix="fir-sequence-") as directory:
        report = reproduce(args.fslc.resolve(), golden, pathlib.Path(directory), lock)
    args.report.write_text(json.dumps(report, indent=2)+"\n")
    print("FIR sequence: 2 origin envelopes and 6 outputs identical; 112 CLI oracle / 4 failure cases passed")


if __name__ == "__main__":
    main()
