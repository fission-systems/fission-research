#!/usr/bin/env python3
"""Decode fixed-layout little-endian HSA AQL kernel dispatch packets.

This is a packet/ABI probe, not an AMDGPU instruction decoder. It preserves
the raw packet and reserved fields so newer runtime uses are not discarded.
The default layout is the 64-bit HSA large model used by current ROCm GPU
processes; --pointer-model=32 selects the small-model kernarg pointer layout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys
from typing import Any


PACKET_SIZE = 64
MAX_INPUT_BYTES = 256 * 1024 * 1024
PACKET_PREFIX = struct.Struct("<6H5I")

PACKET_TYPES = {
    0: "vendor_specific",
    1: "invalid",
    2: "kernel_dispatch",
    3: "barrier_and",
    4: "agent_dispatch",
    5: "barrier_or",
}
FENCE_SCOPES = {0: "none", 1: "agent", 2: "system"}


class ProbeError(Exception):
    """Raised for malformed inputs or layouts outside this probe's scope."""


def hex_pointer(value: int, pointer_model: int) -> str:
    return f"0x{value:0{pointer_model // 4}x}"


def hex64(value: int) -> str:
    return f"0x{value:016x}"


def enum_name(value: int, values: dict[int, str], prefix: str) -> str:
    return values.get(value, f"{prefix}_{value}")


def parse_packet(raw: bytes, file_offset: int, index: int, pointer_model: int) -> dict[str, Any]:
    if len(raw) != PACKET_SIZE:
        raise ProbeError(f"packet {index} is {len(raw)} bytes, expected {PACKET_SIZE}")

    (
        header,
        setup,
        workgroup_x,
        workgroup_y,
        workgroup_z,
        reserved0,
        grid_x,
        grid_y,
        grid_z,
        private_segment_size,
        group_segment_size,
    ) = PACKET_PREFIX.unpack_from(raw)

    packet_type = header & 0xFF
    if packet_type != 2:
        raise ProbeError(
            f"packet {index} at file offset {file_offset} has type {packet_type}; "
            "this probe accepts HSA kernel dispatch packets only"
        )

    kernel_object = struct.unpack_from("<Q", raw, 32)[0]
    if pointer_model == 64:
        kernarg_address = struct.unpack_from("<Q", raw, 40)[0]
        reserved1 = None
    else:
        kernarg_address = struct.unpack_from("<I", raw, 40)[0]
        reserved1 = struct.unpack_from("<I", raw, 44)[0]
    reserved2 = struct.unpack_from("<Q", raw, 48)[0]
    completion_signal = struct.unpack_from("<Q", raw, 56)[0]

    acquire_scope = (header >> 9) & 0x3
    release_scope = (header >> 11) & 0x3
    dimensions = setup & 0x3

    return {
        "index": index,
        "file_offset": file_offset,
        "raw_hex": raw.hex(),
        "header": {
            "raw": f"0x{header:04x}",
            "packet_type": enum_name(packet_type, PACKET_TYPES, "packet_type"),
            "barrier": bool((header >> 8) & 1),
            "acquire_fence_scope": enum_name(acquire_scope, FENCE_SCOPES, "fence_scope"),
            "release_fence_scope": enum_name(release_scope, FENCE_SCOPES, "fence_scope"),
            "reserved_bits": (header >> 13) & 0x7,
        },
        "setup": {
            "raw": f"0x{setup:04x}",
            "dimensions": dimensions,
            "reserved_bits": setup >> 2,
        },
        "workgroup_size": [workgroup_x, workgroup_y, workgroup_z],
        "reserved0": reserved0,
        "grid_size": [grid_x, grid_y, grid_z],
        "private_segment_size": private_segment_size,
        "group_segment_size": group_segment_size,
        "kernel_object": hex64(kernel_object),
        "kernarg_address": hex_pointer(kernarg_address, pointer_model),
        "reserved1": reserved1,
        "reserved2": hex64(reserved2),
        "completion_signal": hex64(completion_signal),
    }


def parse_file(data: bytes, base_offset: int, count: int | None, pointer_model: int) -> list[dict[str, Any]]:
    if base_offset < 0 or base_offset > len(data):
        raise ProbeError(f"offset {base_offset} is outside the input")

    available = len(data) - base_offset
    if count is None:
        if available % PACKET_SIZE != 0:
            raise ProbeError(
                f"{available} bytes remain at offset {base_offset}; pass --count for a bounded slice"
            )
        count = available // PACKET_SIZE
    if count < 1:
        raise ProbeError("packet count must be at least 1")
    required = count * PACKET_SIZE
    if required > available:
        raise ProbeError(
            f"requested {count} packets ({required} bytes), but only {available} bytes remain"
        )

    packets = []
    for index in range(count):
        packet_offset = base_offset + index * PACKET_SIZE
        raw = data[packet_offset : packet_offset + PACKET_SIZE]
        packets.append(parse_packet(raw, packet_offset, index, pointer_model))
    return packets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path, help="raw packet capture or packet fixture")
    parser.add_argument("--offset", type=int, default=0, help="first packet byte offset (default: 0)")
    parser.add_argument("--count", type=int, help="number of consecutive 64-byte packets")
    parser.add_argument(
        "--pointer-model",
        type=int,
        choices=(32, 64),
        default=64,
        help="HSA kernarg pointer width (default: 64-bit large model)",
    )
    args = parser.parse_args()

    try:
        input_size = args.input.stat().st_size
        if input_size > MAX_INPUT_BYTES:
            raise ProbeError(f"input size {input_size} exceeds {MAX_INPUT_BYTES} bytes")
        data = args.input.read_bytes()
        if len(data) > MAX_INPUT_BYTES:
            raise ProbeError(f"input size {len(data)} exceeds {MAX_INPUT_BYTES} bytes")
        packets = parse_file(data, args.offset, args.count, args.pointer_model)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ProbeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    document = {
        "format": "hsa_aql_kernel_dispatch_packet",
        "format_version": 1,
        "byte_order": "little",
        "packet_size": PACKET_SIZE,
        "pointer_model_bits": args.pointer_model,
        "input": {
            "name": args.input.name,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "offset": args.offset,
        },
        "packets": packets,
    }
    json.dump(document, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
