#!/usr/bin/env python3
"""Offline FPK pipe-signature migration to owned TOML .fslib and binary .fsldb.

Prototype candidates retain unresolved type spellings. They are not verified
functions, ABI declarations, or executable FIR semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import subprocess
import tomllib
import zlib

SNAPSHOT = "96fc71f75cecdee305faf9497561c577a8955468"
MAX_BYTES = 128 * 1024 * 1024
MAX_TEXT = 16384
MAX_RECORDS = 1000000


def check_pinned_source(root, relative):
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    if head != SNAPSHOT:
        raise ValueError("library input must match pinned reference commit")
    committed = subprocess.run(["git", "-C", str(root), "show", f"{SNAPSHOT}:{relative}"],
                               capture_output=True, check=True).stdout
    if committed != (root / relative).read_bytes():
        raise ValueError("library source differs from recorded commit")


def text(value):
    if not isinstance(value, str) or not value or len(value.encode()) > MAX_TEXT:
        raise ValueError("invalid or oversized text")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("control character in text")
    return value


def fpk_rows(blob):
    if not 72 <= len(blob) <= MAX_BYTES or blob[:4] != b"FPK1":
        raise ValueError("invalid FPK header or size")
    kind, codec, count, blocks, offset, length = struct.unpack_from("<HHQQQQ", blob, 4)
    if (kind, codec) != (1, 1):
        raise ValueError("only pipe-text / zlib-row FPK admitted")
    if count > MAX_RECORDS or blocks > count or not 72 <= offset <= len(blob) or offset + length != len(blob):
        raise ValueError("invalid FPK bounds")
    if hashlib.sha256(blob[72:offset]).digest() != blob[40:72]:
        raise ValueError("FPK payload hash mismatch")
    rows, pos, payload_end, total = [], offset, 72, 0
    for _ in range(blocks):
        if pos + 4 > len(blob):
            raise ValueError("truncated FPK index")
        size = struct.unpack_from("<I", blob, pos)[0]
        pos += 4
        if not 0 < size <= MAX_TEXT or pos + size + 16 > len(blob):
            raise ValueError("invalid FPK key")
        key = text(blob[pos:pos+size].decode("utf-8"))
        pos += size
        start, packed, raw = struct.unpack_from("<QII", blob, pos)
        pos += 16
        total += raw
        if start != payload_end or not packed or start + packed > offset or not raw or total > MAX_BYTES:
            raise ValueError("invalid FPK block bounds")
        decoder = zlib.decompressobj()
        data = decoder.decompress(blob[start:start+packed], raw + 1)
        if len(data) != raw or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError("invalid FPK compressed block")
        if not data.endswith(b"\n"):
            raise ValueError("unterminated FPK record")
        group = data.decode("utf-8").split("\n")[:-1]
        if not group or group[0].split("|", 1)[0] != key:
            raise ValueError("FPK first-key mismatch")
        rows.extend(group)
        if len(rows) > count:
            raise ValueError("FPK record count exceeded")
        payload_end = start + packed
    if pos != len(blob) or payload_end != offset or len(rows) != count:
        raise ValueError("FPK index / record count mismatch")
    keys = [text(row.split("|", 1)[0]) for row in rows]
    if any(a >= b for a, b in zip(keys, keys[1:])):
        raise ValueError("unordered or duplicate FPK keys")
    return rows


def candidate(row):
    parts = row.split("|")
    if len(parts) != 3:
        raise ValueError("expected symbol|return spelling|parameter spelling")
    symbol, result, params = map(text, parts)
    parameters = []
    variadic = "unknown"
    form = "declared-empty" if params == "void" else "listed"
    if form == "listed":
        for item in params.split(","):
            if item == "...":
                if variadic != "unknown" or item != params.split(",")[-1]:
                    raise ValueError("invalid variadic marker")
                variadic = "explicit"
            else:
                pair = item.split(":")
                if len(pair) != 2:
                    raise ValueError("unsupported parameter grammar")
                parameters.append({"name": text(pair[0]), "type_spelling": text(pair[1])})
    return {"symbol": symbol, "return_spelling": result, "parameter_form": form,
            "variadic": variadic, "parameters": parameters}


def compile_library(document):
    if set(document) != {"schema", "kind", "type_resolution", "source", "candidates"}:
        raise ValueError("unknown or missing library fields")
    if type(document["schema"]) is not int or (document["schema"], document["kind"], document["type_resolution"]) != (1, "prototype-candidates", "unresolved"):
        raise ValueError("unsupported library schema / meaning")
    source = document["source"]
    if set(source) != {"path", "sha256", "commit", "grammar"} or source["grammar"] != "pipe-signatures-v1":
        raise ValueError("unsupported provenance")
    if len(source["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in source["sha256"]):
        raise ValueError("invalid source hash")
    if len(source["commit"]) != 40 or any(c not in "0123456789abcdef" for c in source["commit"]):
        raise ValueError("invalid source commit")
    entries = document["candidates"]
    if not isinstance(entries, list) or len(entries) > MAX_RECORDS:
        raise ValueError("invalid candidate count")
    out = bytearray(b"FSLD" + struct.pack("<HH", 1, 0))

    def string(value):
        value = text(value).encode()
        out.extend(struct.pack("<I", len(value)))
        out.extend(value)

    for name in ("path", "sha256", "commit", "grammar"):
        string(source[name])
    out.extend(struct.pack("<I", len(entries)))
    previous = ""
    for entry in entries:
        if set(entry) != {"symbol", "return_spelling", "parameter_form", "variadic", "parameters"}:
            raise ValueError("unknown or missing candidate fields")
        symbol = text(entry["symbol"])
        if symbol <= previous:
            raise ValueError("unordered or duplicate candidates")
        previous = symbol
        string(symbol)
        string(entry["return_spelling"])
        if entry["parameter_form"] not in ("declared-empty", "listed") or entry["variadic"] not in ("unknown", "explicit"):
            raise ValueError("unknown parameter form / variadic evidence")
        form = {"declared-empty": 0, "listed": 1}[entry["parameter_form"]]
        variadic = {"unknown": 0, "explicit": 1}[entry["variadic"]]
        params = entry["parameters"]
        if not isinstance(params, list) or len(params) > 1024 or (form == 0 and (params or variadic)) or (form == 1 and not params and not variadic):
            raise ValueError("invalid parameter list")
        out.extend(struct.pack("<BBI", form, variadic, len(params)))
        for param in params:
            if set(param) != {"name", "type_spelling"}:
                raise ValueError("unknown or missing parameter fields")
            string(param["name"])
            string(param["type_spelling"])
    if len(out) > MAX_BYTES:
        raise ValueError("library package too large")
    return bytes(out)


def source_text(document):
    # JSON string escaping is a compatible TOML basic-string encoder for the
    # admitted control-free strings. The file itself is TOML, not JSON.
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    lines = ['schema = 1', 'kind = "prototype-candidates"', 'type_resolution = "unresolved"', '', '[source]']
    if not document["candidates"]:
        lines.insert(3, 'candidates = []')
    lines += [f"{k} = {quote(v)}" for k, v in document["source"].items()]
    for item in document["candidates"]:
        lines += ['', '[[candidates]]']
        lines += [f"{k} = {quote(item[k])}" for k in ("symbol", "return_spelling", "parameter_form", "variadic")]
        params = ["{ name = " + quote(p["name"]) + ", type_spelling = " + quote(p["type_spelling"]) + " }" for p in item["parameters"]]
        lines.append("parameters = [" + ", ".join(params) + "]")
    return "\n".join(lines) + "\n"


def migrate(path, relative_path, commit=SNAPSHOT):
    blob = path.read_bytes()
    rows = fpk_rows(blob)
    document = {"schema": 1, "kind": "prototype-candidates", "type_resolution": "unresolved",
                "source": {"path": relative_path, "sha256": hashlib.sha256(blob).hexdigest(),
                           "commit": commit, "grammar": "pipe-signatures-v1"},
                "candidates": [candidate(row) for row in rows]}
    source = source_text(document)
    parsed = tomllib.loads(source)
    if parsed != document:
        raise ValueError("source round trip changed meaning")
    binary = compile_library(parsed)
    report = {"schema": 1, "source": document["source"], "records": len(rows),
              "parameters": sum(len(c["parameters"]) for c in document["candidates"]),
              "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
              "package_sha256": hashlib.sha256(binary).hexdigest(),
              "package_bytes": len(binary), "status": "candidate-metadata-only",
              "limits": ["unresolved type spellings", "symbol function identity unverified",
                         "missing variadic marker means unknown", "no ABI or execution semantics"]}
    return source, binary, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fission-root", type=pathlib.Path, default=pathlib.Path("Fission"))
    parser.add_argument("--source", default="utils/signatures/typeinfo/generic/generic_clib_64_signatures.fpk")
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("artifacts/library-migration"))
    parser.add_argument("--library-source", type=pathlib.Path, help="compile an owned .fslib directly; no legacy input required")
    args = parser.parse_args()
    if args.library_source:
        binary = compile_library(tomllib.loads(args.library_source.read_text()))
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "library.fsldb").write_bytes(binary)
        print(f"compiled owned library: {len(binary)} bytes")
        return
    source_path = args.fission_root / args.source
    check_pinned_source(args.fission_root, args.source)
    source, binary, report = migrate(source_path, args.source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "clib64.fslib").write_text(source)
    (args.output_dir / "clib64.fsldb").write_bytes(binary)
    (args.output_dir / "migration.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"migrated {report['records']} prototype candidates; unresolved types / no ABI inference")


if __name__ == "__main__":
    main()
