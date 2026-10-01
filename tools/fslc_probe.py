#!/usr/bin/env python3
"""Compile the experimental TOML FSL slice into a versioned pattern package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FSL_FORMAT = "fission_fsl_experimental"
FSL_VERSION = "0.0.1"
PACKAGE_FORMAT = "fission_research_isa_pattern_db"
PACKAGE_VERSION = 1
SUPPORTED_TRANSFORMS = {"register_index", "selector_table"}
MAX_SOURCE_BYTES = 16 * 1024 * 1024


class FslError(ValueError):
    pass


def parse_int(value: Any, where: str) -> int:
    if isinstance(value, bool):
        raise FslError(f"{where} must be an integer or base-prefixed string")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError as exc:
            raise FslError(f"{where} is not an integer literal: {value!r}") from exc
    raise FslError(f"{where} must be an integer or base-prefixed string")


def validate(spec: dict[str, Any], source_name: str) -> None:
    if spec.get("format") != FSL_FORMAT:
        raise FslError(f"{source_name}: expected format {FSL_FORMAT!r}")
    if spec.get("language_version") != FSL_VERSION:
        raise FslError(f"{source_name}: unsupported FSL experiment version")

    profile_id = spec.get("profile_id")
    architecture = spec.get("architecture")
    if not isinstance(profile_id, str) or not profile_id:
        raise FslError(f"{source_name}: profile_id is required")
    if not isinstance(architecture, dict):
        raise FslError(f"{source_name}: [architecture] is required")
    word_bits = parse_int(architecture.get("instruction_word_bits"), "instruction_word_bits")
    if word_bits < 8 or word_bits > 256 or word_bits % 8:
        raise FslError(
            f"{source_name}: instruction_word_bits must be byte-aligned and in 8..256"
        )
    if architecture.get("endianness") not in {"little", "big"}:
        raise FslError(f"{source_name}: architecture endianness must be 'little' or 'big'")

    register_classes = spec.get("register_classes", {})
    if not isinstance(register_classes, dict):
        raise FslError(f"{source_name}: register_classes must be a table")
    for class_id, register_class in register_classes.items():
        if not isinstance(register_class, dict):
            raise FslError(f"{source_name}: register class {class_id!r} must be a table")
        count = parse_int(register_class.get("count"), f"register class {class_id}.count")
        width = parse_int(register_class.get("width_bits"), f"register class {class_id}.width_bits")
        if count <= 0 or width <= 0:
            raise FslError(f"{source_name}: register class {class_id!r} has invalid dimensions")
        if not isinstance(register_class.get("prefix"), str):
            raise FslError(f"{source_name}: register class {class_id!r} has no display prefix")

    selector_tables = spec.get("selector_tables", {})
    if not isinstance(selector_tables, dict):
        raise FslError(f"{source_name}: selector_tables must be a table")
    for table_id, table in selector_tables.items():
        where = f"{source_name}: selector table {table_id!r}"
        if not isinstance(table, dict):
            raise FslError(f"{where} must be a table")
        input_bits = parse_int(table.get("input_bits"), f"{where}.input_bits")
        if input_bits <= 0 or input_bits > 32:
            raise FslError(f"{where}.input_bits must be in 1..32")
        code_limit = 1 << input_bits
        if table.get("fallback") != "unsupported":
            raise FslError(f"{where}.fallback must be 'unsupported' in this prototype")
        ranges = table.get("ranges", [])
        cases = table.get("cases", [])
        if not isinstance(ranges, list) or not isinstance(cases, list):
            raise FslError(f"{where} ranges and cases must be arrays")
        covered: list[tuple[int, int, str]] = []
        for range_index, rule in enumerate(ranges):
            rule_where = f"{where}.ranges[{range_index}]"
            if not isinstance(rule, dict):
                raise FslError(f"{rule_where} must be a table")
            start = parse_int(rule.get("start"), f"{rule_where}.start")
            end = parse_int(rule.get("end"), f"{rule_where}.end")
            if start < 0 or end < start or end >= code_limit:
                raise FslError(f"{rule_where} is outside the {input_bits}-bit selector space")
            kind = rule.get("kind")
            if kind not in register_classes and kind != "inline_integer":
                raise FslError(f"{rule_where} has unsupported result kind {kind!r}")
            scale = parse_int(rule.get("scale"), f"{rule_where}.scale")
            value_offset = parse_int(rule.get("offset"), f"{rule_where}.offset")
            if not isinstance(rule.get("render"), str):
                raise FslError(f"{rule_where}.render is required")
            first = start * scale + value_offset
            last = end * scale + value_offset
            if kind in register_classes:
                count = int(register_classes[kind]["count"])
                if min(first, last) < 0 or max(first, last) >= count:
                    raise FslError(f"{rule_where} produces an index outside register class {kind!r}")
            covered.append((start, end, f"range {range_index}"))
        seen_cases: set[int] = set()
        for case_index, case in enumerate(cases):
            case_where = f"{where}.cases[{case_index}]"
            if not isinstance(case, dict):
                raise FslError(f"{case_where} must be a table")
            code = parse_int(case.get("code"), f"{case_where}.code")
            if code < 0 or code >= code_limit or code in seen_cases:
                raise FslError(f"{case_where} has an invalid or duplicate selector code")
            seen_cases.add(code)
            kind = case.get("kind")
            if kind not in {"special_register", "inline_integer", "unsupported"}:
                raise FslError(f"{case_where} has unsupported result kind {kind!r}")
            if kind == "special_register" and not all(
                isinstance(case.get(key), str) and case[key]
                for key in ("name", "text")
            ):
                raise FslError(f"{case_where} requires name and text")
            if kind == "inline_integer":
                parse_int(case.get("value"), f"{case_where}.value")
                if not isinstance(case.get("text"), str):
                    raise FslError(f"{case_where}.text is required")
            if kind == "unsupported" and not isinstance(case.get("reason"), str):
                raise FslError(f"{case_where}.reason is required")
            covered.append((code, code, f"case {case_index}"))
        covered.sort()
        for previous, current in zip(covered, covered[1:]):
            if current[0] <= previous[1]:
                raise FslError(f"{where}: selector ranges/cases overlap")

    sources = spec.get("sources")
    patterns = spec.get("patterns")
    if not isinstance(sources, list) or not sources:
        raise FslError(f"{source_name}: at least one [[sources]] entry is required")
    if not isinstance(patterns, list) or not patterns:
        raise FslError(f"{source_name}: at least one [[patterns]] entry is required")

    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise FslError(f"{source_name}: sources[{index}] must be a table")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise FslError(f"{source_name}: sources[{index}] has no source_id")
        if source_id in source_ids:
            raise FslError(f"{source_name}: duplicate source_id {source_id!r}")
        source_ids.add(source_id)

    pattern_ids: set[str] = set()
    normalized: list[tuple[str, int, int]] = []
    for index, pattern in enumerate(patterns):
        where = f"{source_name}: patterns[{index}]"
        if not isinstance(pattern, dict):
            raise FslError(f"{where} must be a table")
        pattern_id = pattern.get("pattern_id")
        if not isinstance(pattern_id, str) or not pattern_id:
            raise FslError(f"{where} has no pattern_id")
        if pattern_id in pattern_ids:
            raise FslError(f"{where} duplicates pattern_id {pattern_id!r}")
        pattern_ids.add(pattern_id)

        match = pattern.get("match")
        if not isinstance(match, dict):
            raise FslError(f"{where}.match must be a table")
        mask = parse_int(match.get("mask"), f"{where}.match.mask")
        value = parse_int(match.get("value"), f"{where}.match.value")
        limit = (1 << word_bits) - 1
        if mask <= 0 or mask > limit:
            raise FslError(f"{where}: match mask does not fit {word_bits} bits")
        if value < 0 or value > limit or value & mask != value:
            raise FslError(f"{where}: match value must fit and contain no bits outside its mask")
        normalized.append((pattern_id, mask, value))

        fields = pattern.get("fields")
        if not isinstance(fields, dict):
            raise FslError(f"{where}.fields must be a table")
        for field_id, field in fields.items():
            field_where = f"{where}.fields.{field_id}"
            if not isinstance(field, dict):
                raise FslError(f"{field_where} must be a table")
            start = parse_int(field.get("start_bit"), f"{field_where}.start_bit")
            width = parse_int(field.get("width"), f"{field_where}.width")
            if start < 0 or width <= 0 or start + width > word_bits:
                raise FslError(f"{field_where} extends outside the {word_bits}-bit instruction")
            if not isinstance(field.get("name"), str) or not field["name"]:
                raise FslError(f"{field_where}.name is required")
            if "value" in field:
                fixed = parse_int(field["value"], f"{field_where}.value")
                field_limit = 1 << width
                if fixed < 0 or fixed >= field_limit:
                    raise FslError(f"{field_where}.value does not fit its field")
                field_mask = (field_limit - 1) << start
                if mask & field_mask != field_mask:
                    raise FslError(f"{field_where}.value is not fully fixed by the pattern mask")
                if (value >> start) & (field_limit - 1) != fixed:
                    raise FslError(f"{field_where}.value disagrees with the pattern match value")

        decode = pattern.get("decode")
        if not isinstance(decode, dict) or not isinstance(decode.get("render"), str):
            raise FslError(f"{where}.decode.render must be a string")
        operand_names: set[str] = set()
        operands = decode.get("operands", [])
        if not isinstance(operands, list):
            raise FslError(f"{where}.decode.operands must be an array")
        for operand_index, operand in enumerate(operands):
            operand_where = f"{where}.decode.operands[{operand_index}]"
            if not isinstance(operand, dict):
                raise FslError(f"{operand_where} must be a table")
            name = operand.get("name")
            field_id = operand.get("field")
            transform = operand.get("transform")
            if not isinstance(name, str) or not name or name in operand_names:
                raise FslError(f"{operand_where} has a missing or duplicate name")
            operand_names.add(name)
            if field_id not in fields:
                raise FslError(f"{operand_where} references unknown field {field_id!r}")
            if transform not in SUPPORTED_TRANSFORMS:
                raise FslError(f"{operand_where} uses unsupported transform {transform!r}")
            if transform == "register_index":
                class_id = operand.get("register_class")
                if class_id not in register_classes:
                    raise FslError(f"{operand_where} references unknown register class {class_id!r}")
            if transform == "selector_table":
                table_id = operand.get("table")
                if table_id not in selector_tables:
                    raise FslError(f"{operand_where} references unknown selector table {table_id!r}")
        reserved = decode.get("reserved_fields", [])
        if not isinstance(reserved, list) or any(field_id not in fields for field_id in reserved):
            raise FslError(f"{where}.decode.reserved_fields references an unknown field")
        constraints = decode.get("constraints", [])
        if not isinstance(constraints, list):
            raise FslError(f"{where}.decode.constraints must be an array")
        for constraint in constraints:
            if not isinstance(constraint, dict) or constraint.get("field") not in fields:
                raise FslError(f"{where}.decode constraint references an unknown field")
            expected = parse_int(constraint.get("equals"), f"{where}.decode constraint equals")
            width = parse_int(fields[constraint["field"]].get("width"), f"{where} field width")
            if expected < 0 or expected >= (1 << width):
                raise FslError(f"{where}.decode constraint value does not fit its field")

        provenance = pattern.get("provenance")
        if not isinstance(provenance, list) or not provenance:
            raise FslError(f"{where}.provenance must contain at least one evidence link")
        for item in provenance:
            if not isinstance(item, dict) or item.get("source_id") not in source_ids:
                raise FslError(f"{where}.provenance references an unknown source_id")
            if not isinstance(item.get("claim"), str) or not item["claim"]:
                raise FslError(f"{where}.provenance claim is required")
        if not isinstance(pattern.get("fir_effect"), dict):
            raise FslError(f"{where}.fir_effect must be a candidate effect table")

    for index, (left_id, left_mask, left_value) in enumerate(normalized):
        for right_id, right_mask, right_value in normalized[index + 1 :]:
            common = left_mask & right_mask
            if (left_value ^ right_value) & common == 0:
                raise FslError(
                    f"{source_name}: patterns {left_id!r} and {right_id!r} overlap; "
                    "this prototype has no priority/ambiguity resolution"
                )


def compile_spec(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > MAX_SOURCE_BYTES:
        raise FslError(f"source exceeds {MAX_SOURCE_BYTES} bytes")
    try:
        spec = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise FslError(f"invalid UTF-8/TOML FSL source: {exc}") from exc
    validate(spec, str(path))

    try:
        source_name = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        source_name = path.name
    return {
        "format": PACKAGE_FORMAT,
        "schema_version": PACKAGE_VERSION,
        "profile_id": spec["profile_id"],
        "architecture": spec["architecture"],
        "register_classes": spec.get("register_classes", {}),
        "selector_tables": spec.get("selector_tables", {}),
        "sources": spec["sources"],
        "patterns": spec["patterns"],
        "unsupported_behavior": spec.get("unsupported_behavior", []),
        "compiled_from": {
            "format": FSL_FORMAT,
            "language_version": FSL_VERSION,
            "path": source_name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "compiler": {"name": "fslc_probe", "version": "0.0.1"},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="experimental TOML FSL source")
    parser.add_argument("--output", "-o", type=Path, help="write compiled package JSON")
    args = parser.parse_args()
    try:
        package = compile_spec(args.source)
        encoded = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
    except (OSError, FslError) as exc:
        print(f"fslc_probe: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
