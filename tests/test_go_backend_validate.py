import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go_backend_validate as go


class GoBackendValidationTests(unittest.TestCase):
    def test_input_hash_mismatch_refuses_before_compiler(self):
        with patch.object(go, "digest", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "Go input hash mismatch"):
                go.preflight(
                    dict(inputs={"jvm-se26-iadd.fsl": "pinned"}, parent_locks={})
                )

    def test_parent_lock_mismatch_refuses(self):
        with patch.object(go, "digest", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "parent fixture lock mismatch"):
                go.preflight(dict(inputs={}, parent_locks={"stateful": "pinned"}))

    def test_widened_carry_oracle_and_alias_rows(self):
        rows = go.domain_vectors("carry", 64)
        valid = [r for r in rows if r["Status"] == 0]
        self.assertTrue(any(r["WantF"][0] == 1 for r in valid))
        self.assertEqual({r["Fields"][2] for r in valid}, {0, 1, 2})
        for r in valid:
            wide = r["R"][0] + r["R"][1] + r["F"][0]
            self.assertEqual(r["WantF"][0], int(wide > 0xFFFFFFFFFFFFFFFF))
            self.assertEqual(r["WantR"][r["Fields"][2]], wide & 0xFFFFFFFFFFFFFFFF)

    def test_wave_inactive_lanes_preserve_full_bitpatterns(self):
        rows = go.domain_vectors("wave-sgpr")
        for r in rows:
            if r["Status"] != 0:
                continue
            dst = r["Fields"][2]
            for lane in range(64):
                if not r["Exec"] & (1 << lane):
                    self.assertEqual(
                        r["Lane"][dst * 64 + lane], r["WantLane"][dst * 64 + lane]
                    )


if __name__ == "__main__":
    unittest.main()
