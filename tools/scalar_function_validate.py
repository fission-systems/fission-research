#!/usr/bin/env python3
"""Owned catalog -> ELF -> FIR -> checked C function -> differential execution.

Requires clang/ld.lld/LLVM binutils and native x86-64 or macOS Rosetta.
Uses authored freestanding C functions, not a DecBench score or proof.
"""

import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import random
import re
import shlex
import struct
import subprocess
import tempfile

SOURCES = {
    "arithmetic": "return (a+b)^c;",
    "choice": "if (a==0) return b+7; return (a^b)+c;",
    "masked": "return ((a&b)|c)+17;",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args, data=None, env=None):
    p = subprocess.run(list(map(str, args)), input=data, capture_output=True, env=env)
    if p.returncode:
        raise RuntimeError(
            f"{args[0]} failed ({p.returncode}): {p.stderr.decode(errors='replace')}"
        )
    return p.stdout


def harness(symbol, count):
    args = ",".join(f"v[{i}]" for i in range(count))
    params = ",".join(["uint64_t"] * count) or "void"
    return f"""#include <stdint.h>
#include <stdio.h>
extern uint64_t {symbol}({params});
int main(void){{uint64_t v[3];while(fread(v,sizeof v,1,stdin)==1){{
uint64_t r={symbol}({args});if(fwrite(&r,sizeof r,1,stdout)!=1)return 2;
}}return ferror(stdin)?3:0;}}
"""


def validate(a, work):
    cli = Path(a.cli).resolve()
    cc, host_cc = shlex.split(a.cc), shlex.split(a.host_cc)
    host = platform.machine().lower()
    rosetta = platform.system() == "Darwin" and host in ("arm64", "aarch64")
    if not rosetta and host not in ("x86_64", "amd64"):
        raise ValueError("original byte execution requires x86-64 or macOS Rosetta")
    empty = work / "empty"
    empty.mkdir()
    # No legacy resource directory is passed to the CLI. This is not a file trace.
    env = dict(
        os.environ,
        FISSION_RESOURCE_ROOT=str(empty),
        FISSION_SLEIGH_SPEC_DIR=str(empty),
        FISSION_GHIDRA_DATA_DIR=str(empty),
        HOME=str(empty),
        PATH="",
    )
    specs = Path(a.fission).resolve() / "crates/fission-fsl/specs/x86"
    traces = []

    def invoke_cli(arguments, label):
        command = [cli, *arguments]
        if a.trace:
            trace = work / (label + ".trace")
            command = [a.trace, "-f", "-e", "trace=%file", "-o", trace, *command]
        observed = run(command, env=env)
        if a.trace:
            captured = trace.read_text()
            if re.search(
                r'\.(?:sla|slaspec|sinc|cspec|pspec|ldefs|opinion|fpk|fidb)(?:["/\s]|$)',
                captured,
                re.I,
            ):
                raise ValueError("legacy asset access attempted in file trace")
            traces.append({"name": trace.name, "sha256": sha(trace)})
        return observed

    catalog = work / "elf.fslpc"
    invoke_cli(
        ["compile-profiles", specs / "elf.fslprofiles", catalog], "compile-profiles"
    )
    boundary = [0, 1, 7, 1 << 31, (1 << 32) - 1, 1 << 32, 1 << 63, (1 << 64) - 1]
    rows = list(itertools.product(boundary, repeat=3))
    rng = random.Random(0xF1510)
    rows += [tuple(rng.getrandbits(64) for _ in range(3)) for _ in range(1536)]
    data = b"".join(struct.pack("<QQQ", *row) for row in rows)
    (work / "inputs.bin").write_bytes(data)
    reports = []
    for name, body in SOURCES.items():
        for opt in [1, 2]:
            directory = work / f"{name}-O{opt}"
            directory.mkdir()
            source = directory / "original.c"
            source.write_text(
                "#include <stdint.h>\n__attribute__((noinline)) uint64_t candidate(uint64_t a,uint64_t b,uint64_t c){"
                + body
                + "}\n"
            )
            obj, elf = directory / "original.o", directory / "original.elf"
            # Force cmov conversion to branches to stay within the existing FSL
            # subset. This compiler constraint is part of the measured scope.
            flags = [
                "--target=x86_64-unknown-linux-gnu",
                "-ffreestanding",
                f"-O{opt}",
                "-mllvm",
                "-x86-cmov-converter-force-all",
                "-fno-stack-protector",
                "-fno-asynchronous-unwind-tables",
            ]
            run([*cc, *flags, "-c", source, "-o", obj])
            relocations = run([a.readelf, "-r", obj]).decode()
            if "There are no relocations" not in relocations:
                raise ValueError("byte oracle requires relocation-free function")
            run([a.linker, "-e", "candidate", "-Ttext=0x401000", obj, "-o", elf])
            nm = run([a.nm, "--print-size", elf]).decode()
            match = re.search(
                r"^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+T\s+candidate$", nm, re.M
            )
            if not match:
                raise ValueError("missing candidate symbol size")
            address, size = (int(x, 16) for x in match.groups())
            if address != 0x401000:
                raise ValueError("unexpected function placement")
            text = directory / "text.bin"
            run([a.objcopy, "--dump-section", f".text={text}", elf])
            raw = text.read_bytes()[:size]
            (directory / "disassembly.txt").write_bytes(run([a.objdump, "-d", elf]))
            bundle = directory / "decompiled"
            invoke_cli(
                [
                    "decompile-function",
                    catalog,
                    elf,
                    hex(address),
                    size,
                    "sysv-amd64-u64-leaf-v1",
                    "recovered_candidate",
                    bundle,
                ],
                f"{name}-O{opt}",
            )
            evidence = (bundle / "projection.txt").read_text()
            count = int(re.search(r"parameter-prefix=(\d+)", evidence).group(1))
            if count > 3:
                raise ValueError("unexpected extra input dependency")
            # Original ELF bytes executed unmodified at a host-callable address;
            # relative in-function branches retain their exact displacement.
            assembly = directory / "original-bytes.S"
            symbol = "_original_bytes" if rosetta else "original_bytes"
            assembly.write_text(
                f".text\n.globl {symbol}\n{symbol}:\n.byte "
                + ",".join(hex(b) for b in raw)
                + ("\n" if rosetta else '\n.section .note.GNU-stack,"",@progbits\n')
            )
            wrapper = directory / "oracle.c"
            wrapper.write_text(harness("original_bytes", 3))
            original_exe = directory / "original-exec"
            run(
                [
                    *host_cc,
                    *(["-arch", "x86_64"] if rosetta else []),
                    "-O2",
                    wrapper,
                    assembly,
                    "-o",
                    original_exe,
                ]
            )
            original = run(
                ["arch", "-x86_64", original_exe] if rosetta else [original_exe], data
            )
            (directory / "original-results.bin").write_bytes(original)
            if len(original) != 8 * len(rows):
                raise ValueError("truncated byte oracle results")
            wrapper.write_text(harness("candidate", 3))
            reference_exe = directory / "source-exec"
            run([*host_cc, "-O2", wrapper, source, "-o", reference_exe])
            if run([reference_exe], data) != original:
                raise ValueError("source reference differs from original machine bytes")
            wrapper.write_text(harness("recovered_candidate", count))
            executions = []
            for generated_opt in [0, 2]:
                output = directory / f"recompiled-O{generated_opt}"
                run(
                    [
                        *host_cc,
                        f"-O{generated_opt}",
                        "-std=c11",
                        "-Wall",
                        "-Wextra",
                        "-Werror",
                        "-fsanitize=undefined",
                        "-fno-sanitize-recover=undefined",
                        wrapper,
                        bundle / "output.c",
                        "-o",
                        output,
                    ]
                )
                observed = run([output], data)
                (directory / f"recompiled-O{generated_opt}-results.bin").write_bytes(
                    observed
                )
                if observed != original:
                    raise ValueError(
                        f"execution mismatch: {name}/O{opt}/generated-O{generated_opt}"
                    )
                executions.append(
                    {
                        "optimization": generated_opt,
                        "cases": len(rows),
                        "result_sha256": hashlib.sha256(observed).hexdigest(),
                    }
                )
            reports.append(
                {
                    "name": name,
                    "original_optimization": opt,
                    "compiler_flags": flags,
                    "source_sha256": sha(source),
                    "elf_sha256": sha(elf),
                    "raw_hex": raw.hex(),
                    "size": size,
                    "parameter_prefix": count,
                    "cfg_edges": len(re.findall(r"^cfg-edge ", evidence, re.M)),
                    "return_paths": int(
                        re.search(r"return-paths=(\d+)", evidence).group(1)
                    ),
                    "c_sha256": sha(bundle / "output.c"),
                    "fir_sha256": sha(bundle / "output.fir"),
                    "executions": executions,
                }
            )
    return {
        "contract": 1,
        "status": "passed",
        "host": platform.platform(),
        "original_execution": "exact relocation-free ELF function bytes via Rosetta x86-64"
        if rosetta
        else "exact relocation-free ELF function bytes on native x86-64",
        "source_reference_execution": "host-native compiled C",
        "native_commit": run(["git", "-C", a.fission, "rev-parse", "HEAD"])
        .decode()
        .strip(),
        "native_dirty": bool(run(["git", "-C", a.fission, "status", "--porcelain"])),
        "cli_sha256": sha(cli),
        "catalog_sha256": sha(catalog),
        "input_sha256": sha(work / "inputs.bin"),
        "resource_file_traces": traces,
        "attempted_legacy_asset_accesses": 0 if a.trace else None,
        "generated_c_ubsan": "fatal",
        "clang": run([*cc, "--version"]).decode().splitlines()[0],
        "host_cc": run([*host_cc, "--version"]).decode().splitlines()[0],
        "functions": reports,
        "recompiled_comparisons": sum(
            e["cases"] for r in reports for e in r["executions"]
        ),
        "source_reference_comparisons": len(rows) * len(reports),
        "limits": [
            "authored C corpus; not DecBench",
            "compiler constrained to existing FSL subset",
            "explicit ABI and symbol-size boundaries",
            "no original source prototype recovery",
            "no loops, calls, data memory, faults or full ABI",
            "empty resource environment; file tracing only when --trace is supplied; no formal equivalence proof",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fission", required=True)
    p.add_argument("--cli", required=True)
    p.add_argument("--cc", default="clang")
    p.add_argument("--host-cc", default="cc")
    for key, default in [
        ("linker", "ld.lld"),
        ("nm", "llvm-nm"),
        ("objcopy", "llvm-objcopy"),
        ("objdump", "llvm-objdump"),
        ("readelf", "llvm-readelf"),
    ]:
        p.add_argument("--" + key, default=default)
    p.add_argument(
        "--trace", help="absolute strace executable for Linux CLI file-access audits"
    )
    p.add_argument("--output", required=True, type=Path)
    p.add_argument(
        "--keep",
        type=Path,
        help="new directory for reproducible source, ELF and projection artifacts",
    )
    a = p.parse_args()
    if a.keep:
        a.keep = a.keep.resolve()
        a.keep.mkdir(parents=True)
        report = validate(a, a.keep)
    else:
        with tempfile.TemporaryDirectory(prefix="fsl-functions-") as directory:
            report = validate(a, Path(directory))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"passed: {len(report['functions'])} functions, {report['recompiled_comparisons']} recompilation comparisons"
    )


if __name__ == "__main__":
    main()
