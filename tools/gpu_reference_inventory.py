#!/usr/bin/env python3
"""Inventory local GPU references without importing or executing upstream code.

Run from any directory; stdout is the reproducible TOML reference lock file.
Clones are intentionally local reference material rather than Git submodules.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
REPOS = (
    ("envytools", "nvidia", "COPYING"),
    ("CuAssembler", "nvidia", "LICENCE.md"),
    ("isa_spec_manager", "amd", "LICENSE"),
    ("radeon_gpu_analyzer", "amd", "LICENSE.txt"),
    ("intel-graphics-compiler", "intel", "LICENSE.md"),
)


def quoted(value):
    return json.dumps(value, ensure_ascii=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(path, *args):
    return subprocess.check_output(
        ["git", "-C", str(path), *args], text=True
    ).strip()


def main():
    print('format = "fission.gpu-references.v1"')
    print(f'captured_at = {quoted(datetime.now(timezone.utc).isoformat())}')
    print('purpose = "source reference; no runtime integration"')
    for name, vendor, license_file in REPOS:
        path = ROOT / "Vendor" / name
        print("\n[[repository]]")
        fields = {
            "name": name,
            "vendor": vendor,
            "path": str(path.relative_to(ROOT)),
            "url": git(path, "remote", "get-url", "origin"),
            "commit": git(path, "rev-parse", "HEAD"),
            "shallow": git(path, "rev-parse", "--is-shallow-repository") == "true",
            "license_file": license_file,
            "license_sha256": digest(path / license_file),
            "working_tree_status": git(path, "status", "--short"),
        }
        for key, value in fields.items():
            print(f"{key} = {str(value).lower() if isinstance(value, bool) else quoted(value)}")
    base = ROOT / "Vendor" / "amd-machine-readable-isa"
    print("\n[amd_xml_archive]")
    print('source_url = "https://gpuopen.com/download/machine-readable-isa/latest/"')
    print('path = "Vendor/amd-machine-readable-isa/specs.zip"')
    print(f'sha256 = {quoted(digest(base / "specs.zip"))}')
    files = sorted((base / "extracted").glob("*.xml"))
    if not files:
        raise RuntimeError("AMD XML archive has not been extracted")
    for path in files:
        root = ET.parse(path).getroot()
        print("\n[[amd_xml]]")
        for key, value in {
            "path": str(path.relative_to(ROOT)),
            "sha256": digest(path),
            "architecture": root.findtext("./ISA/Architecture/ArchitectureName"),
            "schema": root.findtext("./Document/SchemaVersion"),
            "release_date": root.findtext("./Document/ReleaseDate"),
            "license": root.findtext("./Document/License"),
            "copyright": root.findtext("./Document/Copyright"),
        }.items():
            if value is None:
                raise ValueError(f"Missing {key} in {path}")
            print(f"{key} = {quoted(value)}")
        print(f'instruction_records = {len(root.findall("./ISA/Instructions/Instruction"))}')
        print(f'encoding_records = {len(root.findall("./ISA/Encodings/Encoding"))}')


if __name__ == "__main__":
    main()
