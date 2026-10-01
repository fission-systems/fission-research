#!/usr/bin/env python3
"""Build a provenance-bearing structural inventory of a directory of .sla files."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

from sla_probe import SlaError, inspect


def scan(root: pathlib.Path) -> dict:
    files = sorted(root.rglob("*.sla"))
    rows = []
    errors = []
    for path in files:
        try:
            item = inspect(path, include_tree=False)
            rows.append({
                "path": path.relative_to(root).as_posix(),
                "format_version": item["format_version"],
                "file_size": item["file_size"],
                "payload_size": item["payload_size"],
                "element_node_count": item["element_node_count"],
                "max_depth": item["max_depth"],
                "file_sha256": item["file_sha256"],
                "payload_sha256": item["payload_sha256"],
            })
        except (OSError, SlaError, ValueError) as exc:
            errors.append({"path": path.relative_to(root).as_posix(), "error": str(exc)})

    versions = collections.Counter(str(row["format_version"]) for row in rows)
    result = {
        "source_root": str(root),
        "file_count": len(files),
        "parsed_count": len(rows),
        "error_count": len(errors),
        "versions": dict(sorted(versions.items())),
        "totals": {
            "file_bytes": sum(row["file_size"] for row in rows),
            "payload_bytes": sum(row["payload_size"] for row in rows),
            "element_nodes": sum(row["element_node_count"] for row in rows),
        },
        "artifacts": rows,
        "errors": errors,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=pathlib.Path, help="directory to scan recursively")
    parser.add_argument("--output", "-o", type=pathlib.Path, help="write JSON report to this file")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(f"sla_corpus_scan: not a directory: {args.root}", file=sys.stderr)
        return 2
    result = scan(args.root)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 1 if result["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
