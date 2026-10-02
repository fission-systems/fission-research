#!/usr/bin/env python3
"""Migrate the pinned BPF/eBPF declaration prefix, not instruction semantics."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

from fsl_migrate import MigrationError, SNAPSHOT, evidence, number, provenance, quote


def layout_source(root: pathlib.Path, processor: str, byte_order: str = "little") -> tuple[str, dict]:
    if processor not in {"BPF", "eBPF"} or byte_order not in {"little", "big"}:
        raise MigrationError("only BPF/eBPF explicit little/big entries are admitted")
    if processor == "BPF" and byte_order != "little":
        raise MigrationError("pinned corpus has no BPF big-endian entry")
    folder = root / f"utils/sleigh-specs/languages/{processor}"
    entry = folder / f"{processor}_{'le' if byte_order == 'little' else 'be'}.slaspec"
    source = folder / f"{processor}.sinc"
    strip = lambda text: re.sub(r"#.*", "", text).strip()
    entry_text = strip(entry.read_text())
    expected = (rf'define endian={byte_order};\s*@include "BPF.sinc"' if processor == "BPF"
                else rf'@define ENDIAN "{byte_order}"\s*@include "eBPF.sinc"')
    if not re.fullmatch(expected, entry_text):
        raise MigrationError("unsupported layout entry preprocessor shape")
    text = strip(source.read_text())
    # Refuse declarations outside the admitted unconditional prefix. Do not
    # infer register metadata from comments, token fields or constructor names.
    token = re.search(r"define token\b", text)
    if not token:
        raise MigrationError("missing declaration-prefix delimiter")
    prefix = text[:token.start()]
    if processor == "eBPF":
        prefix = re.sub(r'@if ENDIAN == "little"\s*$', "", prefix)
        prefix, count = re.subn(r"define endian=\$\(ENDIAN\);", "", prefix)
        if count != 1:
            raise MigrationError("unsupported layout endian declaration")
    if re.search(r"define\s+(space|register)\b", text[token.start():]):
        raise MigrationError("register/space declarations outside admitted prefix")
    spaces = []
    registers = []
    default_spaces = []
    while prefix.strip():
        prefix = prefix.lstrip()
        space = re.match(r"define space (\w+) type=(ram_space|register_space) size=(\d+)( default)?;", prefix)
        register = re.match(r"define register offset=(0x[0-9a-fA-F]+|\d+) size=(\d+) \[(.*?)\];", prefix, re.S)
        if space:
            name, kind, width, default = space.groups()
            if default:
                default_spaces.append(name)
            spaces.append({"name": name, "kind": "register" if kind == "register_space" else "memory", "address_bytes": number(width)})
            prefix = prefix[space.end():]
        elif register:
            offset, width, names = register.groups()
            offset, width = number(offset), number(width)
            if not 1 <= width <= 512:
                raise MigrationError("unsupported register width")
            for i, name in enumerate(names.split()):
                if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
                    raise MigrationError("unsupported register identifier")
                if name != "_":
                    registers.append({"name": name, "space": "register", "offset": offset + i * width, "size_bytes": width})
            prefix = prefix[register.end():]
        else:
            raise MigrationError("unsupported declaration prefix: " + prefix[:100])
    if len(default_spaces) != 1 or not spaces or not registers:
        raise MigrationError("layout requires one default space and explicit register views")
    if len({r["name"] for r in registers}) != len(registers) or len({s["name"] for s in spaces}) != len(spaces):
        raise MigrationError("duplicate register/space names")
    bank = next((s for s in spaces if s["name"] == "register" and s["kind"] == "register"), None)
    if bank is None or any(not 1 <= s["address_bytes"] <= 8 for s in spaces):
        raise MigrationError("unsupported space address size or register space")
    if any(r["offset"] + r["size_bytes"] > 1 << (bank["address_bytes"] * 8) for r in registers):
        raise MigrationError("register view exceeds address space")
    relative, digest = provenance(source, root)
    erel, edigest = provenance(entry, root)
    name = f"{processor.lower()}.{'le' if byte_order == 'little' else 'be'}.registers"
    lines = [f"layout {name} {{", "    " + evidence(relative, digest, "Unconditional space/register declaration prefix; byte offsets, holes and overlapping views retained. No instruction or subregister extension semantics inferred."),
             "    " + evidence(erel, edigest, "Entry fixes byte order for the admitted declaration prefix."),
             f"    default_space {quote(default_spaces[0])};"]
    for s in spaces:
        lines.append(f'    space {quote(s["name"])} {s["kind"]} {s["address_bytes"]} byte {byte_order};')
    for r in registers:
        lines.append(f'    register {quote(r["name"])} {quote(r["space"])} {r["offset"]} {r["size_bytes"]};')
    lines.append("}")
    pairs = [[a["name"], b["name"]] for i, a in enumerate(registers) for b in registers[i+1:]
             if a["offset"] < b["offset"] + b["size_bytes"] and b["offset"] < a["offset"] + a["size_bytes"]]
    return "\n".join(lines) + "\n", {"profile": name, "source": relative, "sha256": digest, "entry": erel, "entry_sha256": edigest,
                                      "byte_order": byte_order, "spaces": spaces, "registers": registers, "overlapping_pairs": pairs}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fission-root", type=pathlib.Path, required=True)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        commit = subprocess.run(["git", "-C", str(args.fission_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        if commit != SNAPSHOT:
            raise MigrationError("layout migration requires pinned snapshot " + SNAPSHOT)
        artifacts, sources = {}, []
        for processor in ["BPF", "eBPF"]:
            for byte_order in (["little"] if processor == "BPF" else ["little", "big"]):
                text, record = layout_source(args.fission_root, processor, byte_order)
                artifacts[record["profile"] + ".fslregs"] = text
                sources.append(record)
        report = {"format": "fission-register-layout-migration-v1", "source_snapshot": SNAPSHOT, "sources": sources,
                  "outputs": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in artifacts.items()},
                  "license": {"upstream": "Ghidra Apache-2.0", "files": {name: hashlib.sha256((args.fission_root / name).read_bytes()).hexdigest() for name in ["LICENSE", "NOTICE", "THIRD_PARTY.md"]}},
                  "scope": "BPF little-endian and eBPF little/big-endian unconditional byte-addressed declaration prefixes; no full SLEIGH preprocessing or direct SLA conversion"}
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, text in artifacts.items():
            (args.output_dir / name).write_text(text)
        (args.output_dir / "layout-migration.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"register layouts={len(sources)}; BPF views={len(sources[0]['registers'])} overlapping pairs={len(sources[0]['overlapping_pairs'])}; eBPF views={len(sources[1]['registers'])}")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"register_layout_migrate: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
