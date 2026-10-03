#!/usr/bin/env python3
"""Regenerate the owned signature catalog and optional native-reader evidence."""
import argparse
import json
import pathlib
import subprocess
import tempfile
from fsl_library_migrate import migrate, check_pinned_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fission-root", type=pathlib.Path, default=pathlib.Path("Fission"))
    parser.add_argument("--fslc", type=pathlib.Path)
    parser.add_argument("--report", type=pathlib.Path, default=pathlib.Path("artifacts/library-migration.json"))
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"validation": "failed", "native_reader": "not-executed"}, indent=2) + "\n")
    root = pathlib.Path(__file__).resolve().parents[1]
    expected = json.loads((root / "experiments/migration/asset-replacement/library-migration.json").read_text())
    relative = expected["source"]["path"]
    check_pinned_source(args.fission_root, relative)
    source, binary, report = migrate(args.fission_root / relative, relative)
    if report != expected:
        raise ValueError("library artifact/provenance mismatch")
    report = dict(report, validation="passed", reproduction="identical", native_reader="not-requested")
    if args.fslc:
        with tempfile.TemporaryDirectory(prefix="fsl-library-") as directory:
            package = pathlib.Path(directory) / "clib64.fsldb"
            package.write_bytes(binary)
            fslc = str(args.fslc.resolve())
            result = subprocess.run([fslc, "library-inspect", str(package)], text=True, capture_output=True, check=True).stdout
            if not result.startswith(f"prototype-candidates={expected['records']} type-resolution=unresolved "):
                raise ValueError("unexpected native library inspection")
            for symbol, spelling in [("memcpy", "void*"), ("malloc", "void*"), ("printf", "int")]:
                result = subprocess.run([fslc, "library-query", str(package), symbol], text=True, capture_output=True, check=True).stdout
                if f'symbol: "{symbol}"' not in result or f'return_spelling: "{spelling}"' not in result or "variadic: Unknown" not in result or not result.startswith("type-resolution=unresolved"):
                    raise ValueError("native candidate query changed evidence")
            report["native_reader"] = "passed: all records decoded; 3 exact queries"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"library reproduction: {expected['records']} candidates / {expected['parameters']} parameters identical; {report['native_reader']}")


if __name__ == "__main__":
    main()
