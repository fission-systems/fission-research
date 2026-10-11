import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from x86_stateful_validate import initial, expected
from x86_migrate import bodies, rules


class X86ImmediateTests(unittest.TestCase):
    def test_partial_store_oracle_keeps_neighbors_and_failure_keeps_all_state(self):
        row = initial(64, 3, 0x123456789ABCDEF0)
        before = bytes.fromhex(row["memory_hex"])
        store = dict(offset=8, bits=16, value=0x9876)
        state, memory = expected("imm16", 64, 3, 0x123456789ABCDEF0, row, store=store)
        self.assertEqual(state[1], 0x123456789ABCDEF3)
        self.assertEqual(memory[:152], before[:152])
        self.assertEqual(memory[152:154], b"\x76\x98")
        self.assertEqual(memory[154:], before[154:])
        failed, memory = expected("imm16", 64, 3, 0x123456789ABCDEF0, row, True, store)
        self.assertEqual(failed, [3, *row["registers"], *row["flags"], 99])
        self.assertEqual(memory, before)

    def test_extension_uses_existing_rules_and_preserves_historical_bodies(self):
        evidence = 'evidence "test" "https://example.com" "revision" "authored";'
        old = bodies(evidence, True, True)
        new = bodies(evidence, True, True, True)
        old_records = old.split("    instruction ")[1:]
        for record in old_records[:-1]:
            self.assertIn("    instruction " + record, new)
        self.assertEqual(new.count("field literal offset 86 bits 32;"), 9)
        self.assertEqual(
            rules(True).replace("owned-x86-v1", "owned-x86-v2"), rules(True, True)
        )


if __name__ == "__main__":
    unittest.main()
