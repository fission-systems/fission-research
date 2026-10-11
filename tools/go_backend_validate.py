#!/usr/bin/env python3
"""Compile and execute Go projections against independent bounded expectations."""

import argparse
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess
import tempfile
from x86_semantics_validate import cases, digest, run
from x86_stateful_validate import initial, expected, wrappers

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "experiments/output/go-backend"
INPUTS = GOLDEN / "inputs"
PARENTS = [ROOT / "experiments/x86/stateful", ROOT / "experiments/x86/immediate"]


def preflight(lock):
    for name, sha in lock["inputs"].items():
        if digest(INPUTS / name) != sha:
            raise ValueError("Go input hash mismatch: " + name)
    for parent in PARENTS:
        if digest(parent / "source.lock.json") != lock["parent_locks"][parent.name]:
            raise ValueError("parent fixture lock mismatch: " + parent.name)
        p = json.loads((parent / "source.lock.json").read_text())
        for name, sha in p["inputs"].items():
            if digest(parent / name) != sha:
                raise ValueError("parent fixture input mismatch: " + name)


def test_program(go, source, harness, vectors, work, label):
    h = work / (label + "_test.go")
    h.write_text(harness)
    data = work / (label + ".json")
    data.write_text(json.dumps(vectors))
    for opt, flags in [("default", []), ("disabled", ["-gcflags=all=-N -l"])]:
        exe = work / (label + "-" + opt)
        run([*go, "test", "-c", *flags, "-o", exe, source, h])
        run([exe, "-input", data])
    return len(vectors) * 2


COMMON = """package fsl
import ("encoding/json"; "flag"; "os"; "reflect"; "testing")
var input = flag.String("input","","vector file")
type Row struct {
 R, F, Fields, Stack, Lane []uint64
 WantR, WantF, WantStack, WantLane []uint64
 Depth, WantDepth int
 Exec uint64
 Status uint32
}
func TestCases(t *testing.T) {
 data,err:=os.ReadFile(*input); if err!=nil {t.Fatal(err)}
 var rows []Row; if err=json.Unmarshal(data,&rows);err!=nil {t.Fatal(err)}
 for i,row:=range rows {
"""


def domain_vectors(kind, bits=32):
    rows = []
    if kind == "carry":
        for a, b in cases(bits):
            for carry in [0, 1]:
                for dst in [0, 1, 2]:
                    r = [a, b, 0x123456789ABCDEF0]
                    wide = (a & ((1 << bits) - 1)) + (b & ((1 << bits) - 1)) + carry
                    want = list(r)
                    want[dst] = wide & ((1 << bits) - 1)
                    rows.append(
                        dict(
                            R=r,
                            F=[carry, 1],
                            Fields=[0, 1, dst],
                            WantR=want,
                            WantF=[int(wide >> bits != 0), 1],
                            Status=0,
                        )
                    )
        for fields, flags in [
            ([0, 1, 3], [0, 1]),
            ([0, 1, 2], [2, 1]),
            ([16, 1, 2], [0, 1]),
            ([0, 1], [0, 1]),
        ]:
            rows.append(
                dict(
                    R=[1, 2, 9],
                    F=flags,
                    Fields=fields,
                    WantR=[1, 2, 9],
                    WantF=flags,
                    Status=3,
                )
            )
    elif kind in ["stack", "branch"]:
        for a, b in cases(32):
            s = [0x123456789, a, b, 0xFFEEDDCCBBAA0099]
            want = list(s)
            if kind == "stack":
                depth, final = 3, 2
                want[1] = (a + b) & 0xFFFFFFFF
            else:
                depth = final = 3
                value = b & 0xFFFFFFFF
                want[2] = (value + (1 if value < 10 else 2)) & 0xFFFFFFFF
            rows.append(
                dict(Stack=s, Depth=depth, WantStack=want, WantDepth=final, Status=0)
            )
        for depth, status in [(-1, 3), (5, 3), (0, 1)]:
            rows.append(
                dict(
                    Stack=[11, 12, 13, 14],
                    Depth=depth,
                    WantStack=[11, 12, 13, 14],
                    WantDepth=depth,
                    Status=status,
                )
            )
    elif kind == "register":
        for a in range(256):
            for dst in [0, 1]:
                r = [a, 0xFEDCBA9876543210, 0]
                signed = a if a < 128 else a - 256
                want = list(r)
                want[2] = a
                want[dst] = signed & 0xFFFFFFFF
                rows.append(
                    dict(
                        R=r,
                        F=[0, 0, 0],
                        Fields=[0, dst, 2],
                        WantR=want,
                        WantF=[int(signed < 0), 1, int(signed < 0)],
                        Status=0,
                    )
                )
        rows.append(
            dict(
                R=[7, 8, 9],
                F=[0, 0, 0],
                Fields=[0, 1, 3],
                WantR=[7, 8, 9],
                WantF=[0, 0, 0],
                Status=3,
            )
        )
    elif kind in ["wave-vgpr", "wave-sgpr"]:
        for seed in range(16):
            for exec_mask in [0, 1, 1 << 63, 0xAAAAAAAAAAAAAAAA, 0xFFFFFFFFFFFFFFFF]:
                for dst in [0, 1, 2]:
                    r, f = [0xFFFFFFFF + seed, 4], [0, 1]
                    lane = [
                        ((seed + j) * 0x123456789ABCDEF + (j % 3)) & ((1 << 64) - 1)
                        for j in range(192)
                    ]
                    want = list(lane)
                    for j in range(64):
                        if exec_mask & (1 << j):
                            left = lane[j] if kind == "wave-vgpr" else r[0]
                            want[dst * 64 + j] = (left + lane[64 + j]) & 0xFFFFFFFF
                    fields = [256 if kind == "wave-vgpr" else 0, 1, dst]
                    rows.append(
                        dict(
                            R=r,
                            F=f,
                            Lane=lane,
                            Fields=fields,
                            Exec=exec_mask,
                            WantR=r,
                            WantF=f,
                            WantLane=want,
                            Status=0,
                        )
                    )
        row = dict(rows[-1])
        row.update(Fields=[row["Fields"][0], 1, 3], WantLane=row["Lane"], Status=3)
        rows.append(row)
    return rows


def validate(cli, fslc, go, cc, rustc, record):
    lock_path = GOLDEN / "source.lock.json"
    lock = json.loads(lock_path.read_text())
    preflight(lock)
    generated, rows, cross = {}, [], 0
    with tempfile.TemporaryDirectory(prefix="fsl-go-") as directory:
        work = Path(directory)
        # Existing actual ELF store/frame fixtures; their source goldens remain immutable.
        for parent in PARENTS:
            parent_lock = json.loads((parent / "source.lock.json").read_text())
            package = work / (parent.name + ".fslxc")
            run(
                [
                    cli,
                    "compile",
                    parent / "specs/scalar.fslx",
                    parent / "specs/scalar-bodies.fsl",
                    package,
                ]
            )
            if digest(package) != parent_lock["package_sha256"]:
                raise ValueError("parent package mismatch")
            for fixture in parent_lock["fixtures"]:
                name, bits = fixture["name"], fixture["mode"]
                label = parent.name + "-" + name
                folder = work / label
                ctx = [
                    package,
                    parent / "fixtures" / (name + ".elf"),
                    "0x401000",
                    fixture["size"],
                ]
                run([cli, "bundle-binary", *ctx, "go", folder])
                source = folder / "output.go"
                generated[label + ".go"] = source.read_bytes()
                for arch in ["amd64", "386"]:
                    env = dict(
                        os.environ,
                        GOARCH=arch,
                        GOOS="linux",
                        CGO_ENABLED="0",
                        GOTOOLCHAIN="local",
                    )
                    subprocess.run(
                        [
                            *go,
                            "build",
                            "-o",
                            str(work / (label + arch + ".a")),
                            str(source),
                        ],
                        env=env,
                        check=True,
                        capture_output=True,
                    )
                    cross += 1
                pairs = cases(bits)
                failure_budget = (
                    3 if name == "store64" or fixture.get("literal_store") else 1
                )
                answers = [
                    expected(
                        name,
                        bits,
                        a,
                        b,
                        initial(bits, a, b),
                        fail,
                        fixture.get("literal_store"),
                    )
                    for fail in [False, True]
                    for a, b in pairs
                ]
                payload = b"".join(
                    struct.pack("<QQQ", a, b, budget)
                    for budget in [100, failure_budget]
                    for a, b in pairs
                )
                input_path = work / (label + ".bin")
                input_path.write_bytes(payload)
                harness = folder / "replay_test.go"
                setup = (
                    "r[7]=0x2010;binary.LittleEndian.PutUint64(m[128:],0xdeadbeef);binary.LittleEndian.PutUint64(m[144:],a);binary.LittleEndian.PutUint64(m[152:],b)"
                    if bits == 64
                    else "binary.LittleEndian.PutUint32(m[128:],0xdeadbeef);binary.LittleEndian.PutUint32(m[132:],uint32(a));binary.LittleEndian.PutUint32(m[136:],uint32(b))"
                )
                harness.write_text(
                    """package fsl
import ("encoding/binary";"flag";"os";"testing")
var input=flag.String("input","","input");var output=flag.String("output","","output")
func TestReplay(t *testing.T){data,err:=os.ReadFile(*input);if err!=nil{t.Fatal(err)};if len(data)%24!=0{t.Fatal("framing")};out:=[]byte{}
for i:=0;i<len(data);i+=24{a:=binary.LittleEndian.Uint64(data[i:]);b:=binary.LittleEndian.Uint64(data[i+8:]);budget:=int(binary.LittleEndian.Uint64(data[i+16:]));r:=make([]uint64,17);f:=[]uint64{0,0,0,0,0,0,1,1,1,1,1,1};m:=make([]byte,160);exit:=uint64(99);r[4]=0x2000;r[5]=0x11223344;"""
                    + setup
                    + """
status:=fsl_x86(r,f,m,0x1f80,budget,&exit);values:=append([]uint64{uint64(status)},r...);values=append(values,f...);values=append(values,exit);for _,v:=range values{var word [8]byte;binary.LittleEndian.PutUint64(word[:],v);out=append(out,word[:]...)};out=append(out,m...)}
if err=os.WriteFile(*output,out,0600);err!=nil{t.Fatal(err)}}
"""
                )
                expected_bytes = b"".join(
                    struct.pack("<31Q", *state) + memory for state, memory in answers
                )
                for opt, flags in [
                    ("default", []),
                    ("disabled", ["-gcflags=all=-N -l"]),
                ]:
                    exe = work / (label + opt)
                    run([*go, "test", "-c", *flags, "-o", exe, source, harness])
                    output = work / (label + opt + ".bin")
                    run([exe, "-input", input_path, "-output", output])
                    if output.read_bytes() != expected_bytes:
                        raise ValueError("Go state/memory/rollback mismatch: " + label)
                # C and Rust locked source bytes, compiled and executed over identical payload.
                for lang, suffix in [("c", "c"), ("rust", "rs")]:
                    path = work / (name + "." + suffix)
                    run([cli, "decompile-binary", *ctx, lang, path])
                    if (
                        path.read_bytes()
                        != (parent / "outputs" / path.name).read_bytes()
                        or digest(path)
                        != parent_lock["output_sha256"]["outputs/" + path.name]
                    ):
                        raise ValueError("C/Rust locked source changed")
                c, rs = wrappers(work, name, bits)
                for opt in [0, 2]:
                    for language, src, compiler in [("c", c, cc), ("rust", rs, rustc)]:
                        exe = work / (label + language + str(opt))
                        flags = (
                            ["-std=c11", "-Wall", "-Wextra", "-Werror", f"-O{opt}"]
                            if language == "c"
                            else [
                                "--edition=2021",
                                "-D",
                                "warnings",
                                "-C",
                                f"opt-level={opt}",
                            ]
                        )
                        run([*compiler, *flags, src, "-o", exe])
                        if run([exe], payload) != expected_bytes:
                            raise ValueError("C/Rust execution mismatch")
                rows.append(
                    dict(
                        fixture=label,
                        go_comparisons=len(answers) * 2,
                        c_rust_comparisons=len(answers) * 4,
                        source_sha256=digest(source),
                    )
                )
        domain_count = 0
        profiles = [
            ("jvm-se26-iadd.fsl", "iadd", "stack", 32),
            ("stack-branch-join.fsl", "choose", "branch", 32),
            ("register-branch-convert.fsl", "choose", "register", 32),
        ]
        profiles += [
            ("carry-widths.fsl", "carry" + str(b), "carry", b)
            for b in [1, 8, 16, 32, 64]
        ]
        profiles += [
            ("amdgcn-gfx900-vadd-u32-wave64.fsl", n, k, 32)
            for n, k in [("vadd_vgpr", "wave-vgpr"), ("vadd_sgpr", "wave-sgpr")]
        ]
        for filename, instruction, kind, bits in profiles:
            package = work / (filename + ".fslc")
            run([fslc, "compile", INPUTS / filename, package])
            label = kind + str(bits)
            source = work / (label + ".go")
            run([fslc, "emit-backend", package, instruction, "go", source])
            generated[label + ".go"] = source.read_bytes()
            vectors = domain_vectors(kind, bits)
            if kind in ["stack", "branch"]:
                call = 'status:=fsl_execute(row.Stack,&row.Depth); if status!=row.Status || row.Depth!=row.WantDepth || !reflect.DeepEqual(row.Stack,row.WantStack){t.Fatalf("stack case %d",i)}'
            elif kind.startswith("wave"):
                call = 'status:=fsl_execute(row.R,row.F,row.Lane,64,row.Exec,row.Fields); if status!=row.Status || !reflect.DeepEqual(row.R,row.WantR) || !reflect.DeepEqual(row.F,row.WantF) || !reflect.DeepEqual(row.Lane,row.WantLane){t.Fatalf("wave case %d",i)}'
            else:
                call = 'status:=fsl_execute(row.R,row.F,row.Fields); if status!=row.Status || !reflect.DeepEqual(row.R,row.WantR) || !reflect.DeepEqual(row.F,row.WantF){t.Fatalf("register case %d",i)}'
            harness = COMMON + call + "\n} }\n"
            domain_count += test_program(go, source, harness, vectors, work, label)
        hashes = {
            name: __import__("hashlib").sha256(raw).hexdigest()
            for name, raw in generated.items()
        }
        if record:
            (GOLDEN / "outputs").mkdir(exist_ok=True)
            for name, raw in generated.items():
                (GOLDEN / "outputs" / name).write_bytes(raw)
            lock["source_sha256"] = hashes
            lock_path.write_text(json.dumps(lock, indent=2) + "\n")
        elif hashes != lock["source_sha256"] or any(
            (GOLDEN / "outputs" / n).read_bytes() != raw for n, raw in generated.items()
        ):
            raise ValueError("Go source golden mismatch")
    return dict(
        status="passed",
        x86=rows,
        domain_comparisons=domain_count,
        host_cross_compilations=cross,
        source_artifacts=len(generated),
        scope="bounded Go/C/Rust state and memory comparisons; synthetic domains; no original machine execution in this gate or full-function equivalence",
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fsl-x86", type=Path, required=True)
    p.add_argument("--fslc", type=Path, required=True)
    p.add_argument("--go", default="go")
    p.add_argument("--cc", default="clang")
    p.add_argument("--rustc", default="rustup run stable rustc")
    p.add_argument("--record", action="store_true")
    p.add_argument("--report", type=Path, default=ROOT / "artifacts/go-backend.json")
    a = p.parse_args()
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text('{"status":"failed"}\n')
    result = validate(
        a.fsl_x86.resolve(),
        a.fslc.resolve(),
        shlex.split(a.go),
        shlex.split(a.cc),
        shlex.split(a.rustc),
        a.record,
    )
    result["tools"] = {
        "go": run([*shlex.split(a.go), "version"]).decode().strip(),
        "cc": run([*shlex.split(a.cc), "--version"]).decode().splitlines()[0],
        "rustc": run([*shlex.split(a.rustc), "--version"]).decode().strip(),
    }
    result["validator_sha256"] = digest(Path(__file__))
    result["shared_models_sha256"] = {
        n: digest(ROOT / "tools" / n)
        for n in ["x86_semantics_validate.py", "x86_stateful_validate.py"]
    }
    result["source_lock_sha256"] = digest(GOLDEN / "source.lock.json")
    result["compiler_executable_sha256"] = {
        "fslc": digest(a.fslc),
        "fsl-x86": digest(a.fsl_x86),
    }
    compiler_root = a.fsl_x86.resolve().parents[2]
    if (compiler_root / "Cargo.toml").is_file():
        result["compiler_source_provenance"] = dict(
            checkout_commit=run(["git", "-C", compiler_root, "rev-parse", "HEAD"])
            .decode()
            .strip(),
            checkout_dirty=bool(
                run(["git", "-C", compiler_root, "status", "--porcelain"])
            ),
            source_sha256={
                p.relative_to(compiler_root).as_posix(): digest(p)
                for p in sorted((compiler_root / "crates/fission-fsl/src").glob("*.rs"))
            },
        )
    a.report.write_text(json.dumps(result, indent=2) + "\n")
    print(
        "Go:",
        sum(r["go_comparisons"] for r in result["x86"]),
        "x86 comparisons;",
        result["domain_comparisons"],
        "domain comparisons;",
        result["host_cross_compilations"],
        "host cross compilations",
    )


if __name__ == "__main__":
    main()
