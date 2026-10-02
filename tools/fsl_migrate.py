#!/usr/bin/env python3
"""Strict offline migration probes. Source subsets are explicit, not full SLEIGH.

FSL/ABI source is the output; JSON is only the evidence report. Unsupported XML
attributes/nodes and changed Sleigh shapes are errors, never silently dropped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import subprocess
import xml.etree.ElementTree as ET

from sla_probe import inspect

SNAPSHOT = "96fc71f75cecdee305faf9497561c577a8955468"
DATA = frozenset("absolute_max_alignment machine_alignment default_alignment default_pointer_alignment pointer_size wchar_size short_size integer_size long_size long_long_size float_size double_size long_double_size".split())


class MigrationError(ValueError):
    pass


def quote(value: str) -> str:
    # FSL string escaping shares this subset with JSON; this is not a JSON source.
    return json.dumps(value, ensure_ascii=False)


def number(value: str) -> int:
    try:
        n = int(value, 16 if value.startswith("0x") else 10)
    except ValueError as exc:
        raise MigrationError(f"unsupported numeric value {value!r}") from exc
    if not 0 <= n < 1 << 64:
        raise MigrationError("integer outside u64")
    return n


def provenance(path: pathlib.Path, root: pathlib.Path) -> tuple[str, str]:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    return relative, hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(relative: str, digest: str, claim: str) -> str:
    url = f"https://github.com/fission-systems/Fission/blob/{SNAPSHOT}/{relative}"
    return f'evidence "ghidra-snapshot" {quote(url)} {quote("sha256:" + digest)} {quote(claim)};'


def cspec_source(path: pathlib.Path, root: pathlib.Path, profile: str) -> tuple[str, dict]:
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        raise MigrationError("DTD/entity input is unsupported")
    tree = ET.fromstring(raw)
    schema = {
        "compiler_spec": (set(), {"data_organization", "global", "stackpointer", "default_proto", "prototype"}),
        "data_organization": (set(), DATA | {"size_alignment_map"}),
        "size_alignment_map": (set(), {"entry"}),
        "entry": ({"size", "alignment"}, set()),
        "global": (set(), {"range"}),
        "range": ({"space"}, set()),
        "stackpointer": ({"register", "space"}, set()),
        "default_proto": (set(), {"prototype"}),
        "prototype": ({"name", "extrapop", "stackshift"}, {"input", "output", "unaffected", "killedbycall"}),
        "input": (set(), {"pentry"}),
        "output": ({"killedbycall"}, {"pentry"}),
        "pentry": ({"minsize", "maxsize"}, {"register"}),
        "register": ({"name"}, set()),
        "unaffected": (set(), {"register", "varnode"}),
        "killedbycall": (set(), {"register"}),
        "varnode": ({"space", "offset", "size"}, set()),
        **{name: ({"value"}, set()) for name in DATA},
    }
    if tree.tag != "compiler_spec":
        raise MigrationError("expected compiler_spec")
    for node in tree.iter():
        allowed_attrs, children = schema.get(node.tag, (set(), set()))
        if node.tag not in schema or set(node.attrib) - allowed_attrs:
            raise MigrationError(f"unsupported node/attributes: {node.tag} {node.attrib}")
        if any(child.tag not in children for child in node):
            raise MigrationError(f"unsupported children of {node.tag}")
        if (node.text or "").strip() or (node.tail or "").strip():
            raise MigrationError(f"unsupported text in {node.tag}")
        # Structural sections consumed once must not overwrite each other.
        singleton = children - {"prototype", "entry", "range", "pentry", "register", "varnode"}
        for tag in singleton:
            if len(node.findall(tag)) > 1:
                raise MigrationError(f"duplicate section {node.tag}/{tag}")

    def one(node: ET.Element, tag: str) -> ET.Element:
        matches = node.findall(tag)
        if len(matches) != 1:
            raise MigrationError(f"expected one {node.tag}/{tag}")
        return matches[0]

    def attr(node: ET.Element, key: str) -> str:
        try:
            return node.attrib[key]
        except KeyError as exc:
            raise MigrationError(f"missing {node.tag}@{key}") from exc

    relative, digest = provenance(path, root)
    lines = [f"abi {profile} {{", "    " + evidence(relative, digest, "Strict compiler metadata migration; byte units and ordered register entries retained. No ABI allocator or execution contract is inferred.")]
    organization = one(tree, "data_organization")
    data = {}
    for node in organization:
        if node.tag in DATA:
            data[node.tag] = number(attr(node, "value"))
            lines.append(f"    data {node.tag} {data[node.tag]};")
        else:
            seen = set()
            for entry in node:
                size, align = number(attr(entry, "size")), number(attr(entry, "alignment"))
                if size in seen or not size or not align:
                    raise MigrationError("duplicate/zero alignment entry")
                seen.add(size)
                lines.append(f"    alignment {size} {align};")
    for global_node in tree.findall("global"):
        for entry in global_node:
            lines.append(f"    global_space {quote(attr(entry, 'space'))};")
    sp = one(tree, "stackpointer")
    lines.append(f"    stack_pointer {quote(attr(sp, 'register'))} {quote(attr(sp, 'space'))};")
    default = one(one(tree, "default_proto"), "prototype")
    lines.append(f"    default_convention {quote(attr(default, 'name'))};")
    conventions = [default, *tree.findall("prototype")]
    names = set()
    for proto in conventions:
        name = attr(proto, "name")
        if name in names:
            raise MigrationError("duplicate convention")
        names.add(name)
        cleanup = attr(proto, "extrapop")
        cleanup = "unknown" if cleanup == "unknown" else str(number(cleanup))
        lines += [f"    convention {quote(name)} {{", f"        extrapop {cleanup};", f"        stackshift {number(attr(proto, 'stackshift'))};"]
        for direction in ["input", "output"]:
            entry_list = one(proto, direction)
            if direction == "output" and "killedbycall" in entry_list.attrib:
                flag = entry_list.attrib["killedbycall"]
                if flag not in ["true", "false"]:
                    raise MigrationError("invalid killedbycall boolean")
                lines.append(f"        output_killed_by_call {flag};")
            for entry in entry_list:
                reg = one(entry, "register")
                lo, hi = number(attr(entry, "minsize")), number(attr(entry, "maxsize"))
                if not lo or lo > hi:
                    raise MigrationError("invalid register entry size bounds")
                lines.append(f"        {direction}_register {quote(attr(reg, 'name'))} {lo} {hi};")
        for effect, keyword in [("unaffected", "preserved"), ("killedbycall", "clobbered")]:
            for node in proto.findall(effect):
                for entry in node:
                    if entry.tag == "register":
                        lines.append(f"        {keyword}_register {quote(attr(entry, 'name'))};")
                    else:
                        lines.append(f"        preserved_memory {quote(attr(entry, 'space'))} {number(attr(entry, 'offset'))} {number(attr(entry, 'size'))};")
        lines.append("    }")
    lines.append("}")
    if not data.get("pointer_size"):
        raise MigrationError("missing pointer_size")
    return "\n".join(lines) + "\n", {"source": relative, "sha256": digest, "xml_elements": sum(1 for _ in tree.iter()), "conventions": len(conventions), "status": "metadata-converted", "unsupported_nodes": 0}


def ebpf_add_source(root: pathlib.Path) -> tuple[str, dict]:
    directory = root / "utils/sleigh-specs/languages/eBPF"
    entry = directory / "eBPF_le.slaspec"
    source = directory / "eBPF.sinc"
    entry_text = re.sub(r"#.*", "", entry.read_text())
    if not re.fullmatch(r'\s*@define ENDIAN "little"\s*@include "eBPF.sinc"\s*', entry_text):
        raise MigrationError("unsupported entry preprocessor shape")
    text = re.sub(r"#.*", "", source.read_text())
    # Only this conditional is admitted; require the token and register binding.
    token = re.search(r'@if ENDIAN == "little"\s*define token instr\(64\)(.*?);', text, re.S)
    if not token:
        raise MigrationError("missing little-endian 64-bit token")
    fields = {m[0]: (int(m[1]), int(m[2])) for m in re.findall(r"(\w+)=\((\d+),\s*(\d+)\)", token[1])}
    required = {"src": (12, 15), "dst": (8, 11), "op_alu_jmp_opcode": (4, 7), "op_alu_jmp_source": (3, 3), "op_insn_class": (0, 2)}
    if any(fields.get(name) != span for name, span in required.items()):
        raise MigrationError("changed token fields")
    if not re.search(r"define register offset=0 size=8 \[\s*R0\s+R1\s+R2\s+R3\s+R4\s+R5\s+R6\s+R7\s+R8\s+R9\s+R10\s+PC\s*\];", text):
        raise MigrationError("changed register bank")
    binding = re.search(r"attach variables \[ src dst llvm_reg_callx \] \[(.*?)\];", text, re.S)
    if not binding or binding[1].split() != [*(f"R{i}" for i in range(11)), *(["_"] * 5)]:
        raise MigrationError("changed register selector binding")
    pattern = r":ADD\s+dst,\s*SRC8\s+is\s+SRC8\s*&\s*dst\s*&\s*op_alu_jmp_opcode=0x0\s*&\s*op_insn_class=0x7\s*\{\s*dst\s*=\s*dst\s*\+\s*SRC8;\s*\}"
    if len(re.findall(pattern, text)) != 1 or not re.search(r"SRC8:\s*src\s+is\s+src\s*&\s*op_alu_jmp_source=1\s*\{\s*export src;\s*\}", text):
        raise MigrationError("unsupported ADD/SRC8 constructor shape")
    relative, digest = provenance(source, root)
    erel, edigest = provenance(entry, root)
    result = f'''# Migrated leaf subset; other constructors and immediate ADD are unsupported.
# Logical register slots R0..R10; unused off/imm bytes are retained by reencoding.
language ebpf.le.add64.register {{
    byte_order little;
    address_unit byte;
    instruction add64_register {{
        encoding 64 mask 0xff value 0x0f {{
            field destination offset 8 bits 4 exclude 11, 12, 13, 14, 15;
            field source offset 12 bits 4 exclude 11, 12, 13, 14, 15;
        }}
        mnemonic "ADD";
        {evidence(relative, digest, "Leaf ADD dst,SRC8 with SRC8 register branch; 64-bit modulo sum. Logical bank slots preserve Sleigh R0..R10 binding. eBPF verifier restrictions are not inferred.")}
        {evidence(erel, edigest, "Entry selects little endian and includes eBPF.sinc.")}
        semantics {{
            %lhs: u64 = register.read destination;
            %rhs: u64 = register.read source;
            %sum: u64 = u64.add.wrap %lhs, %rhs;
            register.write destination, %sum;
        }}
    }}
}}
'''
    return result, {"source": relative, "sha256": digest, "entry": erel, "entry_sha256": edigest, "migrated_leaf_variants": 1, "scope": "little-endian ADD64 register leaf only; not full preprocessor or SLEIGH compiler"}


def inventory(root: pathlib.Path) -> dict:
    languages = root / "utils/sleigh-specs/languages"
    results = []
    for path in sorted(languages.rglob("*.cspec")):
        try:
            _, record = cspec_source(path, root, "probe.abi")
        except (MigrationError, ET.ParseError) as exc:
            relative, digest = provenance(path, root)
            record = {"source": relative, "sha256": digest, "status": "unsupported", "reason": str(exc)}
        results.append(record)
    return {"cspec_total": len(results), "cspec_metadata_converted": sum(r["status"] == "metadata-converted" for r in results), "cspec": results, "slaspec_files": len(list(languages.rglob("*.slaspec"))), "sinc_files": len(list(languages.rglob("*.sinc"))), "sla_files": len(list((root / "utils/sleigh-specs/compiled").rglob("*.sla")))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fission-root", required=True, type=pathlib.Path)
    parser.add_argument("--output-dir", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        commit = subprocess.run(["git", "-C", str(args.fission_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        if commit != SNAPSHOT:
            raise MigrationError(f"migration input requires pinned snapshot {SNAPSHOT}; found {commit}")
        output = args.output_dir
        sources = []
        artifacts = {}
        fsl, record = ebpf_add_source(args.fission_root)
        artifacts["ebpf-add64-register.fsl"] = fsl
        sources.append(record)
        for processor in ["BPF", "eBPF"]:
            path = args.fission_root / f"utils/sleigh-specs/languages/{processor}/{processor}.cspec"
            abi, record = cspec_source(path, args.fission_root, f"{processor.lower()}.compiler")
            artifacts[f"{processor.lower()}.fslabi"] = abi
            sources.append(record)
        sla = args.fission_root / "utils/sleigh-specs/compiled/eBPF/eBPF_le.sla"
        structural = inspect(sla, include_tree=False)
        structural["path"] = sla.relative_to(args.fission_root).as_posix()
        structural["semantic_migration_status"] = "unsupported; numeric packed tree is only structural evidence"
        report = {"format": "fission-fsl-migration-probe", "source_snapshot": SNAPSHOT,
                  "sources": sources, "sla": structural, "inventory": inventory(args.fission_root),
                  "outputs": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in artifacts.items()}}
        report["license"] = {"upstream": "Ghidra Apache-2.0; see Fission NOTICE and THIRD_PARTY.md", "files": {name: hashlib.sha256((args.fission_root / name).read_bytes()).hexdigest() for name in ["LICENSE", "NOTICE", "THIRD_PARTY.md"]}}
        output.mkdir(parents=True, exist_ok=True)
        for name, text in artifacts.items():
            (output / name).write_text(text)
        (output / "migration.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"FSL leaves=1 ABI profiles=2; cspec admitted={report['inventory']['cspec_metadata_converted']}/{report['inventory']['cspec_total']}")
    except (OSError, MigrationError, ET.ParseError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"fsl_migrate: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
