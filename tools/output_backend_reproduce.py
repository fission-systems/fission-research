#!/usr/bin/env python3
"""Reproduce source-backend plans/bundles; compilation is a separate observed gate."""

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
from x86_semantics_validate import run, digest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "experiments/x86/immediate"
GOLDEN = ROOT / "experiments/output/backend-contract"


def reproduce(cli, cc, rustc, record=False):
    source_lock = FIXTURES / "source.lock.json"
    parent = json.loads(source_lock.read_text())
    # Parent inputs are immutable validation prerequisites, never regenerated here.
    for name, sha in parent["inputs"].items():
        if digest(FIXTURES / name) != sha:
            raise ValueError("fixture input hash mismatch: " + name)
    lock_path = GOLDEN / "source.lock.json"
    lock = None if record else json.loads(lock_path.read_text())
    if lock and lock["fixture_lock_sha256"] != digest(source_lock):
        raise ValueError("fixture lock hash mismatch")
    metadata = {}
    with tempfile.TemporaryDirectory(prefix="fsl-backend-") as directory:
        work = Path(directory)
        package = work / "immediate.fslxc"
        run(
            [
                cli,
                "compile",
                FIXTURES / "specs/scalar.fslx",
                FIXTURES / "specs/scalar-bodies.fsl",
                package,
            ]
        )
        if digest(package) != parent["package_sha256"]:
            raise ValueError("package hash mismatch")
        reports = []
        for fixture in parent["fixtures"]:
            name = fixture["name"]
            binary = FIXTURES / "fixtures" / (name + ".elf")
            ctx = [package, binary, "0x401000", fixture["size"]]
            for language, suffix, compiler in [("c", "c", cc), ("rust", "rs", rustc)]:
                folder = work / (name + "-" + language)
                planned = run([cli, "plan-binary", *ctx, language])
                run([cli, "bundle-binary", *ctx, language, folder])
                source = folder / ("output." + suffix)
                if (
                    source.read_bytes()
                    != (FIXTURES / "outputs" / (name + "." + suffix)).read_bytes()
                ):
                    raise ValueError("backend changed locked source output")
                expected = parent["output_sha256"]["outputs/" + name + "." + suffix]
                if digest(source) != expected:
                    raise ValueError("backend source hash mismatch")
                if (
                    b"compilation=not-performed equivalence=not-performed"
                    not in planned
                ):
                    raise ValueError("plan incorrectly claims validation")
                if (
                    b"TransactionalByteMemory" not in planned
                    or b"GuestPc" not in planned
                ):
                    raise ValueError("missing runtime requirements")
                for artifact, data in [
                    (name + "-" + language + ".plan.txt", planned),
                    (
                        name + "-" + language + ".projection.txt",
                        (folder / "projection.txt").read_bytes(),
                    ),
                    (
                        name + "-" + language + ".build.txt",
                        (folder / "build.txt").read_bytes(),
                    ),
                ]:
                    metadata[artifact] = hashlib.sha256(data).hexdigest()
                    golden = GOLDEN / "outputs" / artifact
                    if record:
                        golden.parent.mkdir(parents=True, exist_ok=True)
                        golden.write_bytes(data)
                    elif (
                        golden.read_bytes() != data
                        or lock["metadata_sha256"][artifact] != metadata[artifact]
                    ):
                        raise ValueError("backend metadata mismatch: " + artifact)
                output = work / (
                    name + "-" + language + (".o" if language == "c" else ".rlib")
                )
                flags = (
                    ["-std=c11", "-Wall", "-Wextra", "-Werror", "-c"]
                    if language == "c"
                    else ["--edition=2021", "--crate-type=lib", "-D", "warnings"]
                )
                run([*compiler, *flags, source, "-o", output])
                # Existing output folder must refuse without modifying any artifact.
                before = {p.name: digest(p) for p in folder.iterdir()}
                refused = subprocess.run(
                    [str(x) for x in [cli, "bundle-binary", *ctx, language, folder]],
                    capture_output=True,
                )
                if refused.returncode == 0 or before != {
                    p.name: digest(p) for p in folder.iterdir()
                }:
                    raise ValueError("existing bundle was overwritten")
                reports.append(
                    dict(
                        fixture=name,
                        backend=language,
                        source_sha256=digest(source),
                        compilation="passed",
                        execution_equivalence="not measured by this gate",
                    )
                )
        unregistered = work / "unsupported-go"
        refused = subprocess.run(
            [str(x) for x in [cli, "bundle-binary", *ctx, "go", unregistered]],
            capture_output=True,
        )
        if refused.returncode == 0 or unregistered.exists():
            raise ValueError("unregistered backend produced an artifact")
        if record:
            GOLDEN.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(
                json.dumps(
                    dict(
                        format="fsl-backend-contract-v1",
                        fixture_lock_sha256=digest(source_lock),
                        native_compiler_commit="pending",
                        metadata_sha256=metadata,
                    ),
                    indent=2,
                )
                + "\n"
            )
    return dict(
        status="passed",
        bundles=reports,
        metadata_artifacts=len(metadata),
        existing_directory_refusals=6,
        unregistered_backend_refusals=1,
        scope="same C/Rust source bytes; backend admission metadata and compilation, not new instruction coverage or execution-equivalence proof",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fsl-x86", type=Path, required=True)
    parser.add_argument("--cc", default="clang")
    parser.add_argument("--rustc", default="rustup run stable rustc")
    parser.add_argument(
        "--record",
        action="store_true",
        help="record only new backend metadata; parent source goldens remain required",
    )
    parser.add_argument(
        "--report", type=Path, default=ROOT / "artifacts/output-backend.json"
    )
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('{"status":"failed"}\n')
    result = reproduce(
        args.fsl_x86.resolve(),
        shlex.split(args.cc),
        shlex.split(args.rustc),
        args.record,
    )
    result["validator_sha256"] = digest(Path(__file__))
    result["source_lock_sha256"] = digest(GOLDEN / "source.lock.json")
    result["compiler_executable_sha256"] = digest(args.fsl_x86)
    result["tools"] = {
        "cc": run(shlex.split(args.cc) + ["--version"]).decode().splitlines()[0],
        "rustc": run(shlex.split(args.rustc) + ["--version"]).decode().strip(),
    }
    compiler_root = args.fsl_x86.resolve().parents[2]
    if (compiler_root / "Cargo.toml").is_file():
        result["compiler_source_provenance"] = {
            "checkout_commit": run(["git", "-C", compiler_root, "rev-parse", "HEAD"])
            .decode()
            .strip(),
            "checkout_dirty": bool(
                run(["git", "-C", compiler_root, "status", "--porcelain"])
            ),
            "source_sha256": {
                p.relative_to(compiler_root).as_posix(): digest(p)
                for p in sorted((compiler_root / "crates/fission-fsl/src").glob("*.rs"))
            },
            "scope": "supplied checkout and executable snapshot, not reproducible-build attestation",
        }
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(
        "Source backends: 6 bundles/18 metadata artifacts reproduced, 6 source compilations passed; 7 refusal checks passed"
    )


if __name__ == "__main__":
    main()
