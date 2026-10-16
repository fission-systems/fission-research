#!/usr/bin/env python3
"""Check the asset-independent ELF/FSL/FIR route; optional Linux chroot + file trace."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
from x86_semantics_validate import digest, run

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "experiments/x86/immediate"
GO = ROOT / "experiments/output/go-backend"
LEGACY = re.compile(
    r'\.(?:sla|slaspec|sinc|cspec|pspec|ldefs|opinion|fpk|fidb)(?:["/\s]|$)', re.I
)
FORBIDDEN_CRATES = {
    "fission-sleigh",
    "fission-pcode",
    "fission-decompiler",
    "iced-x86",
    "capstone",
    "zydis",
}


def check_graph(packages):
    refused = sorted(FORBIDDEN_CRATES.intersection(packages))
    if refused:
        raise ValueError("legacy/decoder dependency: " + ", ".join(refused))


def preflight():
    lock = json.loads((FIXTURES / "source.lock.json").read_text())
    for name, sha in lock["inputs"].items():
        if digest(FIXTURES / name) != sha:
            raise ValueError("fixture input hash mismatch: " + name)
    return lock


def validate(cli, cc, rustc, go, isolate):
    lock = preflight()
    go_lock = json.loads((GO / "source.lock.json").read_text())
    reports = []
    entry_reports = []
    with tempfile.TemporaryDirectory(prefix="fsl-owned-") as directory:
        work = Path(directory)
        runtime = work / "runtime"
        runtime.mkdir()
        for folder in ["bin", "inputs", "out", "empty"]:
            (runtime / folder).mkdir()
        shutil.copy2(cli, runtime / "bin/fsl-x86")
        env = dict(
            os.environ,
            FISSION_RESOURCE_ROOT=str(runtime / "empty"),
            FISSION_SLEIGH_SPEC_DIR=str(runtime / "empty"),
            FISSION_GHIDRA_DATA_DIR=str(runtime / "empty"),
            HOME=str(runtime / "empty"),
            PATH="",
        )
        if isolate:
            if os.uname().sysname != "Linux":
                raise ValueError("chroot file tracing requires Linux")
            libraries = run(["ldd", cli]).decode()
            for library in sorted(set(re.findall(r"(/[^\s()]+)", libraries))):
                path = Path(library)
                if not path.is_file():
                    raise ValueError("missing dynamic library: " + library)
                target = runtime / library.lstrip("/")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)

        def invoke(args, trace):
            if isolate:
                command = [
                    "sudo",
                    "-n",
                    "strace",
                    "-f",
                    "-e",
                    "trace=%file",
                    "-o",
                    str(trace),
                    "chroot",
                    "--userspec=" + str(os.getuid()) + ":" + str(os.getgid()),
                    str(runtime),
                    "/bin/fsl-x86",
                    *map(str, args),
                ]
                result = subprocess.run(command, capture_output=True)
                text = trace.read_text()
                if LEGACY.search(text):
                    raise ValueError("legacy asset path access in trace")
                return result
            return subprocess.run(
                [str(runtime / "bin/fsl-x86"), *map(str, args)],
                cwd=runtime,
                env=env,
                capture_output=True,
            )

        for fixture in lock["fixtures"]:
            name = fixture["name"]
            shutil.copy2(
                FIXTURES / "fixtures" / (name + ".elf"),
                runtime / "inputs" / (name + ".elf"),
            )
            for language, suffix in [("c", "c"), ("rust", "rs"), ("go", "go")]:
                label = name + "-" + language
                folder = runtime / "out" / label
                binary = (
                    "/inputs/" + name + ".elf"
                    if isolate
                    else str(runtime / "inputs" / (name + ".elf"))
                )
                target = "/out/" + label if isolate else str(folder)
                args = [
                    "decompile-owned",
                    binary,
                    "0x401000",
                    fixture["size"],
                    language,
                    target,
                ]
                trace = work / (label + ".trace")
                observed = invoke(args, trace)
                if observed.returncode:
                    raise ValueError(observed.stderr.decode())
                if digest(folder / "profile.fslxc") != lock["package_sha256"]:
                    raise ValueError("embedded profile mismatch")
                source = folder / ("output." + suffix)
                golden = (
                    GO / "outputs" / ("immediate-" + name + ".go")
                    if language == "go"
                    else FIXTURES / "outputs" / (name + "." + suffix)
                )
                expected_sha = (
                    go_lock["source_sha256"]["immediate-" + name + ".go"]
                    if language == "go"
                    else lock["output_sha256"]["outputs/" + name + "." + suffix]
                )
                if (
                    source.read_bytes() != golden.read_bytes()
                    or digest(source) != expected_sha
                ):
                    raise ValueError("locked source output changed")
                if (folder / "output.fir").read_bytes() != (
                    FIXTURES / "outputs" / (name + ".fir")
                ).read_bytes():
                    raise ValueError("canonical FIR output changed")
                report = (folder / "pipeline.txt").read_text()
                if (
                    "legacy-fallback=none" not in report
                    or "no legacy LoadSpec" not in report
                ):
                    raise ValueError("missing route evidence")
                output = work / (label + ".compiled")
                commands = {
                    "c": [
                        *cc,
                        "-std=c11",
                        "-Wall",
                        "-Wextra",
                        "-Werror",
                        "-c",
                        source,
                        "-o",
                        output,
                    ],
                    "rust": [
                        *rustc,
                        "--edition=2021",
                        "--crate-type=lib",
                        "-D",
                        "warnings",
                        source,
                        "-o",
                        output,
                    ],
                    "go": [*go, "build", "-o", output, source],
                }
                run(commands[language])
                before = {p.name: digest(p) for p in folder.iterdir()}
                refused = invoke(args, work / (label + "-refusal.trace"))
                if refused.returncode == 0 or before != {
                    p.name: digest(p) for p in folder.iterdir()
                }:
                    raise ValueError("existing directory overwritten")
                reports.append(
                    dict(
                        fixture=name,
                        backend=language,
                        source_sha256=digest(source),
                        compilation="passed",
                        existing_directory_refusal=True,
                        file_trace_sha256=digest(trace) if isolate else None,
                    )
                )
            # Address-only DecBench path must reach identical FIR/source without
            # consulting a function-size oracle or any legacy assets.
            label = name + "-entry"
            folder = runtime / "out" / label
            target = "/out/" + label if isolate else str(folder)
            trace = work / (label + ".trace")
            observed = invoke(
                ["decompile-owned-entry", binary, "0x401000", "c", target], trace
            )
            if observed.returncode:
                raise ValueError(observed.stderr.decode())
            for emitted, golden in [
                ("output.c", name + ".c"),
                ("output.fir", name + ".fir"),
            ]:
                if (folder / emitted).read_bytes() != (
                    FIXTURES / "outputs" / golden
                ).read_bytes():
                    raise ValueError("entry selection changed locked projection")
            if digest(folder / "profile.fslxc") != lock["package_sha256"]:
                raise ValueError("entry embedded profile mismatch")
            if (
                "source-function-boundary=unproven"
                not in (folder / "pipeline.txt").read_text()
            ):
                raise ValueError("entry boundary limitation missing")
            entry_reports.append(
                dict(
                    fixture=name,
                    source_sha256=digest(folder / "output.c"),
                    selection="entry-only straight-line to RET; no original ABI recovery",
                    file_trace_sha256=digest(trace) if isolate else None,
                )
            )
        # Unsupported opcode and backend must not create partial output bundles.
        bad = bytearray((runtime / "inputs/imm64.elf").read_bytes())
        bad[4096] = 0xCC
        (runtime / "inputs/bad.elf").write_bytes(bad)
        for name, language in [("bad", "c"), ("imm64", "python")]:
            label = "refused-" + name
            source = (
                "/inputs/" + name + ".elf"
                if isolate
                else str(runtime / "inputs" / (name + ".elf"))
            )
            output = "/out/" + label if isolate else str(runtime / "out" / label)
            refused = invoke(
                ["decompile-owned", source, "0x401000", 16, language, output],
                work / (label + ".trace"),
            )
            if refused.returncode == 0 or (runtime / "out" / label).exists():
                raise ValueError("unsupported input produced output")
        traces = {p.name: p.read_text() for p in sorted(work.glob("*.trace"))}
    return dict(
        status="passed",
        isolation=(
            "Linux chroot containing only executable, dynamic libraries and fixture inputs; strace file access"
            if isolate
            else "copied executable and inputs; empty cwd/resource roots/PATH; host filesystem remains accessible"
        ),
        bundles=reports,
        entry_bundles=entry_reports,
        refusals=11,
        legacy_file_accesses=[] if isolate else "not traced locally",
        traces=traces,
        scope="asset independence and byte-identical existing bounded projections; not new instruction coverage, function ABI recovery or execution-equivalence proof",
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fsl-x86", type=Path, required=True)
    p.add_argument("--compiler-root", type=Path, required=True)
    p.add_argument("--cargo", default="rustup run stable cargo")
    p.add_argument("--cc", default="clang")
    p.add_argument("--rustc", default="rustup run stable rustc")
    p.add_argument("--go", default="go")
    p.add_argument("--isolate", action="store_true")
    p.add_argument(
        "--report", type=Path, default=ROOT / "artifacts/owned-pipeline.json"
    )
    a = p.parse_args()
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text('{"status":"failed"}\n')
    preflight()
    graph = run(
        [
            *shlex.split(a.cargo),
            "tree",
            "--color",
            "never",
            "--manifest-path",
            a.compiler_root / "Cargo.toml",
            "--locked",
            "-p",
            "fission-fsl",
            "--features",
            "x86",
            "--prefix",
            "none",
            "--format",
            "{p}",
        ]
    ).decode()
    packages = sorted(
        set(line.split()[0] for line in graph.splitlines() if line.strip())
    )
    check_graph(packages)
    r = validate(
        a.fsl_x86.resolve(),
        shlex.split(a.cc),
        shlex.split(a.rustc),
        shlex.split(a.go),
        a.isolate,
    )
    r["dependency_packages"] = packages
    r["compiler_executable_sha256"] = digest(a.fsl_x86)
    r["validator_sha256"] = digest(Path(__file__))
    r["fixture_lock_sha256"] = digest(FIXTURES / "source.lock.json")
    r["compiler_commit"] = (
        run(["git", "-C", a.compiler_root, "rev-parse", "HEAD"]).decode().strip()
    )
    r["compiler_dirty"] = bool(
        run(["git", "-C", a.compiler_root, "status", "--porcelain"])
    )
    r["compiler_source_sha256"] = {
        n: digest(a.compiler_root / n)
        for n in [
            "crates/fission-fsl/src/pipeline.rs",
            "crates/fission-fsl/src/x86.rs",
            "crates/fission-loader/src/loader/elf/mod.rs",
            "crates/fission-loader/src/loader/pipeline.rs",
            "crates/fission-loader/src/loader/mod.rs",
        ]
    }
    a.report.write_text(json.dumps(r, indent=2) + "\n")
    print(
        "Owned pipeline: 9 unchanged source bundles compiled; 11 refusals; dependency closure checked; "
        + r["isolation"]
    )


if __name__ == "__main__":
    main()
