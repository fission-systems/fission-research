#!/usr/bin/env python3
"""Inspect a narrow, independent subset of AMDGPU ELF code objects.

This research parser intentionally supports ELF64 little-endian objects for
EM_AMDGPU only. It reports container facts, section/symbol tables, ELF notes,
and executable-section hashes. It does not decode GPU instructions or claim
that LLVM-emitted metadata is semantically correct.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys
from typing import Any


ELF_MAGIC = b"\x7fELF"
ELFCLASS64 = 2
ELFDATA2LSB = 1
EM_AMDGPU = 224
SHT_SYMTAB = 2
SHT_DYNSYM = 11
SHT_NOTE = 7
SHT_NOBITS = 8
ET_REL = 1
ET_EXEC = 2
ET_DYN = 3

ELF64_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
ELF64_SECTION = struct.Struct("<IIQQQQIIQQ")
ELF64_SYMBOL = struct.Struct("<IBBHQQ")
ELF_NOTE_HEADER = struct.Struct("<III")

MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_SECTION_COUNT = 65_536
MAX_NOTE_TEXT_BYTES = 16 * 1024 * 1024

ELF_TYPES = {ET_REL: "ET_REL", ET_EXEC: "ET_EXEC", ET_DYN: "ET_DYN"}


class ProbeError(Exception):
    """Raised when the input is malformed or outside this probe's scope."""


def checked_slice(data: bytes, offset: int, size: int, what: str) -> bytes:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise ProbeError(f"{what} extends beyond the input: offset={offset}, size={size}")
    return data[offset : offset + size]


def c_string(table: bytes, offset: int, what: str) -> str:
    if offset < 0 or offset >= len(table):
        raise ProbeError(f"{what} string offset {offset} is outside its table")
    end = table.find(b"\0", offset)
    if end < 0:
        raise ProbeError(f"{what} string at offset {offset} is not terminated")
    return table[offset:end].decode("utf-8", errors="replace")


class MessagePackReader:
    """Small bounded decoder for the MessagePack value types used by AMDGPU notes."""

    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
        self.values_seen = 0

    def take(self, size: int) -> bytes:
        value = checked_slice(self.data, self.offset, size, "MessagePack value")
        self.offset += size
        return value

    def unsigned(self, size: int) -> int:
        return int.from_bytes(self.take(size), "big", signed=False)

    def signed(self, size: int) -> int:
        return int.from_bytes(self.take(size), "big", signed=True)

    def string(self, size: int) -> str:
        raw = self.take(size)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProbeError(f"invalid UTF-8 MessagePack string at offset {self.offset - size}") from exc

    def sequence_size(self, size: int) -> int:
        if size > 1_000_000:
            raise ProbeError(f"MessagePack container size {size} exceeds the probe limit")
        return size

    def value(self, depth: int = 0) -> Any:
        if depth > 128:
            raise ProbeError("MessagePack nesting exceeds 128 levels")
        self.values_seen += 1
        if self.values_seen > 2_000_000:
            raise ProbeError("MessagePack value count exceeds the probe limit")

        tag = self.unsigned(1)
        if tag <= 0x7F:
            return tag
        if tag >= 0xE0:
            return tag - 0x100
        if 0x80 <= tag <= 0x8F:
            return self.map(tag & 0x0F, depth)
        if 0x90 <= tag <= 0x9F:
            return self.array(tag & 0x0F, depth)
        if 0xA0 <= tag <= 0xBF:
            return self.string(tag & 0x1F)

        if tag == 0xC0:
            return None
        if tag == 0xC1:
            raise ProbeError("reserved MessagePack tag 0xc1")
        if tag == 0xC2:
            return False
        if tag == 0xC3:
            return True
        if tag in (0xC4, 0xC5, 0xC6):
            size_width = {0xC4: 1, 0xC5: 2, 0xC6: 4}[tag]
            size = self.sequence_size(self.unsigned(size_width))
            return {"msgpack_bin_hex": self.take(size).hex()}
        if tag in (0xC7, 0xC8, 0xC9):
            size_width = {0xC7: 1, 0xC8: 2, 0xC9: 4}[tag]
            return self.extension(self.sequence_size(self.unsigned(size_width)))
        if tag == 0xCA:
            return struct.unpack(">f", self.take(4))[0]
        if tag == 0xCB:
            return struct.unpack(">d", self.take(8))[0]
        if tag in (0xCC, 0xCD, 0xCE, 0xCF):
            size = {0xCC: 1, 0xCD: 2, 0xCE: 4, 0xCF: 8}[tag]
            return self.unsigned(size)
        if tag in (0xD0, 0xD1, 0xD2, 0xD3):
            size = {0xD0: 1, 0xD1: 2, 0xD2: 4, 0xD3: 8}[tag]
            return self.signed(size)
        if tag in (0xD4, 0xD5, 0xD6, 0xD7, 0xD8):
            size = {0xD4: 1, 0xD5: 2, 0xD6: 4, 0xD7: 8, 0xD8: 16}[tag]
            return self.extension(size)
        if tag in (0xD9, 0xDA, 0xDB):
            size_width = {0xD9: 1, 0xDA: 2, 0xDB: 4}[tag]
            return self.string(self.sequence_size(self.unsigned(size_width)))
        if tag in (0xDC, 0xDD):
            size_width = 2 if tag == 0xDC else 4
            return self.array(self.sequence_size(self.unsigned(size_width)), depth)
        if tag in (0xDE, 0xDF):
            size_width = 2 if tag == 0xDE else 4
            return self.map(self.sequence_size(self.unsigned(size_width)), depth)
        raise ProbeError(f"unsupported MessagePack tag 0x{tag:02x}")

    def array(self, size: int, depth: int) -> list[Any]:
        self.sequence_size(size)
        return [self.value(depth + 1) for _ in range(size)]

    def map(self, size: int, depth: int) -> dict[str, Any]:
        self.sequence_size(size)
        result: dict[str, Any] = {}
        for _ in range(size):
            key = self.value(depth + 1)
            if not isinstance(key, str):
                raise ProbeError("AMDGPU MessagePack metadata map has a non-string key")
            if key in result:
                raise ProbeError(f"duplicate MessagePack map key {key!r}")
            result[key] = self.value(depth + 1)
        return result

    def extension(self, size: int) -> dict[str, Any]:
        ext_type = self.signed(1)
        return {"msgpack_ext_type": ext_type, "msgpack_ext_hex": self.take(size).hex()}

    def parse(self) -> Any:
        result = self.value()
        if self.offset != len(self.data):
            raise ProbeError(
                f"MessagePack descriptor has {len(self.data) - self.offset} trailing bytes"
            )
        return result


def note_text(payload: bytes) -> str | None:
    if len(payload) > MAX_NOTE_TEXT_BYTES or b"\0" in payload:
        return None
    try:
        value = payload.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if any(not (char.isprintable() or char in "\r\n\t") for char in value):
        return None
    return value


def parse_notes(section_name: str, payload: bytes, base_offset: int) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    cursor = 0
    while cursor < len(payload):
        remaining = len(payload) - cursor
        if remaining < ELF_NOTE_HEADER.size:
            if all(byte == 0 for byte in payload[cursor:]):
                break
            raise ProbeError(f"truncated ELF note header in {section_name} at +{cursor}")

        name_size, desc_size, note_type = ELF_NOTE_HEADER.unpack_from(payload, cursor)
        cursor += ELF_NOTE_HEADER.size
        padded_name_size = (name_size + 3) & ~3
        padded_desc_size = (desc_size + 3) & ~3
        padded_name = checked_slice(
            payload, cursor, padded_name_size, f"{section_name} padded note name"
        )
        name = padded_name[:name_size]
        cursor += padded_name_size
        padded_descriptor = checked_slice(
            payload, cursor, padded_desc_size, f"{section_name} padded note descriptor"
        )
        descriptor = padded_descriptor[:desc_size]
        cursor += padded_desc_size
        text = note_text(descriptor)
        owner = name.rstrip(b"\0").decode("utf-8", errors="replace")
        metadata: Any = None
        metadata_error: str | None = None
        if owner == "AMDGPU" and note_type == 32:
            try:
                metadata = MessagePackReader(descriptor).parse()
            except ProbeError as exc:
                metadata_error = str(exc)
        notes.append(
            {
                "section": section_name,
                "file_offset": base_offset,
                "owner": owner,
                "type": note_type,
                "descriptor_size": desc_size,
                "descriptor_text": text,
                "descriptor_msgpack": metadata,
                "descriptor_msgpack_error": metadata_error,
                "descriptor_sha256": hashlib.sha256(descriptor).hexdigest(),
            }
        )
    return notes


def inspect(path: pathlib.Path, include_text: bool) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise ProbeError(f"input exceeds {MAX_INPUT_BYTES} byte limit")
    if len(raw) < ELF64_HEADER.size:
        raise ProbeError("input is too short to contain an ELF64 header")

    (
        ident,
        elf_type,
        machine,
        version,
        entry,
        program_header_offset,
        section_header_offset,
        flags,
        header_size,
        program_header_entry_size,
        program_header_count,
        section_header_entry_size,
        section_header_count,
        section_name_index,
    ) = ELF64_HEADER.unpack_from(raw)

    if ident[:4] != ELF_MAGIC:
        raise ProbeError("missing ELF magic")
    if ident[4] != ELFCLASS64:
        raise ProbeError(f"unsupported ELF class {ident[4]}; expected ELF64")
    if ident[5] != ELFDATA2LSB:
        raise ProbeError(f"unsupported ELF byte order {ident[5]}; expected little-endian")
    if machine != EM_AMDGPU:
        raise ProbeError(f"unsupported ELF machine {machine}; expected EM_AMDGPU (224)")
    if header_size != ELF64_HEADER.size:
        raise ProbeError(f"unexpected ELF header size {header_size}")
    if section_header_entry_size != ELF64_SECTION.size:
        raise ProbeError(
            f"unexpected section-header entry size {section_header_entry_size}"
        )
    if not section_header_count or section_header_count > MAX_SECTION_COUNT:
        raise ProbeError(f"unsupported section count {section_header_count}")
    if section_name_index >= section_header_count:
        raise ProbeError(f"section-name table index {section_name_index} is out of range")

    section_table_size = section_header_count * section_header_entry_size
    checked_slice(raw, section_header_offset, section_table_size, "section-header table")
    raw_sections: list[dict[str, int]] = []
    for index in range(section_header_count):
        offset = section_header_offset + index * section_header_entry_size
        (
            name_offset,
            section_type,
            section_flags,
            address,
            file_offset,
            size,
            link,
            info,
            address_alignment,
            entry_size,
        ) = ELF64_SECTION.unpack_from(raw, offset)
        if section_type != SHT_NOBITS:
            checked_slice(raw, file_offset, size, f"section {index}")
        raw_sections.append(
            {
                "index": index,
                "name_offset": name_offset,
                "type": section_type,
                "flags": section_flags,
                "address": address,
                "offset": file_offset,
                "size": size,
                "link": link,
                "info": info,
                "alignment": address_alignment,
                "entry_size": entry_size,
            }
        )

    name_section = raw_sections[section_name_index]
    if name_section["type"] != 3:
        raise ProbeError("section-name table is not SHT_STRTAB")
    section_names = checked_slice(
        raw, name_section["offset"], name_section["size"], "section-name string table"
    )

    sections: list[dict[str, Any]] = []
    for section in raw_sections:
        name = c_string(section_names, section["name_offset"], "section")
        record: dict[str, Any] = {
            "index": section["index"],
            "name": name,
            "type": section["type"],
            "flags": f"0x{section['flags']:x}",
            "address": f"0x{section['address']:x}",
            "offset": section["offset"],
            "size": section["size"],
            "alignment": section["alignment"],
            "entry_size": section["entry_size"],
        }
        if section["type"] != SHT_NOBITS:
            content = checked_slice(
                raw, section["offset"], section["size"], f"section {section['index']}"
            )
            if section["flags"] & 0x4:  # SHF_EXECINSTR
                record["content_sha256"] = hashlib.sha256(content).hexdigest()
                if include_text:
                    record["content_hex"] = content.hex()
        sections.append(record)

    symbols: list[dict[str, Any]] = []
    for section in raw_sections:
        if section["type"] not in (SHT_SYMTAB, SHT_DYNSYM):
            continue
        if section["entry_size"] != ELF64_SYMBOL.size or section["size"] % ELF64_SYMBOL.size:
            raise ProbeError(f"symbol table section {section['index']} has invalid entry size")
        if section["link"] >= section_header_count:
            raise ProbeError(f"symbol table section {section['index']} has invalid string table")
        string_section = raw_sections[section["link"]]
        if string_section["type"] != 3:
            raise ProbeError(f"symbol table section {section['index']} does not link to SHT_STRTAB")
        strings = checked_slice(
            raw, string_section["offset"], string_section["size"], "symbol string table"
        )
        count = section["size"] // ELF64_SYMBOL.size
        symbol_data = checked_slice(raw, section["offset"], section["size"], "symbol table")
        for index in range(count):
            name_offset, info, other, section_index, value, size = ELF64_SYMBOL.unpack_from(
                symbol_data, index * ELF64_SYMBOL.size
            )
            if section_index < section_header_count:
                symbol_section = sections[section_index]["name"]
            else:
                symbol_section = f"special:0x{section_index:x}"
            symbols.append(
                {
                    "table_section": section["index"],
                    "name": c_string(strings, name_offset, "symbol"),
                    "binding": info >> 4,
                    "type": info & 0x0F,
                    "visibility": other & 0x03,
                    "section": symbol_section,
                    "value": f"0x{value:x}",
                    "size": size,
                }
            )

    notes: list[dict[str, Any]] = []
    for section, record in zip(raw_sections, sections, strict=True):
        if section["type"] != SHT_NOTE:
            continue
        payload = checked_slice(raw, section["offset"], section["size"], "note section")
        notes.extend(parse_notes(record["name"], payload, section["offset"]))

    return {
        "path": str(path),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "elf": {
            "class": "ELF64",
            "byte_order": "little",
            "osabi": ident[7],
            "abi_version": ident[8],
            "type": ELF_TYPES.get(elf_type, f"unknown:{elf_type}"),
            "machine": machine,
            "version": version,
            "entry": f"0x{entry:x}",
            "flags": f"0x{flags:x}",
            "program_header_offset": program_header_offset,
            "program_header_entry_size": program_header_entry_size,
            "program_header_count": program_header_count,
        },
        "sections": sections,
        "symbols": symbols,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=pathlib.Path, help="ELF64 little-endian EM_AMDGPU object")
    parser.add_argument(
        "--include-text",
        action="store_true",
        help="include executable-section bytes as hex in JSON output",
    )
    args = parser.parse_args()
    try:
        result = inspect(args.path, include_text=args.include_text)
    except (OSError, ProbeError, struct.error) as exc:
        print(f"gpu_elf_probe: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
