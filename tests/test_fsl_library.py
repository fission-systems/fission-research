import hashlib
import pathlib
import struct
import sys
import unittest
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from fsl_library_migrate import candidate, compile_library, fpk_rows, source_text
import tomllib


def fixture(rows):
    raw = ("\n".join(rows) + "\n").encode()
    packed = zlib.compress(raw)
    key = rows[0].split("|")[0].encode()
    index = struct.pack("<I", len(key)) + key + struct.pack("<QII", 72, len(packed), len(raw))
    return (b"FPK1" + struct.pack("<HHQQQQ", 1, 1, len(rows), 1, 72+len(packed), len(index))
            + hashlib.sha256(packed).digest() + packed + index)


class LibraryTests(unittest.TestCase):
    def test_independent_fpk_reader(self):
        rows = ["alpha|int|void", "beta|void*|p:void*,n:size_t"]
        self.assertEqual(fpk_rows(fixture(rows)), rows)
        original = fixture(rows)
        for blob in [original[:71], original[:-1], original + b"x",
                     original[:6] + b"\x02\x00" + original[8:],
                     original[:40] + b"0" * 32 + original[72:],
                     fixture(list(reversed(rows))), fixture([rows[0], rows[0]])]:
            with self.assertRaises(ValueError):
                fpk_rows(blob)

    def test_candidates_do_not_infer_variadic_or_resolve_types(self):
        self.assertEqual(candidate("printf|int|format:char*")["variadic"], "unknown")
        self.assertEqual(candidate("printf|int|format:char*,...")["variadic"], "explicit")
        self.assertEqual(candidate("f|int|void")["parameter_form"], "declared-empty")
        for row in ["f|int", "f|int|void,x:int", "f|int|x", "f|int|...,x:int", "f|int|..."]:
            if row == "f|int|...":
                self.assertEqual(candidate(row)["parameters"], [])
            else:
                with self.assertRaises(ValueError):
                    candidate(row)

    def test_owned_text_and_binary_schema(self):
        doc = {"schema": 1, "kind": "prototype-candidates", "type_resolution": "unresolved",
               "source": {"path": "self-authored", "sha256": "0"*64, "commit": "0"*40,
                          "grammar": "pipe-signatures-v1"},
               "candidates": [candidate('alpha|int|void'), candidate('βeta|T*|p:T*')]}
        parsed = tomllib.loads(source_text(doc))
        self.assertEqual(parsed, doc)
        binary = compile_library(parsed)
        self.assertEqual(binary[:8], b"FSLD\x01\x00\x00\x00")
        for mutation in [dict(doc, kind="verified-functions"), dict(doc, schema=2),
                         dict(doc, extra=True), dict(doc, candidates=list(reversed(doc["candidates"]))),
                         dict(doc, candidates=[doc["candidates"][0]]*2)]:
            with self.assertRaises(ValueError):
                compile_library(mutation)


if __name__ == "__main__":
    unittest.main()
