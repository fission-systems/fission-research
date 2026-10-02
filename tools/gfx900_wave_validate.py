#!/usr/bin/env python3
"""LLVM encoding comparison for the wave64 FSL slice, not hardware execution."""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import pathlib
import re
import subprocess
import tempfile
import tomllib

from gfx900_sop2_validate import run

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILE = "amdgcn.gfx900.vadd_u32.wave64"


def check_hashes(report, lock):
    for name in ["source_sha256", "package_sha256", "corpus_sha256"]:
        if report[name] != lock[name]:
            raise ValueError(f"wave {name} differs from reviewed snapshot")


def validate(fslc, llvm_mc, work):
    source = ROOT / "specs/gpu/amdgcn/gfx900-vadd-u32-wave64.fsl"
    package = work / "wave.fslc"
    run([fslc, "compile", source, package])
    second = work / "second.fslc"
    run([fslc, "compile", source, second])
    if package.read_bytes() != second.read_bytes():
        raise ValueError("nondeterministic wave packaging")
    cases = []
    for scalar in [False, True]:
        for src0, src1, dst in itertools.product([0, 1, 2, 95 if scalar else 255], [0, 1, 2, 255], [0, 1, 2, 255]):
            cases.append((scalar, src0, src1, dst))

    def assemble(edited=False):
        text = "\n".join(f"v_add_u32_e32 v{254 if edited else dst}, {'s' if scalar else 'v'}{src0}, v{src1}" for scalar, src0, src1, dst in cases) + "\n"
        listing = run([llvm_mc, "-triple=amdgcn-amd-amdhsa", "-mcpu=gfx900", "-show-encoding"], input=text)
        blobs = [bytes(int(v.strip(), 16) for v in record.split(",")) for record in re.findall(r"encoding: \[([^\]]+)\]", listing)]
        if len(blobs) != len(cases) or any(len(blob) != 4 for blob in blobs):
            raise ValueError("LLVM corpus incomplete or extended encoding")
        return blobs

    blobs, edits = assemble(), assemble(True)
    output = work / "reencoded.bin"
    for (scalar, src0, src1, dst), raw, edited in zip(cases, blobs, edits):
        decoded = run([fslc, "decode-bytes", package, PROFILE, raw.hex()])
        fields = {name: int(value) for name, value in re.findall(r"^  (\w+)=(\d+) ", decoded, re.M)}
        if fields != {"source0": src0 if scalar else src0+256, "source1": src1, "destination": dst}:
            raise ValueError("decoded fields disagree with LLVM operands")
        name = "vadd_sgpr" if scalar else "vadd_vgpr"
        if not re.search(rf"^instruction {name} encoding=", decoded, re.M) or "lane.mask.read" not in decoded:
            raise ValueError("incorrect semantic variant or missing mask effect")
        run([fslc, "reencode", package, PROFILE, raw.hex(), output])
        if output.read_bytes() != raw:
            raise ValueError("unchanged roundtrip differs")
        run([fslc, "reencode", package, PROFILE, raw.hex(), output, "destination=254"])
        if output.read_bytes() != edited:
            raise ValueError("edited bytes disagree with LLVM reassembly")
    rejected = 0
    for selector in [96, 127, 128, 249, 250, 255]:
        # Replace just SRC0 in independently assembled bytes.
        word = (int.from_bytes(blobs[0], "little") & ~511) | selector
        run([fslc, "decode-bytes", package, PROFILE, word.to_bytes(4,"little").hex()], accepted=False)
        rejected += 1
    for profile, raw in [("wrong.profile",blobs[0].hex()),(PROFILE,"0000"),(PROFILE,"00000000")]:
        run([fslc,"decode-bytes",package,profile,raw],accepted=False)
        rejected += 1
    report = {"status":"passed", "profile":PROFILE, "variants":2, "corpus_cases":len(cases),
            "decode_field_comparisons":len(cases), "unchanged_roundtrips":len(cases),
            "edited_oracle_comparisons":len(cases), "rejected_inputs":rejected,
            "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "package_sha256":hashlib.sha256(package.read_bytes()).hexdigest(),
            "corpus_sha256":hashlib.sha256(b"".join(blobs)).hexdigest(),
            "fslc_binary_sha256":hashlib.sha256(fslc.read_bytes()).hexdigest(),
            "llvm_mc_version":run([llvm_mc,"--version"]).splitlines()[0],
            "oracle_scope":"Encoding/operand fields only; LLVM is not a GPU execution oracle",
            "execution_scope":"Synthetic reference/C/Rust state comparisons are in native wave_state tests; GPU hardware unsupported"}
    lock = tomllib.loads((ROOT/"experiments/gpu/gfx900-wave64/source.lock.toml").read_text())
    check_hashes(report, lock)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", required=True, type=pathlib.Path)
    parser.add_argument("--llvm-mc", default="llvm-mc")
    parser.add_argument("--report", type=pathlib.Path, default=ROOT/"artifacts/gfx900-wave.json")
    args=parser.parse_args()
    report={"status":"failed"}
    try:
        with tempfile.TemporaryDirectory(prefix="fission-wave-") as directory:
            report=validate(args.fslc.resolve(),args.llvm_mc,pathlib.Path(directory))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report["error"]=str(exc)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":
    raise SystemExit(main())
