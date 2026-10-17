from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import eqasm_binary_probe as q


class EqasmWords(unittest.TestCase):
    def test_reference_corpus_coverage_and_masks(self):
        rows = q.corpus()
        self.assertEqual(len(rows), 200)
        self.assertEqual(len([r for r in rows if r[0].startswith("QWAIT ")]), 128)
        for _, fields, word in rows:
            if "cycles" in fields:
                self.assertEqual(word & 0xFFFFF, fields["cycles"])
            if "source" in fields:
                self.assertEqual((word >> 15) & 31, fields["source"])
            if "slot0" in fields:
                self.assertEqual(word & 7, fields["separator"])
                self.assertEqual((word >> 3) & 0x3FFF, fields["slot0"])
                self.assertEqual((word >> 17) & 0x3FFF, fields["slot1"])

    def test_unpinned_reference_refuses_before_building(self):
        with patch.object(q.common, "run", return_value=b"bad-revision") as invoke:
            with self.assertRaisesRegex(ValueError, "frozen revision"):
                q.build(Path("absent"), Path("unused"), "bison", "flex", "c++")
            self.assertEqual(invoke.call_count, 1)


if __name__ == "__main__":
    unittest.main()
