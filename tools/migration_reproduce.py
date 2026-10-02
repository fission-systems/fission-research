#!/usr/bin/env python3
"""Rebuild migration artifacts and verify them against the captured snapshot."""
import argparse
import pathlib
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fission-root", type=pathlib.Path, default=pathlib.Path("Fission"))
    parser.add_argument("--fslc", type=pathlib.Path)
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    golden = root / "experiments/migration/first-slice"
    try:
        with tempfile.TemporaryDirectory(prefix="fsl-migration-") as directory:
            rebuilt = pathlib.Path(directory)
            subprocess.run([sys.executable, str(root / "tools/fsl_migrate.py"), "--fission-root", str(args.fission_root.resolve()), "--output-dir", str(rebuilt)], check=True)
            names = ["ebpf-add64-register.fsl", "bpf.fslabi", "ebpf.fslabi", "migration.json"]
            for name in names:
                if (golden / name).read_bytes() != (rebuilt / name).read_bytes():
                    raise ValueError(f"migration artifact mismatch: {name}")
            if args.fslc:
                fslc = str(args.fslc.resolve())
                for name in ["bpf.fslabi", "ebpf.fslabi"]:
                    subprocess.run([fslc, "check-abi", str(rebuilt / name)], check=True, stdout=subprocess.PIPE)
                package = rebuilt / "ebpf.fslc"
                subprocess.run([fslc, "compile", str(rebuilt / "ebpf-add64-register.fsl"), str(package)], check=True, stdout=subprocess.PIPE)
                observed = subprocess.run([fslc, "execute-state", str(package), "ebpf.le.add64.register", "0f12000000000000", "0,1,0xffffffffffffffff", "0"], check=True, capture_output=True, text=True).stdout
                if observed.strip() != "status=Success registers=[0, 1, 0] flags=[0]":
                    raise ValueError(f"unexpected migrated leaf behavior: {observed}")
        print("migration reproduction: 4 artifacts match;" + (" ABI/FSL compiler and CLI passed" if args.fslc else " compiler not requested"))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"migration_reproduce: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
