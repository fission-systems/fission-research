#!/usr/bin/env python3
"""Rebuild locked layouts, then optionally link/execute with native FSL."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile


def checked(command, expected_code=0, expected_text=None):
    result = subprocess.run([str(arg) for arg in command], capture_output=True, text=True)
    if result.returncode != expected_code or (expected_text is not None and expected_text not in result.stdout + result.stderr):
        raise ValueError(f"command failed expected gate {command}: {result.returncode} {result.stdout} {result.stderr}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fission-root", type=pathlib.Path, default=pathlib.Path("Fission"))
    parser.add_argument("--fslc", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("artifacts/register-layout.json"))
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    golden = root / "experiments/migration/register-layout"
    first = root / "experiments/migration/first-slice"
    report = {"format": "fission-register-layout-reproduction-v1", "status": "failed", "artifact_hashes": {},
              "native_checks": [], "scope": "source metadata and linked leaf reference execution; no ABI allocator/calls, GPU layout, direct SLA semantics or hardware execution"}
    try:
        with tempfile.TemporaryDirectory(prefix="fsl-layout-") as directory:
            rebuilt = pathlib.Path(directory)
            checked([sys.executable, root / "tools/register_layout_migrate.py", "--fission-root", args.fission_root.resolve(), "--output-dir", rebuilt])
            names = ["bpf.le.registers.fslregs", "ebpf.le.registers.fslregs", "ebpf.be.registers.fslregs", "layout-migration.json"]
            for name in names:
                data = (rebuilt / name).read_bytes()
                if (golden / name).read_bytes() != data:
                    raise ValueError("layout artifact mismatch: " + name)
                report["artifact_hashes"][name] = hashlib.sha256(data).hexdigest()
            if args.fslc:
                fslc = args.fslc.resolve()
                report["fslc_sha256"] = hashlib.sha256(fslc.read_bytes()).hexdigest()
                for name in names[:3]:
                    result = checked([fslc, "check-layout", rebuilt / name])
                    report["native_checks"].append({"gate": "layout-parse", "source": name, "stdout": result.stdout.strip()})
                for name in names[1:3]:
                    result = checked([fslc, "link-abi", first / "ebpf.fslabi", rebuilt / name], expected_text="stack=R10@register:80+8")
                    report["native_checks"].append({"gate": "abi-link", "source": name, "status": "linked", "stdout": result.stdout.strip()})
                result = checked([fslc, "link-abi", first / "bpf.fslabi", rebuilt / names[0]], expected_code=1,
                                 expected_text="stack pointer RS width 4 differs from ABI pointer_size 8")
                report["native_checks"].append({"gate": "abi-link", "source": names[0], "status": "expected-refusal", "stderr": result.stderr.strip()})
                package = rebuilt / "ebpf.fslc"
                checked([fslc, "compile", first / "ebpf-add64-register.fsl", package])
                for name in names[1:3]:
                    result = checked([fslc, "execute-layout", rebuilt / name, first / "ebpf.fslabi", package, "ebpf.le.add64.register",
                                      "0f12000000000000", "R0,R1,R2", "0,1,0xffffffffffffffff"], expected_text="status=Success registers=[0, 1, 0]")
                    report["native_checks"].append({"gate": "linked-leaf-reference", "source": name, "stdout": result.stdout.strip()})
            report["status"] = "passed"
    except (OSError, ValueError) as exc:
        report["error"] = str(exc)
        print(f"register_layout_reproduce: {exc}", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    if report["status"] == "passed":
        print(f"register layout reproduction: 4 artifacts match; native gates={len(report['native_checks'])}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
