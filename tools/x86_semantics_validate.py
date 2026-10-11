#!/usr/bin/env python3
"""Compare three locked ELF spans: FIR, emitted C/Rust, and optional machine/P-code execution.

The machine adapter embeds exact locked instruction bytes. It supports only the
three declared leaf contracts; moving these spans does not change their semantics
because neither uses PC-relative addresses/control. No decoder dependency.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import platform
import re
import shlex
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "experiments/x86/memory"


def run(command, payload=None):
    result = subprocess.run([str(x) for x in command], input=payload, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"command failed: {command[0]}\n{result.stderr.decode(errors='replace')[-2000:]}")
    return result.stdout


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases(bits):
    m = (1 << bits) - 1
    boundaries = [0, 1, 15, 16, 255, m, m >> 1, 1 << (bits - 1)]
    rows = [(a, b) for a in boundaries for b in boundaries]
    seed = 0x48e93a710f20
    for _ in range(192):
        seed = (seed * 6364136223846793005 + 1) & ((1 << 64) - 1)
        a = seed & m
        seed = (seed * 6364136223846793005 + 1) & ((1 << 64) - 1)
        rows.append((a, seed & m))
    return rows


def state_for(bits, a, b):
    registers = [0] * 17
    registers[4] = 0x2000
    flags = [0] * 6 + [1] * 6
    memory = (0xdeadbeef).to_bytes(bits // 8, "little")
    if bits == 32:
        memory += struct.pack("<II", a, b)
    else:
        registers[7] = 0x2010
        memory += bytes(8) + struct.pack("<QQ", a, b)
    return {"registers": registers, "flags": flags, "memory_base": 0x2000, "memory_hex": memory.hex()}


def expected(bits, a, b, row, operation):
    mask = (1 << bits) - 1
    result = ((a + b) if operation=="add" else (a ^ b)) & mask
    r = row["registers"].copy()
    r[0] = result
    r[4] += bits // 8
    sign = 1 << (bits - 1)
    flags = [int(a + b > mask), int((result & 255).bit_count() % 2 == 0), int(result == 0),
             int(bool(result & sign)), int(bool((~(a ^ b) & (a ^ result)) & sign)),
             int(bool((a ^ b ^ result) & 16))] + [1] * 6
    if operation=="xor":
        flags[0]=flags[4]=flags[5]=0
        flags[11]=0  # AF is undefined; retained placeholder is not observable.
    return [0, *r, *flags, 0xdeadbeef]


def wrappers(generated, bits, work):
    setup_c = ('r[7]=0x2010; memcpy(m,&ret,8); memcpy(m+16,&ab[0],8); memcpy(m+24,&ab[1],8);'
               if bits == 64 else 'memcpy(m,&ret,4); uint32_t a=(uint32_t)ab[0], b=(uint32_t)ab[1]; memcpy(m+4,&a,4); memcpy(m+8,&b,4);')
    c = work / f"wrapper{bits}.c"
    c.write_text(f'''#include <stdio.h>
#include <string.h>
#include "{generated / ('program'+str(bits)+'.c')}"
int main(void) {{uint64_t ab[2]; while(fread(ab,sizeof ab,1,stdin)==1) {{
uint64_t r[17]={{0}}, f[12]={{0,0,0,0,0,0,1,1,1,1,1,1}}, ret=0xdeadbeef, exit_pc=99;
uint8_t m[32]={{0}};r[4]=0x2000;{setup_c}
uint64_t result[31];result[0]=fsl_x86(r,17,f,12,m,{32 if bits==64 else 12},0x2000,100,&exit_pc);
memcpy(result+1,r,sizeof r);memcpy(result+18,f,sizeof f);result[30]=exit_pc;
if(fwrite(result,sizeof result,1,stdout)!=1)return 2;
}}return ferror(stdin)?3:0;}}
''')
    setup_r = ('r[7]=0x2010;m[..8].copy_from_slice(&ret.to_le_bytes());m[16..24].copy_from_slice(&a.to_le_bytes());m[24..32].copy_from_slice(&b.to_le_bytes());'
               if bits == 64 else 'm[..4].copy_from_slice(&(ret as u32).to_le_bytes());m[4..8].copy_from_slice(&(a as u32).to_le_bytes());m[8..12].copy_from_slice(&(b as u32).to_le_bytes());')
    rs = work / f"wrapper{bits}.rs"
    rs.write_text(f'''include!("{generated / ('program'+str(bits)+'.rs')}");
use std::io::{{Read,Write}};
fn main(){{let mut data=Vec::new();std::io::stdin().read_to_end(&mut data).unwrap();assert_eq!(data.len()%16,0);
let mut stdout=std::io::stdout().lock();for row in data.chunks_exact(16){{
let a=u64::from_le_bytes(row[..8].try_into().unwrap());let b=u64::from_le_bytes(row[8..].try_into().unwrap());
let mut r=[0u64;17];let mut f=[0u64,0,0,0,0,0,1,1,1,1,1,1];let ret=0xdeadbeefu64;
let mut m=[0u8;32];let mut exit_pc=99;r[4]=0x2000;{setup_r}
let status=fsl_x86(&mut r,&mut f,&m[..{32 if bits==64 else 12}],0x2000,100,&mut exit_pc);
for value in std::iter::once(status as u64).chain(r).chain(f).chain(std::iter::once(exit_pc)){{stdout.write_all(&value.to_le_bytes()).unwrap();}}
}}}}
''')
    return c, rs


def machine_oracle(bits, raw, cc, work, host):
    if host == "none" or (bits == 32 and host != "native-x86"):
        return None
    symbol = "_oracle_code" if host == "rosetta64" else "oracle_code"
    assembly = work / f"code{bits}.S"
    assembly.write_text(f'.text\n.globl {symbol}\n{symbol}:\n.byte '+','.join(f'0x{x:02x}' for x in raw)+'\n'+
                        ('.section .note.GNU-stack,"",@progbits\n' if host == "native-x86" else ''))
    output = work / f"original{bits}"
    if bits == 32:
        run([*cc, "-m32", "-nostdlib", "-static", "-Wl,-e,_start",
             GOLDEN / "oracle32.S", assembly, "-o", output])
    else:
        run([*cc, *(["-arch", "x86_64"] if host == "rosetta64" else ["-m64"]),
             "-O2", "-mno-red-zone", "-Wall", "-Wextra", "-Werror", GOLDEN / "oracle64.c", assembly, "-o", output])
    return ["arch", "-x86_64", str(output)] if host == "rosetta64" else [str(output)]


def validate(cli, baseline, cc, rustc, work, host):
    lock = json.loads((GOLDEN / "source.lock.json").read_text())
    for name, expected_hash in lock["inputs"].items():
        if digest(GOLDEN / name) != expected_hash:
            raise ValueError(f"input hash mismatch: {name}")
    package = work / "memory.fslxc"
    run([cli, "compile", GOLDEN / "specs/scalar.fslx", GOLDEN / "specs/scalar-bodies.fsl", package])
    if digest(package) != lock["package_sha256"]:
        raise ValueError("memory package hash mismatch")
    reports = []
    for fixture in lock["fixtures"]:
        bits, name = fixture["mode"], fixture["name"]
        binary = GOLDEN / "fixtures" / f"{name}.elf"
        raw = bytes.fromhex(fixture["hex"])
        if binary.read_bytes()[fixture["file_offset"]:fixture["file_offset"] + len(raw)] != raw:
            raise ValueError("machine oracle bytes differ from original ELF")
        context = [package, binary, "0x401000", len(raw)]
        for layer, suffix in [("fir", "fir"), ("c", "c"), ("rust", "rs")]:
            output = work / f"program{bits}.{suffix}"
            run([cli, "decompile-binary", *context, layer, output])
            if output.read_bytes() != (GOLDEN / "outputs" / f"{name}.{suffix}").read_bytes() or digest(output) != lock["output_sha256"][f"outputs/{name}.{suffix}"]:
                raise ValueError("locked projection mismatch")
        evidence = work / f"{name}.evidence.txt"
        run([cli, "recover-binary", *context, evidence])
        if evidence.read_bytes() != (GOLDEN / "outputs" / evidence.name).read_bytes() or digest(evidence) != lock["output_sha256"][f"outputs/{evidence.name}"]:
            raise ValueError("input evidence mismatch")
        pairs = cases(bits)
        states = [state_for(bits, a, b) for a, b in pairs]
        expect = [expected(bits, a, b, row, fixture["operation"]) for (a,b),row in zip(pairs,states)]
        for row, result in zip(states, expect):
            text = run([cli, "execute-binary", *context, ','.join(map(str,row["registers"])),
                        ','.join(map(str,row["flags"])), row["memory_base"], row["memory_hex"], 100]).decode()
            match = re.fullmatch(r"status=Success exit=Some\((\d+)\) registers=(\[.*?\]) flags=(\[.*?\])\n", text)
            if not match or [0, *ast.literal_eval(match[2]), *ast.literal_eval(match[3]), int(match[1])] != result:
                raise ValueError("FIR result differs from independent arithmetic/state oracle")
        payload = b''.join(struct.pack('<QQ',a,b) for a,b in pairs)
        c, rs = wrappers(work, bits, work)
        for optimization in (0, 2):
            for language, source, compiler in [('c',c,cc),('rust',rs,rustc)]:
                executable = work / f"{name}-{language}-O{optimization}"
                options = ["-std=c11", "-Wall", "-Wextra", "-Werror", f"-O{optimization}"] if language == 'c' else ["--edition=2021", "-D", "warnings", "-C", f"opt-level={optimization}"]
                run([*compiler, *options, source, '-o', executable])
                observed = run([executable], payload)
                if len(observed) != len(expect)*248:
                    raise ValueError("recompiled output framing mismatch")
                actual = [list(struct.unpack('<31Q',observed[i:i+248])) for i in range(0,len(observed),248)]
                if actual != expect:
                    raise ValueError(f"recompiled {language}/O{optimization} state mismatch")
        original = machine_oracle(bits, raw, cc, work, host)
        original_rows = []
        if original:
            machine_payload = b''.join(struct.pack('<II' if bits==32 else '<QQ',a,b) for a,b in pairs)
            observed = run(original, machine_payload)
            width = 8 if bits==32 else 16
            if len(observed) != width*len(pairs):
                raise ValueError("original-machine output framing mismatch")
            for i, result in enumerate(expect):
                value, rflags = struct.unpack('<II' if bits==32 else '<QQ',observed[i*width:(i+1)*width])
                flags = [(rflags >> bit) & 1 for bit in [0,2,6,7,11,4]]
                if value != result[1] or any(flags[j] != result[18+j] for j in range(6) if result[24+j]):
                    raise ValueError("original machine result/defined arithmetic flags differ from FIR")
                original_rows.append((value,flags))
        baseline_report = {"status":"not requested"}
        if baseline:
            data = ('\n'.join(json.dumps(row) for row in states)+'\n').encode()
            observed = run([baseline, binary, "0x401000", len(raw)], data)
            rows = [json.loads(line) for line in observed.decode().splitlines()]
            if len(rows) != len(expect):
                raise ValueError("baseline framing mismatch")
            differences = {key:0 for key in ["registers","exit","CF","PF","ZF","SF","OF","AF"]}
            examples = []
            for index,(row, result) in enumerate(zip(rows, expect)):
                differences["registers"] += int(row["registers"] != result[1:18])
                differences["exit"] += int(row["exit"] != result[30])
                for flag, old, new in zip(["CF","PF","ZF","SF","OF","AF"],row["flags"],result[18:24]):
                    differences[flag] += int(old != new) if result[24+["CF","PF","ZF","SF","OF","AF"].index(flag)] else 0
                if any(row["flags"][j] != result[18+j] for j in range(6) if result[24+j]) and len(examples)<4:
                    examples.append({"inputs":pairs[index], "legacy_flags":row["flags"], "fir_flags":result[18:24],
                                     "original_machine_flags":original_rows[index][1] if original else "not run"})
            baseline_report = {"status":"measured", "cases":len(rows), "differences_from_fir":differences,
                               "examples":examples,"undefined_AF_samples_excluded":len(rows) if fixture["operation"]=="xor" else 0,"baseline":"actual Fission SLA and canonical P-code evaluator; implementation differences, not P-code expressive limits"}
        reports.append({"name":name,"mode":bits,"input_sha256":hashlib.sha256(raw).hexdigest(),
                        "fir_states":len(expect),"c_rust_O0_O2_comparisons":len(expect)*4,
                        "machine_execution":{"adapter":host if original else "not available", "result_and_defined_flags_cases":len(original_rows),
                                             "compared_flags":["CF","PF","ZF","SF","OF","AF"] if fixture["operation"]=="add" else ["CF","PF","ZF","SF","OF"],
                                             "excluded":"all-register hardware snapshots, guest memory/fault/concurrency, arbitrary relocation, arbitrary ABI"},
                        "pcode_baseline":baseline_report})
    return {"status":"passed","fixtures":reports,"scope":"three compiled leaf ELF spans; no global decompiler quality or full x86/ABI equivalence claim"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fsl-x86',type=Path,required=True)
    p.add_argument('--pcode-baseline',type=Path)
    p.add_argument('--baseline-root',type=Path,help='source checkout for baseline provenance')
    p.add_argument('--cc',default='clang')
    p.add_argument('--rustc',default='rustup run stable rustc')
    p.add_argument('--machine-host',choices=['auto','native-x86','rosetta64','none'],default='auto')
    p.add_argument('--report',type=Path,default=ROOT/'artifacts/x86-semantics.json')
    args=p.parse_args()
    if args.pcode_baseline and not args.baseline_root:
        p.error("--pcode-baseline requires --baseline-root to record source provenance")
    host=args.machine_host
    if host=='auto':
        host='native-x86' if platform.system()=='Linux' and platform.machine() in ['x86_64','AMD64'] else ('rosetta64' if platform.system()=='Darwin' and platform.machine() in ['arm64','aarch64'] else 'none')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps({'status':'failed'},indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='x86-semantic-') as directory:
        report=validate(args.fsl_x86.resolve(),args.pcode_baseline.resolve() if args.pcode_baseline else None,
                        shlex.split(args.cc),shlex.split(args.rustc),Path(directory),host)
    report["validator_sha256"]=digest(Path(__file__))
    report["compiler_executable_sha256"]=digest(args.fsl_x86)
    report["tools"]={"cc":run(shlex.split(args.cc)+["--version"]).decode().splitlines()[0],
                     "rustc":run(shlex.split(args.rustc)+["--version"]).decode().strip(),
                     "host_system":platform.system(),"host_machine":platform.machine()}
    if args.baseline_root:
        paths=["crates/fission-emulator/examples/x86_fir_baseline.rs", "crates/fission-emulator/src/pcode/eval.rs", "utils/sleigh-specs/languages/x86/ia.sinc"]
        paths += [p.relative_to(args.baseline_root).as_posix() for p in sorted((args.baseline_root/"utils/sleigh-specs/compiled/x86").glob("*.sla"))]
        report["baseline_provenance"]={"checkout_commit":run(["git","-C",args.baseline_root,"rev-parse","HEAD"]).decode().strip(),
                                      "source_sha256":{p:digest(args.baseline_root/p) for p in paths},
                                      "executable_sha256":digest(args.pcode_baseline) if args.pcode_baseline else "not requested"}
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print('Three ELF windows: 768 FIR states and 3072 C/Rust comparisons passed; machine and P-code results recorded separately')


if __name__=='__main__':
    main()
