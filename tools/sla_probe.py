#!/usr/bin/env python3
"""Inspect the outer header and packed tree of a Ghidra .sla artifact.

This is an independent research probe. Element and attribute IDs intentionally
remain numeric until they are mapped against versioned format definitions.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys
import zlib
from typing import Any


MAGIC = b"sla"
HEADER_SIZE = 4
HEADER_MASK = 0xC0
ELEMENT_START = 0x40
ELEMENT_END = 0x80
ATTRIBUTE = 0xC0
HEADER_EXTEND = 0x20
ELEMENT_ID_MASK = 0x1F
RAW_MASK = 0x7F

ATTR_TYPES = {
    1: "boolean",
    2: "signed-positive",
    3: "signed-negative",
    4: "unsigned",
    5: "address-space",
    6: "special-space",
    7: "string",
}

MAX_COMPRESSED_BYTES = 256 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_TREE_DEPTH = 16_384
SLA_V4 = 4
SPECIAL_SPACES = {
    0: "stack",
    1: "join",
    2: "fspec",
    3: "iop",
    4: "spacebase",
}


class SlaError(Exception):
    pass


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.elements: collections.Counter[int] = collections.Counter()
        self.attributes: collections.Counter[tuple[int, str]] = collections.Counter()
        self.strings = 0
        self.max_string_bytes = 0
        self.max_depth = 0

    def byte(self) -> int:
        if self.pos >= len(self.data):
            raise SlaError(f"unexpected end of payload at offset {self.pos}")
        value = self.data[self.pos]
        self.pos += 1
        return value

    def header(self) -> tuple[int, int]:
        header = self.byte()
        kind = header & HEADER_MASK
        ident = header & ELEMENT_ID_MASK
        if header & HEADER_EXTEND:
            ident = (ident << 7) | (self.byte() & RAW_MASK)
        return kind, ident

    def integer(self, length: int) -> int:
        if length > 10:
            raise SlaError(f"packed integer has {length} groups at offset {self.pos}")
        value = 0
        for _ in range(length):
            if value > (0xFFFFFFFFFFFFFFFF >> 7):
                raise SlaError(f"packed integer exceeds 64 bits at offset {self.pos}")
            value = (value << 7) | (self.byte() & RAW_MASK)
        return value

    def attribute(self, ident: int) -> dict[str, Any]:
        type_byte = self.byte()
        attr_type = type_byte >> 4
        length = type_byte & 0x0F
        type_name = ATTR_TYPES.get(attr_type)
        if type_name is None:
            raise SlaError(f"unknown attribute type {attr_type} at offset {self.pos - 1}")

        if attr_type == 1:
            if length not in (0, 1):
                raise SlaError(f"invalid boolean encoding {length} at offset {self.pos - 1}")
            value: Any = bool(length)
        elif attr_type in (2, 3, 4, 5):
            value = self.integer(length)
            if attr_type == 2 and value > 0x7FFFFFFFFFFFFFFF:
                raise SlaError(f"positive signed value exceeds 64 bits at offset {self.pos}")
            if attr_type == 3:
                if value > (1 << 63):
                    raise SlaError(f"negative signed magnitude exceeds 64 bits at offset {self.pos}")
                value = -(1 << 63) if value == (1 << 63) else -value
        elif attr_type == 6:
            value = {"code": length, "name": SPECIAL_SPACES.get(length, "unknown")}
        else:
            string_size = self.integer(length)
            end = self.pos + string_size
            if end > len(self.data):
                raise SlaError(f"string extends past payload at offset {self.pos}")
            raw = self.data[self.pos:end]
            try:
                value = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SlaError(f"invalid UTF-8 string at offset {self.pos}: {exc}") from exc
            self.pos = end
            self.strings += 1
            self.max_string_bytes = max(self.max_string_bytes, string_size)

        self.attributes[(ident, type_name)] += 1
        return {"id": ident, "type": type_name, "value": value}

    def parse(self, build_tree: bool) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        root: dict[str, Any] | None = None
        stack: list[dict[str, Any]] = []
        saw_child: list[bool] = []

        while self.pos < len(self.data):
            kind, ident = self.header()
            if kind == ELEMENT_START:
                node: dict[str, Any] = {"id": ident, "attrs": [], "children": []}
                self.elements[ident] += 1
                if stack:
                    if build_tree:
                        stack[-1]["children"].append(node)
                    saw_child[-1] = True
                elif root is None:
                    root = node
                else:
                    raise SlaError(f"multiple root elements; second root at offset {self.pos}")
                stack.append(node)
                saw_child.append(False)
                if len(stack) > MAX_TREE_DEPTH:
                    raise SlaError(f"tree exceeds maximum depth {MAX_TREE_DEPTH}")
                self.max_depth = max(self.max_depth, len(stack))
            elif kind == ATTRIBUTE:
                if not stack:
                    raise SlaError(f"attribute outside element at offset {self.pos}")
                if saw_child[-1]:
                    raise SlaError(f"attribute after child element at offset {self.pos}")
                attr = self.attribute(ident)
                if build_tree:
                    stack[-1]["attrs"].append(attr)
            elif kind == ELEMENT_END:
                if not stack:
                    raise SlaError(f"element end outside root at offset {self.pos}")
                node = stack.pop()
                saw_child.pop()
                if node["id"] != ident:
                    raise SlaError(
                        f"element end ID {ident} does not match open element {node['id']}"
                    )
            else:
                raise SlaError(f"unknown header kind {kind:#x} at offset {self.pos - 1}")

        if stack:
            raise SlaError(f"payload ended with {len(stack)} unclosed elements")
        if root is None:
            raise SlaError("payload contains no root element")
        stats = {
            "root_element_id": root["id"],
            "element_counts": {str(k): v for k, v in sorted(self.elements.items())},
            "attribute_counts": {
                f"{ident}:{kind}": count
                for (ident, kind), count in sorted(self.attributes.items())
            },
            "element_node_count": sum(self.elements.values()),
            "max_depth": self.max_depth,
            "string_count": self.strings,
            "max_string_bytes": self.max_string_bytes,
        }
        return (root if build_tree else None), stats


def decompress_limited(stream: bytes) -> bytes:
    decoder = zlib.decompressobj()
    out = bytearray()
    chunk_size = 64 * 1024
    for start in range(0, len(stream), chunk_size):
        part = stream[start : start + chunk_size]
        while part:
            remaining = MAX_UNCOMPRESSED_BYTES - len(out)
            piece = decoder.decompress(part, remaining + 1)
            out.extend(piece)
            if len(out) > MAX_UNCOMPRESSED_BYTES:
                raise SlaError(
                    f"decompressed payload exceeds {MAX_UNCOMPRESSED_BYTES} bytes"
                )
            part = decoder.unconsumed_tail
            if not part:
                break
    out.extend(decoder.flush(MAX_UNCOMPRESSED_BYTES - len(out) + 1))
    if len(out) > MAX_UNCOMPRESSED_BYTES:
        raise SlaError(f"decompressed payload exceeds {MAX_UNCOMPRESSED_BYTES} bytes")
    if not decoder.eof:
        raise SlaError("truncated zlib stream")
    if decoder.unused_data:
        raise SlaError(f"unexpected {len(decoder.unused_data)} trailing bytes after zlib stream")
    return bytes(out)


def inspect(path: pathlib.Path, include_tree: bool) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > MAX_COMPRESSED_BYTES:
        raise SlaError(f"file exceeds {MAX_COMPRESSED_BYTES} byte input limit")
    if len(raw) < HEADER_SIZE + 1:
        raise SlaError("file is too short to contain an SLA header and zlib stream")
    if raw[:3] != MAGIC:
        raise SlaError("missing 'sla' magic")
    if raw[3] != SLA_V4:
        raise SlaError(f"no packed/zlib decoder for SLA format version {raw[3]}")

    payload = decompress_limited(raw[HEADER_SIZE:])
    reader = Reader(payload)
    tree, stats = reader.parse(build_tree=include_tree)
    result: dict[str, Any] = {
        "path": str(path),
        "format_version": raw[3],
        "file_size": len(raw),
        "payload_size": len(payload),
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        **stats,
    }
    if include_tree:
        result["tree"] = tree
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sla", type=pathlib.Path, help="compiled .sla artifact")
    parser.add_argument("--tree", action="store_true", help="include the full numeric-ID tree")
    parser.add_argument("--output", "-o", type=pathlib.Path, help="write JSON to this file")
    args = parser.parse_args()

    try:
        result = inspect(args.sla, include_tree=args.tree)
        encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
    except (OSError, SlaError, zlib.error) as exc:
        print(f"sla_probe: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
