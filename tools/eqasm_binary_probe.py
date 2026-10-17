#!/usr/bin/env python3
"""Build a pinned reference assembler, compare its words with owned FSL formats.

Reference build only: no upstream dependency in Fission. Layout decoding does
not execute timing, pulses, target masks or configurable physical operations.
"""

import argparse
import json
from pathlib import Path
import random
import re
import subprocess
import sys
import shutil
import tempfile

import quantum_validate as common

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/quantum/eqasm-words"
REVISION = "9b024494558287a937cdd5a8ccd63fcaa784b1c4"
PROFILE = "qisa.qelab.9b024494.le"
WARNING = "\nError: the quantum layout information is not read into assembler\n"
SHIM = """
// Bison 3.8 no longer generates position equality used by this old frontend.
// Diagnostic source positions only; no encoding/gate logic is changed.
inline bool operator==(const position& a,const position& b) {
 return a.line==b.line && a.column==b.column && (a.filename==b.filename || (a.filename && b.filename && *a.filename==*b.filename));
}
"""


def build(source, output, bison, flex, cxx):
    revision = common.run(["git", "-C", source, "rev-parse", "HEAD"]).decode().strip()
    if (
        revision != REVISION
        or common.run(["git", "-C", source, "status", "--porcelain"]).strip()
    ):
        raise ValueError("reference checkout must be clean at the frozen revision")
    source = source.resolve() / "qisa-as"
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if b"3.8.2" not in common.run([bison, "--version"]):
        raise ValueError("reference build recipe requires Bison 3.8.2")
    common.run(
        [
            sys.executable,
            source / "scripts/gen_qisa_instructions.py",
            "-d",
            source / "qisa_opcodes.qmap",
            "-co",
            output / "qisa_opcode_defs.inc",
        ]
    )
    common.run([bison, "-o", output / "qisa_parser.tab.cc", source / "qisa_parser.yy"])
    location = output / "location.hh"
    text = location.read_text()
    if text.count("} // QISA") != 1:
        raise ValueError("unexpected generated location schema")
    location.write_text(text.replace("} // QISA", SHIM + "} // QISA"))
    common.run([flex, "-o", output / "qisa_lexer.yy.cc", source / "qisa_lexer.l"])
    command = [
        cxx,
        "-std=c++14",
        "-O2",
        "-Wno-deprecated-declarations",
        "-I",
        source,
        "-I",
        output,
        source / "main.cpp",
        source / "qisa_driver.cpp",
        source / "qisa_qmap_parser.cpp",
        output / "qisa_parser.tab.cc",
        output / "qisa_lexer.yy.cc",
        "-o",
        output / "qisa-as",
    ]
    # Compilation may take longer than a single oracle invocation.
    compiled = subprocess.run(list(map(str, command)), capture_output=True, timeout=180)
    if compiled.returncode:
        raise ValueError(
            "reference C++ build failed:\n" + compiled.stderr.decode(errors="replace")
        )
    shutil.copyfile(source / "qisa_opcodes.qmap", output / "pinned.qmap")
    return output / "qisa-as"


def corpus():
    rng = random.Random(176)
    rows = []
    for imm in [0, 1, (1 << 20) - 1] + [rng.randrange(1 << 20) for _ in range(125)]:
        rows.append((f"QWAIT {imm}", {"cycles": imm}, 0x60000000 | imm))
    for reg in range(32):
        rows.append((f"QWAITR R{reg}", {"source": reg}, 0x70000000 | (reg << 15)))
    for reg in range(32):
        bs = reg % 8
        slot0 = (1 << 6) | reg
        slot1 = (2 << 6) | (31 - reg)
        rows.append(
            (
                f"{bs} CW_01 S{reg} | CW_02 S{31-reg}",
                {"separator": bs, "slot0": slot0, "slot1": slot1},
                0x80000000 | (slot0 << 3) | (slot1 << 17) | bs,
            )
        )
    for bs in range(8):
        rows.append(
            (f"{bs} QNOP", {"separator": bs, "slot0": 0, "slot1": 0}, 0x80000000 | bs)
        )
    return rows


def validate(cli, oracle):
    lock = json.loads((FIXTURE / "source.lock.json").read_text())
    if common.digest(Path(__file__)) != lock["validator_sha256"]:
        raise ValueError("validator hash mismatch")
    for name, digest in lock["dependencies"].items():
        if common.digest(ROOT / "tools" / name) != digest:
            raise ValueError("oracle dependency hash mismatch")
    profile = FIXTURE / "qisa.fsl"
    if common.digest(profile) != lock["source_sha256"]:
        raise ValueError("FSL profile hash mismatch")
    with tempfile.TemporaryDirectory(prefix="eqasm-probe-") as directory:
        work = Path(directory)
        source = work / "corpus.qisa"
        binary = work / "corpus.bin"
        package = work / "qisa.fslc"
        rows = corpus()
        source.write_text("\n".join(row[0] for row in rows) + "\n")
        output = common.run(
            [oracle, "-q", oracle.parent / "pinned.qmap", "-o", binary, source]
        ).decode()
        if output != WARNING:
            raise ValueError("unrecognized assembler diagnostics")
        raw = binary.read_bytes()
        # The upstream writer stores host-order uint32_t words. Only little-
        # endian oracle hosts are admitted by this profile/experiment.
        expected = b"".join(word.to_bytes(4, "little") for _, _, word in rows)
        if raw != expected:
            raise ValueError("assembler bytes differ from pinned little-endian layout")
        disassembly = common.run(
            [oracle, "-q", oracle.parent / "pinned.qmap", "-d2", binary]
        ).decode()
        words = [
            int(word, 16) for word in re.findall(r"# 0x([0-9a-fA-F]{8})", disassembly)
        ]
        if words != [word for _, _, word in rows]:
            raise ValueError("upstream disassembly word sequence mismatch")
        common.run([cli, "compile", profile, package])
        if common.digest(package) != lock["package_sha256"]:
            raise ValueError("FSL package hash mismatch")
        for _, fields, word in rows:
            encoded = word.to_bytes(4, "little")
            decoded = common.run(
                [cli, "decode-bytes", package, PROFILE, encoded.hex()]
            ).decode()
            actual = {
                k: int(v) for k, v in re.findall(r"^  (\w+)=(\d+) ", decoded, re.M)
            }
            if actual != fields or "unsupported" not in decoded.lower():
                raise ValueError(
                    "owned field decode or unsupported-semantics contract mismatch"
                )
            out = work / "roundtrip.bin"
            common.run([cli, "reencode", package, PROFILE, encoded.hex(), out])
            if out.read_bytes() != encoded:
                raise ValueError("owned binary roundtrip mismatch")
        rejected = 0
        for encoded in [
            b"",
            b"\x00",
            b"\x00\x00\x00",
            (0).to_bytes(4, "little"),
            (0x60200000).to_bytes(4, "little"),
            (0x70000001).to_bytes(4, "little"),
        ]:
            result = subprocess.run(
                [str(cli), "decode-bytes", str(package), PROFILE, encoded.hex()],
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0:
                raise ValueError("unadmitted format accepted")
            rejected += 1
        for path, name in [(source, "corpus.qisa"), (binary, "corpus.bin")]:
            if common.digest(path) != lock[name + "_sha256"]:
                raise ValueError("reference corpus changed")
        return {
            "status": "passed",
            "words": len(rows),
            "field_comparisons": len(rows),
            "roundtrips": len(rows),
            "refusals": rejected,
            "source_sha256": common.digest(profile),
            "package_sha256": common.digest(package),
            "corpus_sha256": common.digest(binary),
            "oracle_commit": REVISION,
            "oracle_executable_sha256": common.digest(oracle),
            "compiler_executable_sha256": common.digest(cli),
            "upstream_warning": WARNING.strip(),
            "scope": "reference-assembled quantum-control words; strict QWAIT/QWAITR and opaque bundle layout; all execution semantics unsupported; no device capture, gate/pulse identity or QPU execution",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "Vendor/eqasm-assembler")
    parser.add_argument("--build", type=Path, default=ROOT / "artifacts/eqasm-build")
    parser.add_argument("--bison", default="bison")
    parser.add_argument("--flex", default="flex")
    parser.add_argument("--cxx", default="c++")
    parser.add_argument("--fslc", type=Path, required=True)
    parser.add_argument("--compiler-root", type=Path, required=True)
    parser.add_argument(
        "--report", type=Path, default=ROOT / "artifacts/eqasm-words.json"
    )
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('{"status":"failed"}\n')
    frozen_hashes = {
        p: common.digest(p)
        for p in [
            Path(__file__),
            Path(common.__file__),
            FIXTURE / "qisa.fsl",
            FIXTURE / "source.lock.json",
            FIXTURE / "corpus.bin",
            FIXTURE / "corpus.qisa",
        ]
    }
    oracle = build(args.source, args.build, args.bison, args.flex, args.cxx)
    before = (
        common.run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"])
        .decode()
        .strip()
    )
    dirty = bool(
        common.run(["git", "-C", args.compiler_root, "status", "--porcelain"]).strip()
    )
    with tempfile.TemporaryDirectory(prefix="eqasm-engine-") as directory:
        import shutil

        frozen = Path(directory) / "fslc"
        original_sha = common.digest(args.fslc)
        shutil.copy2(args.fslc, frozen)
        if common.digest(frozen) != original_sha:
            raise ValueError("compiler changed during snapshot")
        result = validate(frozen, oracle)
    after = (
        common.run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"])
        .decode()
        .strip()
    )
    if before != after:
        raise ValueError("compiler revision changed")
    result.update(
        compiler_commit=before,
        compiler_dirty=dirty
        or bool(
            common.run(
                ["git", "-C", args.compiler_root, "status", "--porcelain"]
            ).strip()
        ),
        validator_sha256=common.digest(Path(__file__)),
        bison_version=common.run([args.bison, "--version"]).decode().splitlines()[0],
        cxx_version=common.run([args.cxx, "--version"]).decode().splitlines()[0],
    )
    if any(common.digest(path) != digest for path, digest in frozen_hashes.items()):
        raise ValueError("probe inputs or oracle source changed during run")
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(
        f"eQASM: {result['words']} assembled words decoded and reencoded; semantics remain unsupported"
    )


if __name__ == "__main__":
    main()
