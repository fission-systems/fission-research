#!/usr/bin/env python3
"""Static-only DecBench external eval-kit coverage for the owned FSL/FIR engine.

The current backend emits explicit machine-state code, not original-ABI C.
Successful projections are diagnostic artifacts and are NEVER submissions.
Only functions.json.public selects targets; no private mapping/answer key is used.
"""

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
MAX_LOG = 16384


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def targets(kit):
    """Validate the complete public selection before creating output/running tools."""
    manifest = kit / "functions.json"
    data = json.loads(manifest.read_text())
    if data.get("kit_format_version") != 1:
        raise ValueError("expected eval-kit format version 1")
    public = data.get("public")
    if not isinstance(public, dict) or not public:
        raise ValueError("public selection must be a nonempty object")
    binary_root = (kit / "binaries").resolve(strict=True)
    selected = []
    for binary, addresses in sorted(public.items()):
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", binary):
            raise ValueError("unsafe binary basename")
        path = binary_root / binary
        if path.is_symlink() or path.resolve(strict=True).parent != binary_root:
            raise ValueError("binary must be a direct nonsymlink file in binaries")
        if not path.is_file():
            raise ValueError("binary is not a file")
        if not isinstance(addresses, list) or not addresses:
            raise ValueError("addresses must be a nonempty list")
        parsed = []
        for address in addresses:
            if not isinstance(address, str) or not re.fullmatch(
                r"0x[0-9a-fA-F]{1,16}", address
            ):
                raise ValueError("expected hexadecimal u64 virtual address")
            parsed.append(int(address, 16))
        if len(set(parsed)) != len(parsed):
            raise ValueError("duplicate public virtual address")
        sha = digest(path)
        for address in sorted(parsed):
            selected.append((binary, path, address, sha))
    # The private block is deliberately neither interpreted nor copied.
    return {
        "kit_format_version": 1,
        "manifest_sha256": digest(manifest),
        "public_selection_sha256": json_digest(public),
        "selection_source": "functions.json.public only; encoded-header virtual addresses",
        "target_count": len(selected),
        "binary_count": len(public),
    }, selected


def refusal_category(message):
    """Diagnostic grouping only; preserve raw tool messages as primary evidence."""
    if "loader:" in message or "not little-endian x86" in message:
        return "loader_or_architecture"
    if "branch refused" in message:
        return "entry_cfg_unsupported"
    if "found no near RET" in message:
        return "entry_bound_exhausted"
    if "entry decode" in message:
        return "owned_decode_unsupported"
    if "not executable" in message or "not file-backed" in message:
        return "entry_mapping"
    if "relocated instruction window" in message:
        return "instruction_relocation"
    return "other_admission_or_tool_error"


def attempt(cli, path, address, bundle, cwd, timeout):
    # The only executable in this command is the trusted FSL tool. No target
    # execution, chmod, emulator, compilation, metric tool or package.py call.
    command = [
        str(cli),
        "decompile-owned-entry",
        str(path),
        hex(address),
        "c",
        str(bundle),
    ]
    env = dict(
        os.environ,
        FISSION_RESOURCE_ROOT=str(cwd),
        FISSION_SLEIGH_SPEC_DIR=str(cwd),
        FISSION_GHIDRA_DATA_DIR=str(cwd),
    )
    start = time.monotonic()
    try:
        result = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as failure:
        return {
            "status": "timeout",
            "category": "tool_timeout",
            "seconds": round(time.monotonic() - start, 6),
            "stderr": (failure.stderr or b"")[-MAX_LOG:].decode(errors="replace"),
        }
    except OSError as failure:
        return {
            "status": "tool_error",
            "category": "tool_invocation_error",
            "seconds": round(time.monotonic() - start, 6),
            "stderr": str(failure),
        }
    elapsed = round(time.monotonic() - start, 6)
    stderr = result.stderr[-MAX_LOG:].decode(errors="replace")
    common = {
        "seconds": elapsed,
        "returncode": result.returncode,
        "stderr": stderr,
        "stdout": result.stdout[-MAX_LOG:].decode(errors="replace"),
        "logs_truncated": max(len(result.stdout), len(result.stderr)) > MAX_LOG,
    }
    if result.returncode:
        return dict(
            common,
            status="refused" if result.returncode == 1 else "tool_error",
            category=(
                refusal_category(stderr)
                if result.returncode == 1
                else "tool_process_failure"
            ),
        )
    expected = {
        "output.c",
        "output.fir",
        "profile.fslxc",
        "pipeline.txt",
        "projection.txt",
        "build.txt",
    }
    if not bundle.is_dir() or {p.name for p in bundle.iterdir()} != expected:
        return dict(common, status="tool_error", category="incomplete_bundle")
    if any(p.is_symlink() or not p.is_file() for p in bundle.iterdir()):
        return dict(common, status="tool_error", category="unexpected_bundle_file")
    report = (bundle / "pipeline.txt").read_text()
    if not all(
        marker in report
        for marker in [
            "semantic-owner=canonical-fir",
            "legacy-fallback=none",
            "backend=c",
            "selection=conservative-straight-line-entry",
            "source-function-boundary=unproven",
            "no general function discovery, source prototype or ABI recovery",
        ]
    ):
        return dict(
            common, status="tool_error", category="unexpected_pipeline_contract"
        )
    return dict(
        common,
        status="state_projection_only",
        category="original_abi_unrecovered",
        artifacts={p.name: digest(p) for p in sorted(bundle.iterdir())},
        pipeline_report=report,
    )


def summarize(rows):
    return {
        "attempted": len(rows),
        "status_counts": dict(sorted(Counter(r["status"] for r in rows).items())),
        "category_counts": dict(sorted(Counter(r["category"] for r in rows).items())),
        "ordinary_c_functions_eligible": 0,
        "submission_ready": False,
        "metrics": "not run; explicit-state code is ineligible for original-ABI function metrics",
    }


def evaluate(kit, cli, output, timeout=10):
    kit, cli, output = (
        kit.resolve(strict=True),
        cli.resolve(strict=True),
        output.resolve(),
    )
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if not cli.is_file() or not os.access(cli, os.X_OK) or cli.is_relative_to(kit):
        raise ValueError("FSL tool must be an executable outside the eval kit")
    if output.is_relative_to(kit):
        raise ValueError("output must be outside the immutable eval kit")
    source, selected = targets(kit)
    binary_root = (kit / "binaries").resolve(strict=True)
    if cli.is_relative_to(binary_root) or output.is_relative_to(binary_root):
        raise ValueError(
            "tool/output must be outside the resolved target binary directory"
        )
    report = {
        "report_contract": 1,
        "engine": {"id": "fission-fsl", "executable_sha256": digest(cli)},
        "adapter_sha256": digest(Path(__file__)),
        "selection": source,
        "policy": {
            "analysis": "static only; target binaries never executed or emulated",
            "answer_keys": "not used; no private mapping, source, DWARF or reference decompiler",
            "candidate": "owned embedded FSL -> canonical FIR -> explicit-state C",
            "entry_selection": "straight-line to near RET, at most 65536 bytes / 4096 instructions; branches refuse",
            "source_function_abi": "unsupported; never rename a state wrapper to the target function",
            "submission": "no results/results.json or archive until ordinary source-function ABI is supported",
            "equivalence": "not measured; Alive2 deferred",
        },
        "complete": False,
        "functions": [],
    }
    output.mkdir()  # Existing directories refuse; never overwrite an earlier run.
    (output / "diagnostics").mkdir()
    (output / "empty-resources").mkdir()
    report_path = output / "report.json"
    write_json(report_path, report)
    for binary, path, address, sha in selected:
        parent = output / "diagnostics" / binary
        parent.mkdir(exist_ok=True)
        bundle = parent / f"{address:x}"
        result = attempt(
            cli, path, address, bundle, output / "empty-resources", timeout
        )
        result.update(
            binary=binary,
            address=hex(address),
            binary_sha256=sha,
            metric_eligible=False,
        )
        if bundle.exists():
            result["diagnostic_bundle"] = str(bundle.relative_to(output))
        report["functions"].append(result)
        report["summary"] = summarize(report["functions"])
        write_json(report_path, report)
    report["integrity"] = {
        "manifest_unchanged": digest(kit / "functions.json")
        == source["manifest_sha256"],
        "tool_unchanged": digest(cli) == report["engine"]["executable_sha256"],
        "binaries_unchanged": all(
            digest(path) == sha
            for path, sha in {row[1]: row[3] for row in selected}.items()
        ),
    }
    report["complete"] = all(report["integrity"].values())
    report["summary"] = summarize(report["functions"])
    write_json(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit-root", type=Path, required=True)
    parser.add_argument("--fsl-x86", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, required=True, help="new directory outside kit"
    )
    parser.add_argument(
        "--timeout", type=float, default=10, help="per-function tool timeout in seconds"
    )
    args = parser.parse_args()
    report = evaluate(args.kit_root, args.fsl_x86, args.output, args.timeout)
    print(json.dumps(report["summary"], indent=2))
    # An honest completed coverage run is successful even with no admitted
    # functions. Read submission_ready; exit zero never means a benchmark score.
    if not report["complete"] or any(
        r["status"] == "tool_error" for r in report["functions"]
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
