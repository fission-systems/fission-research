#!/usr/bin/env python3
"""Hash the pinned legacy asset set; inventory is not semantic migration."""
import argparse
import hashlib
import json
import pathlib
import subprocess

from fsl_library_migrate import SNAPSHOT

TARGETS = {".slaspec": ".fsl", ".sinc": ".fsl modules", ".sla": ".fslc",
           ".cspec": ".fslabi", ".pspec": ".fslregs + processor policy",
           ".ldefs": "owned profile manifest", ".fpk": ".fslib/.fsldb or family-specific corpus schema"}


def inventory(root):
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != SNAPSHOT:
        raise ValueError("inventory input must match pinned reference commit")
    rows = []
    for path in sorted((root / "utils").rglob("*")):
        if path.is_file() and path.suffix in TARGETS:
            blob = path.read_bytes()
            rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(blob),
                         "sha256": hashlib.sha256(blob).hexdigest(), "family": path.suffix,
                         "replacement": TARGETS[path.suffix], "status": "inventoried-only"})
    return {"schema": 1, "source_commit": head,
            "scope": "pinned utils assets; inventory does not assert migration or coverage",
            "counts": {suffix: sum(row["family"] == suffix for row in rows) for suffix in TARGETS},
            "assets": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fission-root", type=pathlib.Path, default=pathlib.Path("Fission"))
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("artifacts/legacy-assets.json"))
    args = parser.parse_args()
    report = inventory(args.fission_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(report["counts"])


if __name__ == "__main__":
    main()
