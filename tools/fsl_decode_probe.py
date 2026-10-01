#!/usr/bin/env python3
"""Decode fixed-width instruction words from an experimental FSL pattern package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "data/patterns/amdgpu-gfx900.json"
MAX_INPUT_BYTES = 256 * 1024 * 1024


class DecodeError(ValueError):
    pass


def extract_fields(
    word: int, pattern: dict[str, Any], offset: int, word_bits: int
) -> dict[str, int]:
    fields: dict[str, int] = {}
    for field_id, field in pattern.get("fields", {}).items():
        try:
            start = int(field["start_bit"])
            width = int(field["width"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DecodeError(f"invalid field definition {field_id!r} at 0x{offset:x}") from exc
        if start < 0 or width <= 0 or start + width > word_bits:
            raise DecodeError(
                f"field {field_id!r} exceeds the {word_bits}-bit word at 0x{offset:x}"
            )
        fields[field_id] = (word >> start) & ((1 << width) - 1)
    return fields


def selector_table_operand(code: int, table: dict[str, Any], offset: int) -> dict[str, Any]:
    for case in table.get("cases", []):
        if code != int(case["code"]):
            continue
        kind = case["kind"]
        if kind == "unsupported":
            raise DecodeError(f"instruction at 0x{offset:x}: {case['reason']} (selector {code})")
        if kind == "special_register":
            return {"kind": kind, "name": case["name"], "text": case["text"]}
        if kind == "inline_integer":
            return {"kind": kind, "value": int(case["value"]), "text": case["text"]}

    for rule in table.get("ranges", []):
        if int(rule["start"]) <= code <= int(rule["end"]):
            value = code * int(rule["scale"]) + int(rule["offset"])
            kind = rule["kind"]
            rendered = rule["render"].format(value=value)
            if kind == "inline_integer":
                return {"kind": kind, "value": value, "text": rendered}
            return {"kind": kind, "index": value, "text": rendered}
    raise DecodeError(f"instruction at 0x{offset:x} uses unsupported or reserved selector code {code}")


def decode_operand(
    operand_spec: dict[str, Any], value: int, profile: dict[str, Any], offset: int
) -> dict[str, Any]:
    transform = operand_spec["transform"]
    if transform == "register_index":
        class_id = operand_spec["register_class"]
        register_class = profile["register_classes"][class_id]
        count = int(register_class["count"])
        if not 0 <= value < count:
            raise DecodeError(f"unsupported {class_id} register index {value} at 0x{offset:x}")
        return {
            "kind": class_id,
            "index": value,
            "text": f"{register_class['prefix']}{value}",
        }
    if transform == "selector_table":
        table = profile["selector_tables"][operand_spec["table"]]
        return selector_table_operand(value, table, offset)
    raise DecodeError(f"unsupported operand transform {transform!r} at 0x{offset:x}")


def constraint_failure(
    pattern: dict[str, Any], fields: dict[str, int], offset: int
) -> str | None:
    decode_spec = pattern.get("decode", {})
    for constraint in decode_spec.get("constraints", []):
        field_id = constraint.get("field")
        expected = int(constraint.get("equals"))
        actual = fields.get(field_id)
        if actual != expected:
            field = pattern["fields"][field_id]
            width = (int(field["width"]) + 3) // 4
            return (
                f"instruction at 0x{offset:x} has {field.get('name', field_id)} "
                f"0x{actual:0{width}x}, expected 0x{expected:0{width}x}"
            )
    return None


def decode_pattern(
    word: int,
    pattern: dict[str, Any],
    profile: dict[str, Any],
    offset: int,
    word_bits: int,
) -> tuple[list[dict[str, Any]], str, dict[str, str]]:
    fields = extract_fields(word, pattern, offset, word_bits)
    decode_spec = pattern.get("decode", {})
    operands: list[dict[str, Any]] = []
    render_values: dict[str, str] = {"mnemonic": pattern["mnemonic"]}
    for operand_spec in decode_spec.get("operands", []):
        name = operand_spec["name"]
        field_id = operand_spec["field"]
        operand = decode_operand(operand_spec, fields[field_id], profile, offset)
        operands.append(operand)
        render_values[name] = operand["text"]

    try:
        rendered = decode_spec["render"].format_map(render_values)
    except (KeyError, ValueError) as exc:
        raise DecodeError(f"invalid render template for {pattern['pattern_id']!r}") from exc

    reserved: dict[str, str] = {}
    for field_id in decode_spec.get("reserved_fields", []):
        field = pattern["fields"][field_id]
        width = (int(field["width"]) + 3) // 4
        reserved[str(field.get("name", field_id))] = f"0x{fields[field_id]:0{width}x}"
    return operands, rendered, reserved


def resolve_provenance(
    pattern: dict[str, Any], profile: dict[str, Any], offset: int
) -> list[dict[str, Any]]:
    source_items = profile.get("sources", [])
    if not isinstance(source_items, list):
        raise DecodeError("pattern profile sources must be an array")
    sources = {
        source["source_id"]: source
        for source in source_items
        if isinstance(source, dict) and isinstance(source.get("source_id"), str)
    }
    evidence_items = pattern.get("provenance", [])
    if not isinstance(evidence_items, list) or not evidence_items:
        raise DecodeError(f"pattern {pattern.get('pattern_id')!r} has no provenance")

    resolved: list[dict[str, Any]] = []
    for evidence in evidence_items:
        if not isinstance(evidence, dict):
            raise DecodeError(f"pattern provenance is malformed at 0x{offset:x}")
        source_id = evidence.get("source_id")
        source = sources.get(source_id)
        if source is None:
            raise DecodeError(
                f"pattern provenance references unknown source {source_id!r} at 0x{offset:x}"
            )
        resolved.append(
            {
                **evidence,
                "source_metadata": {
                    key: value for key, value in source.items() if key != "source_id"
                },
            }
        )
    return resolved


def load_profile(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        profile = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DecodeError(f"invalid pattern profile {path}: {exc}") from exc
    if profile.get("format") != "fission_research_isa_pattern_db":
        raise DecodeError(f"unsupported pattern database format in {path}")
    architecture = profile.get("architecture")
    if not isinstance(architecture, dict):
        raise DecodeError("pattern profile has no architecture table")
    word_bits = architecture.get("instruction_word_bits")
    if isinstance(word_bits, bool) or not isinstance(word_bits, int):
        raise DecodeError("instruction_word_bits must be an integer")
    if word_bits < 8 or word_bits > 256 or word_bits % 8:
        raise DecodeError("fixed-width decoder requires byte-aligned words in 8..256 bits")
    if architecture.get("endianness") not in {"little", "big"}:
        raise DecodeError("architecture endianness must be 'little' or 'big'")
    return profile, raw


def decode(data: bytes, offset: int, profile: dict[str, Any]) -> list[dict[str, Any]]:
    if offset < 0 or offset > len(data):
        raise DecodeError(f"offset {offset} is outside input size {len(data)}")
    architecture = profile["architecture"]
    word_bits = int(architecture["instruction_word_bits"])
    word_bytes = word_bits // 8
    endianness = architecture["endianness"]
    if (len(data) - offset) % word_bytes:
        raise DecodeError(
            f"selected input range is not a whole number of {word_bits}-bit words"
        )

    patterns = profile.get("patterns", [])
    decoded: list[dict[str, Any]] = []
    for absolute_offset in range(offset, len(data), word_bytes):
        raw = data[absolute_offset : absolute_offset + word_bytes]
        word = int.from_bytes(raw, endianness)
        matches = [
            item
            for item in patterns
            if word & int(item["match"]["mask"], 0) == int(item["match"]["value"], 0)
        ]
        accepted: list[tuple[dict[str, Any], dict[str, int]]] = []
        rejected: list[str] = []
        for item in matches:
            fields = extract_fields(word, item, absolute_offset, word_bits)
            failure = constraint_failure(item, fields, absolute_offset)
            if failure:
                rejected.append(failure)
            else:
                accepted.append((item, fields))
        if len(accepted) != 1:
            if not accepted and rejected:
                raise DecodeError(rejected[0])
            if not matches:
                reason = f"no pattern in profile {profile.get('profile_id')!r} matches"
            else:
                reason = "ambiguous pattern database match"
            digits = (word_bits + 3) // 4
            raise DecodeError(f"{reason} at 0x{absolute_offset:x}: 0x{word:0{digits}x}")

        pattern, _fields = accepted[0]
        operands, rendered, reserved = decode_pattern(
            word, pattern, profile, absolute_offset, word_bits
        )
        decoded.append(
            {
                "offset": absolute_offset,
                "size": word_bytes,
                "raw_bytes": raw.hex(),
                "raw_word": f"0x{word:0{(word_bits + 3) // 4}x}",
                "pattern_id": pattern["pattern_id"],
                "mnemonic": pattern["mnemonic"],
                "rendered": rendered,
                "operands": operands,
                "reserved_or_uninterpreted": reserved,
                "fir_effect_candidate": pattern["fir_effect"],
                "provenance": resolve_provenance(pattern, profile, absolute_offset),
            }
        )
    return decoded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="raw fixed-width instruction bytes")
    parser.add_argument("--offset", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--patterns", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--output", "-o", type=Path, help="write decoded JSON")
    args = parser.parse_args()

    try:
        if args.input.stat().st_size > MAX_INPUT_BYTES:
            raise DecodeError(f"input exceeds {MAX_INPUT_BYTES} bytes")
        data = args.input.read_bytes()
        profile, profile_bytes = load_profile(args.patterns)
        instructions = decode(data, args.offset, profile)
    except (OSError, DecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"fsl_decode_probe: {exc}", file=sys.stderr)
        return 2

    result = {
        "format": "fission_research_fsl_decode_probe",
        "format_version": 1,
        "target": profile["architecture"]["target"],
        "instruction_word_bits": profile["architecture"]["instruction_word_bits"],
        "endianness": profile["architecture"]["endianness"],
        "profile_id": profile["profile_id"],
        "pattern_profile_sha256": hashlib.sha256(profile_bytes).hexdigest(),
        "compiled_from": profile.get("compiled_from"),
        "compiler": profile.get("compiler"),
        "input": {
            "name": args.input.name,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "offset": args.offset,
        },
        "execution_performed": False,
        "instructions": instructions,
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        except OSError as exc:
            print(f"fsl_decode_probe: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
