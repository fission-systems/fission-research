#!/usr/bin/env python3
"""Project one spec-derived FIR candidate into several consumer-facing views."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class ProjectionError(ValueError):
    pass


def parse_integer_type(value: Any) -> tuple[int, str]:
    if not isinstance(value, str):
        raise ProjectionError("FIR candidate input_type must be a string")
    match = re.fullmatch(r"int([1-9][0-9]*)", value)
    if not match:
        raise ProjectionError(f"unsupported integer type {value!r}")
    return int(match.group(1)), "signed"


def project(decoded_result: dict[str, Any]) -> dict[str, Any]:
    instructions = decoded_result.get("instructions")
    if not isinstance(instructions, list) or len(instructions) != 1:
        raise ProjectionError("this projection probe expects exactly one decoded instruction")
    instruction = instructions[0]
    if instruction.get("pattern_id") != "jvm.se26.iadd":
        raise ProjectionError("this projection probe currently models only jvm.se26.iadd")

    effect = instruction.get("fir_effect_candidate")
    if not isinstance(effect, dict):
        raise ProjectionError("decoded instruction has no FIR effect candidate")
    if effect.get("operation") != "arith.add" or effect.get("domain") != "vm_operand_stack":
        raise ProjectionError("candidate is not the expected operand-stack integer addition")

    width_bits, signedness = parse_integer_type(effect.get("input_type"))
    result_width, result_signedness = parse_integer_type(effect.get("output_type"))
    pops = effect.get("pops")
    pushes = effect.get("pushes")
    if width_bits != 32 or result_width != width_bits or result_signedness != signedness:
        raise ProjectionError("this first code-generation slice requires matching signed 32-bit types")
    if pops != ["int32", "int32"] or pushes != ["int32"]:
        raise ProjectionError("unexpected operand-stack signature for this iadd slice")
    if effect.get("overflow") != "wrap_low_32_bits":
        raise ProjectionError("iadd projection requires the documented low-32-bit overflow rule")
    if effect.get("runtime_exception") != "none":
        raise ProjectionError("iadd projection requires the documented no-runtime-exception effect")

    source_provenance = instruction.get("provenance")
    if not isinstance(source_provenance, list) or not source_provenance:
        raise ProjectionError("decoded instruction has no evidence provenance")

    canonical = {
        "format": "fission_fir_candidate",
        "schema_version": 0,
        "operation_id": instruction["pattern_id"],
        "operation": {
            "kind": "integer.add",
            "domain": "vm_operand_stack",
            "type": {
                "kind": "integer",
                "width_bits": width_bits,
                "signedness": signedness,
                "representation": "two_complement_bitvector",
            },
        },
        "inputs": [
            {"id": "lhs", "role": "stack_value", "depth_from_top": 1, "type": "int32"},
            {"id": "rhs", "role": "stack_value", "depth_from_top": 0, "type": "int32"},
        ],
        "outputs": [{"id": "sum", "role": "stack_value", "type": "int32"}],
        "effects": {
            "operand_stack": {"pop_count": 2, "push_values": ["sum"]},
            "arithmetic": {
                "overflow": "wrap_low_32_bits",
                "result_is_low_bits": width_bits,
            },
            "runtime_exceptions": [],
        },
        "preconditions": ["The verifier-established top two operand-stack values have JVM type int."],
        "evidence": source_provenance,
        "evidence_status": "primary-specification-derived-candidate",
        "execution_semantics_implemented": False,
    }

    c_code = """#include <stdint.h>

uint32_t fir_jvm_iadd_bits(uint32_t lhs, uint32_t rhs) {
    return lhs + rhs;
}
"""
    rust_code = """pub fn fir_jvm_iadd_bits(lhs: u32, rhs: u32) -> u32 {
    lhs.wrapping_add(rhs)
}
"""

    return {
        "format": "fission_research_fir_projection_probe",
        "format_version": 1,
        "target": decoded_result.get("target"),
        "source_decode": {
            "format": decoded_result.get("format"),
            "profile_id": decoded_result.get("profile_id"),
            "pattern_profile_sha256": decoded_result.get("pattern_profile_sha256"),
            "input": decoded_result.get("input"),
        },
        "canonical_fir_candidate": canonical,
        "projections": {
            "bytecode_listing": {
                "status": "lossless-for-instruction-identity",
                "offset": instruction["offset"],
                "bytes": instruction["raw_bytes"],
                "text": instruction["rendered"],
                "opcode": instruction["raw_word"],
            },
            "c_source": {
                "status": "lossless-for-32-bit-result-bit-pattern",
                "type_mapping": "JVM int bit pattern -> C uint32_t",
                "code": c_code,
                "note": "The unsigned C view preserves result bits; it does not model Java source-level signed comparisons or formatting.",
            },
            "rust_source": {
                "status": "lossless-for-32-bit-result-bit-pattern",
                "type_mapping": "JVM int bit pattern -> Rust u32",
                "code": rust_code,
                "note": "wrapping_add makes the JVM low-32-bit result explicit.",
            },
            "stack_ir": {
                "status": "lossless-for-local-stack-transition",
                "operation": "i32.add.wrap",
                "inputs": ["stack[-2]", "stack[-1]"],
                "output": "sum32",
                "transition": {"pop": 2, "push": ["sum32"]},
                "precondition": "top two stack values are verifier-typed int32",
            },
            "sequential_ir_candidate": {
                "status": "value-semantics-preserved; stack mapping explicit",
                "dialect": "p-code-like research projection; not Ghidra P-code serialization",
                "operations": [
                    {
                        "opcode": "INT_ADD",
                        "inputs": ["stack[-2]", "stack[-1]"],
                        "output": "t0",
                        "width_bits": 32,
                        "overflow": "modulo_2^32",
                    }
                ],
                "stack_transition": {"pop": 2, "push": ["t0"]},
                "scope": "single-instruction arithmetic and local operand-stack effect",
            },
            "analysis_graph": {
                "status": "lossless-for-modeled-dataflow-and-stack-effect",
                "nodes": [
                    {"id": "lhs", "kind": "stack_input", "type": "int32"},
                    {"id": "rhs", "kind": "stack_input", "type": "int32"},
                    {"id": "add", "kind": "integer.add", "width_bits": 32, "overflow": "wrap_low_32_bits"},
                    {"id": "sum", "kind": "stack_output", "type": "int32"},
                ],
                "edges": [
                    {"from": "lhs", "to": "add", "role": "left_operand"},
                    {"from": "rhs", "to": "add", "role": "right_operand"},
                    {"from": "add", "to": "sum", "role": "result"},
                ],
                "stack_effect": {"pop": 2, "push": ["sum"]},
            },
            "ai_evidence_packet": {
                "status": "source-backed; not execution-validated",
                "claim": "JVM iadd (0x60) consumes two int values and pushes their low 32-bit sum; this instruction has no runtime exception.",
                "precondition": "A valid verified method frame supplies two int values on top of the operand stack.",
                "provenance": source_provenance,
                "input_sha256": (decoded_result.get("input") or {}).get("sha256"),
                "pattern_profile_sha256": decoded_result.get("pattern_profile_sha256"),
                "known_scope_limit": "One opcode only; no class-file parser, verifier, method CFG, or JVM execution was run.",
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded", type=Path, help="JSON output from fsl_decode_probe.py")
    parser.add_argument("--output", "-o", type=Path, help="write FIR projection JSON")
    args = parser.parse_args()
    try:
        decoded = json.loads(args.decoded.read_bytes())
        if not isinstance(decoded, dict):
            raise ProjectionError("decoded input must be a JSON object")
        result = project(decoded)
        encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"fir_projection_probe: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
