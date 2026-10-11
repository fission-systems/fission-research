#!/usr/bin/env python3
"""Validate locked stack/store FIR against emitted execution and original bytes."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import platform
import re
import shlex
import struct
import tempfile
from x86_semantics_validate import run, digest, cases, expected as add_expected

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "experiments/x86/stateful"
BP = 0x11223344
BASE = 0x1F80
SIZE = 160


def initial(bits, a, b):
    r = [0] * 17
    r[4] = 0x2000
    r[5] = BP
    m = bytearray(SIZE)
    m[128 : 128 + bits // 8] = (0xDEADBEEF).to_bytes(bits // 8, "little")
    if bits == 32:
        m[132:140] = struct.pack("<II", a, b)
    else:
        r[7] = 0x2010
        m[144:160] = struct.pack("<QQ", a, b)
    return dict(
        registers=r, flags=[0] * 6 + [1] * 6, memory_base=BASE, memory_hex=m.hex()
    )


def expected(name, bits, a, b, row, fail=False):
    if fail:
        return [3, *row["registers"], *row["flags"], 99], bytes.fromhex(
            row["memory_hex"]
        )
    result = add_expected(bits, a, b, row, "add")
    m = bytearray.fromhex(row["memory_hex"])
    if name == "frame32":
        m[124:128] = BP.to_bytes(4, "little")
    if name == "frame64":
        m[120:128] = BP.to_bytes(8, "little")
        m[112:120] = (0x2010).to_bytes(8, "little")
        result[2] = 0x2010  # RCX
    if name == "store64":
        m[144:152] = result[1].to_bytes(8, "little")
    return result, bytes(m)


def wrappers(work, name, bits):
    setup = (
        "r[7]=0x2010; memcpy(m+128,&ret,8); memcpy(m+144,&ab[0],8); memcpy(m+152,&ab[1],8);"
        if bits == 64
        else "memcpy(m+128,&ret,4); uint32_t a=(uint32_t)ab[0], b=(uint32_t)ab[1]; memcpy(m+132,&a,4); memcpy(m+136,&b,4);"
    )
    c = work / (name + "-wrapper.c")
    c.write_text(f"""#include <stdio.h>
#include <string.h>
#include "{work/(name+'.c')}"
int main(void){{uint64_t ab[3];while(fread(ab,sizeof ab,1,stdin)==1){{
uint64_t r[17]={{0}},f[12]={{0,0,0,0,0,0,1,1,1,1,1,1}},ret=0xdeadbeef,exit_pc=99;
uint8_t m[160]={{0}},scratch[160];r[4]=0x2000;r[5]=0x11223344;{setup}
uint64_t out[31];out[0]=fsl_x86(r,17,f,12,m,160,0x1f80,scratch,160,(size_t)ab[2],&exit_pc);
memcpy(out+1,r,sizeof r);memcpy(out+18,f,sizeof f);out[30]=exit_pc;
if(fwrite(out,sizeof out,1,stdout)!=1||fwrite(m,sizeof m,1,stdout)!=1)return 2;
}}return ferror(stdin)?3:0;}}
""")
    setup = (
        "r[7]=0x2010;m[128..136].copy_from_slice(&ret.to_le_bytes());m[144..152].copy_from_slice(&a.to_le_bytes());m[152..160].copy_from_slice(&b.to_le_bytes());"
        if bits == 64
        else "m[128..132].copy_from_slice(&(ret as u32).to_le_bytes());m[132..136].copy_from_slice(&(a as u32).to_le_bytes());m[136..140].copy_from_slice(&(b as u32).to_le_bytes());"
    )
    rs = work / (name + "-wrapper.rs")
    rs.write_text(f"""include!("{work/(name+'.rs')}");
use std::io::{{Read,Write}};
fn main(){{let mut data=Vec::new();std::io::stdin().read_to_end(&mut data).unwrap();assert_eq!(data.len()%24,0);let mut out=std::io::stdout().lock();
for row in data.chunks_exact(24){{let a=u64::from_le_bytes(row[..8].try_into().unwrap());let b=u64::from_le_bytes(row[8..16].try_into().unwrap());let budget=u64::from_le_bytes(row[16..].try_into().unwrap()) as usize;
let mut r=[0u64;17];let mut f=[0u64,0,0,0,0,0,1,1,1,1,1,1];let ret=0xdeadbeefu64;let mut m=[0u8;160];let mut scratch=[0u8;160];let mut exit_pc=99;r[4]=0x2000;r[5]=0x11223344;{setup}
let status=fsl_x86(&mut r,&mut f,&mut m,0x1f80,&mut scratch,budget,&mut exit_pc);
for v in std::iter::once(status as u64).chain(r).chain(f).chain(std::iter::once(exit_pc)){{out.write_all(&v.to_le_bytes()).unwrap();}}out.write_all(&m).unwrap();
}}}}
""")
    return c, rs


def original(bits, raw, cc, work, host):
    if host == "none" or (bits == 32 and host != "native-x86"):
        return None
    symbol = "_oracle_code" if host == "rosetta64" else "oracle_code"
    asm = work / f"original{bits}.S"
    asm.write_text(
        ".text\n.globl "
        + symbol
        + "\n"
        + symbol
        + ":\n.byte "
        + ",".join(f"0x{v:02x}" for v in raw)
        + "\n"
        + ('.section .note.GNU-stack,"",@progbits\n' if host == "native-x86" else "")
    )
    output = work / f"original{bits}"
    if bits == 32:
        run(
            [
                *cc,
                "-m32",
                "-nostdlib",
                "-static",
                "-Wl,-e,_start",
                GOLDEN / "oracle32.S",
                asm,
                "-o",
                output,
            ]
        )
    else:
        run(
            [
                *cc,
                *(["-arch", "x86_64"] if host == "rosetta64" else ["-m64"]),
                "-O2",
                "-fomit-frame-pointer",
                "-mno-red-zone",
                "-Wall",
                "-Wextra",
                "-Werror",
                GOLDEN / "oracle64.c",
                asm,
                "-o",
                output,
            ]
        )
    return ["arch", "-x86_64", str(output)] if host == "rosetta64" else [str(output)]


def validate(cli, baseline, cc, rustc, work, host):
    lock = json.loads((GOLDEN / "source.lock.json").read_text())
    for name, sha in lock["inputs"].items():
        if digest(GOLDEN / name) != sha:
            raise ValueError("input hash mismatch: " + name)
    package = work / "stateful.fslxc"
    run(
        [
            cli,
            "compile",
            GOLDEN / "specs/scalar.fslx",
            GOLDEN / "specs/scalar-bodies.fsl",
            package,
        ]
    )
    if digest(package) != lock["package_sha256"]:
        raise ValueError("package hash mismatch")
    reports = []
    for f in lock["fixtures"]:
        name, bits = f["name"], f["mode"]
        binary = GOLDEN / "fixtures" / (name + ".elf")
        raw = bytes.fromhex(f["hex"])
        ctx = [package, binary, "0x401000", f["size"]]
        if binary.read_bytes()[f["file_offset"] : f["file_offset"] + f["size"]] != raw:
            raise ValueError("original bytes mismatch")
        for layer, suffix in [
            ("fir", "fir"),
            ("c", "c"),
            ("rust", "rs"),
            ("evidence", "evidence.txt"),
        ]:
            path = work / (name + "." + suffix)
            run(
                [cli, "recover-binary", *ctx, path]
                if layer == "evidence"
                else [cli, "decompile-binary", *ctx, layer, path]
            )
            if (
                digest(path) != lock["output_sha256"]["outputs/" + path.name]
                or path.read_bytes() != (GOLDEN / "outputs" / path.name).read_bytes()
            ):
                raise ValueError("output/evidence mismatch")
        pairs = cases(bits)
        states = [initial(bits, a, b) for a, b in pairs]
        answers = [
            expected(name, bits, a, b, row) for (a, b), row in zip(pairs, states)
        ]
        for row, (state, memory) in zip(states, answers):
            observed = run(
                [
                    cli,
                    "execute-memory-binary",
                    *ctx,
                    ",".join(map(str, row["registers"])),
                    ",".join(map(str, row["flags"])),
                    BASE,
                    row["memory_hex"],
                    100,
                ]
            ).decode()
            match = re.fullmatch(
                r"status=Success exit=Some\((\d+)\) registers=(\[.*?\]) flags=(\[.*?\])\nmemory=([0-9a-f]+)\n",
                observed,
            )
            if (
                not match
                or [
                    0,
                    *ast.literal_eval(match[2]),
                    *ast.literal_eval(match[3]),
                    int(match[1]),
                ]
                != state
                or bytes.fromhex(match[4]) != memory
            ):
                raise ValueError("FIR state/memory mismatch")
        # Exhaust budget after an actual write: PUSH in frames, MOV store in store64.
        all_answers = answers + [
            expected(name, bits, a, b, row, True) for (a, b), row in zip(pairs, states)
        ]
        failure_budget = 3 if name == "store64" else 1
        payload = b"".join(
            struct.pack("<QQQ", a, b, budget)
            for budget in [100, failure_budget]
            for a, b in pairs
        )
        c, rs = wrappers(work, name, bits)
        for opt in [0, 2]:
            for lang, source, compiler in [("c", c, cc), ("rust", rs, rustc)]:
                exe = work / f"{name}-{lang}-{opt}"
                flags = (
                    ["-std=c11", "-Wall", "-Wextra", "-Werror", f"-O{opt}"]
                    if lang == "c"
                    else ["--edition=2021", "-D", "warnings", "-C", f"opt-level={opt}"]
                )
                run([*compiler, *flags, source, "-o", exe])
                data = run([exe], payload)
                if len(data) != len(all_answers) * 408:
                    raise ValueError("compiled output framing mismatch")
                for i, (state, memory) in enumerate(all_answers):
                    if (
                        list(struct.unpack("<31Q", data[i * 408 : i * 408 + 248]))
                        != state
                        or data[i * 408 + 248 : (i + 1) * 408] != memory
                    ):
                        raise ValueError("compiled state/memory or rollback mismatch")
        machine = original(bits, raw, cc, work, host)
        machine_cases = 0
        if machine:
            data = run(
                machine,
                b"".join(
                    struct.pack("<II" if bits == 32 else "<QQ", a, b) for a, b in pairs
                ),
            )
            width = 16 if bits == 32 else 48
            if len(data) != width * len(pairs):
                raise ValueError("machine output framing mismatch")
            for i, ((a, b), (state, memory)) in enumerate(zip(pairs, answers)):
                values = struct.unpack(
                    "<4I" if bits == 32 else "<6Q", data[i * width : (i + 1) * width]
                )
                value, rflags = values[:2]
                bp, balance = values[-2:]
                flags = [(rflags >> n) & 1 for n in [0, 2, 6, 7, 11, 4]]
                if (
                    value != state[1]
                    or flags != state[18:24]
                    or bp != BP
                    or balance != 0
                ):
                    raise ValueError("original result/flags/frame mismatch")
                if bits == 64 and values[2:4] != (
                    state[1] if name == "store64" else a,
                    b,
                ):
                    raise ValueError("original external memory effect mismatch")
                machine_cases += 1
        baseline_report = {"status": "not requested"}
        if baseline:
            data = run(
                [baseline, binary, "0x401000", f["size"]],
                ("\n".join(json.dumps(row) for row in states) + "\n").encode(),
            )
            rows = [json.loads(x) for x in data.decode().splitlines()]
            if len(rows) != len(pairs):
                raise ValueError("baseline framing mismatch")
            diff = {
                k: 0
                for k in [
                    "registers",
                    "exit",
                    "memory",
                    "CF",
                    "PF",
                    "ZF",
                    "SF",
                    "OF",
                    "AF",
                ]
            }
            for row, (state, memory) in zip(rows, answers):
                diff["registers"] += int(row["registers"] != state[1:18])
                diff["exit"] += int(row["exit"] != state[-1])
                diff["memory"] += int(bytes.fromhex(row["memory_hex"]) != memory)
                for key, a, b in zip(
                    ["CF", "PF", "ZF", "SF", "OF", "AF"], row["flags"], state[18:24]
                ):
                    diff[key] += int(a != b)
            baseline_report = dict(
                status="measured",
                cases=len(rows),
                differences_from_fir=diff,
                scope="actual SLA/canonical evaluator implementation; not IR superiority",
            )
        reports.append(
            dict(
                name=name,
                mode=bits,
                fir_states=len(pairs),
                c_rust_success_and_rollback_comparisons=len(all_answers) * 4,
                rollback_failure_budget=failure_budget,
                machine_execution=dict(
                    adapter=host if machine else "not available",
                    cases=machine_cases,
                    observables="result, six defined arithmetic flags, preserved RBP, balanced SP; external two-word memory in 64-bit adapters",
                    excluded="full register/stack memory hardware snapshots, faults, concurrency and arbitrary ABI",
                ),
                pcode_baseline=baseline_report,
            )
        )
    return dict(
        status="passed",
        fixtures=reports,
        scope="three compiled stack/store spans; no full x86, ABI recovery or whole-function equivalence proof",
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fsl-x86", type=Path, required=True)
    p.add_argument("--pcode-baseline", type=Path)
    p.add_argument("--baseline-root", type=Path)
    p.add_argument("--cc", default="clang")
    p.add_argument("--rustc", default="rustup run stable rustc")
    p.add_argument(
        "--machine-host",
        choices=["auto", "native-x86", "rosetta64", "none"],
        default="auto",
    )
    p.add_argument("--report", type=Path, default=ROOT / "artifacts/x86-stateful.json")
    a = p.parse_args()
    if a.pcode_baseline and not a.baseline_root:
        p.error("--pcode-baseline requires --baseline-root")
    host = a.machine_host
    if host == "auto":
        host = (
            "native-x86"
            if platform.system() == "Linux"
            and platform.machine() in ["x86_64", "AMD64"]
            else (
                "rosetta64"
                if platform.system() == "Darwin"
                and platform.machine() in ["arm64", "aarch64"]
                else "none"
            )
        )
    a.report.parent.mkdir(exist_ok=True, parents=True)
    a.report.write_text('{"status":"failed"}\n')
    with tempfile.TemporaryDirectory(prefix="x86-stateful-") as d:
        r = validate(
            a.fsl_x86.resolve(),
            a.pcode_baseline.resolve() if a.pcode_baseline else None,
            shlex.split(a.cc),
            shlex.split(a.rustc),
            Path(d),
            host,
        )
    r["validator_sha256"] = digest(Path(__file__))
    r["expected_native_compiler_commit"] = json.loads(
        (GOLDEN / "source.lock.json").read_text()
    )["native_compiler_commit"]
    r["compiler_executable_sha256"] = digest(a.fsl_x86)
    r["tools"] = dict(
        cc=run(shlex.split(a.cc) + ["--version"]).decode().splitlines()[0],
        rustc=run(shlex.split(a.rustc) + ["--version"]).decode().strip(),
        host_system=platform.system(),
        host_machine=platform.machine(),
    )
    if a.baseline_root:
        paths = [
            "crates/fission-emulator/examples/x86_fir_baseline.rs",
            "crates/fission-emulator/src/pcode/eval.rs",
            "utils/sleigh-specs/languages/x86/ia.sinc",
        ]
        paths += [
            x.relative_to(a.baseline_root).as_posix()
            for x in sorted(
                (a.baseline_root / "utils/sleigh-specs/compiled/x86").glob("*.sla")
            )
        ]
        r["baseline_provenance"] = dict(
            checkout_commit=run(["git", "-C", a.baseline_root, "rev-parse", "HEAD"])
            .decode()
            .strip(),
            source_sha256={p: digest(a.baseline_root / p) for p in paths},
            executable_sha256=(
                digest(a.pcode_baseline) if a.pcode_baseline else "not requested"
            ),
        )
        r["compiler_source_provenance"] = dict(
            checkout_commit=r["baseline_provenance"]["checkout_commit"],
            checkout_dirty=bool(
                run(["git", "-C", a.baseline_root, "status", "--porcelain"])
            ),
            source_sha256={
                x.relative_to(a.baseline_root).as_posix(): digest(x)
                for x in sorted(
                    (a.baseline_root / "crates/fission-fsl/src").glob("*.rs")
                )
            },
            scope="supplied checkout source snapshot and executable hash; no binary reproducible-build attestation",
        )
    a.report.write_text(json.dumps(r, indent=2) + "\n")
    print(
        "Stateful x86: 768 FIR states and 6144 C/Rust success/rollback comparisons passed; machine/P-code observations separate"
    )


if __name__ == "__main__":
    main()
