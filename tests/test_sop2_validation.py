import importlib.util
import pathlib
import sys
import unittest

spec = importlib.util.spec_from_file_location('sop2', pathlib.Path(__file__).resolve().parents[1] / 'tools/gfx900_sop2_validate.py')
sop2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sop2)


class Sop2Tests(unittest.TestCase):
    def test_register_pair_widths(self):
        self.assertEqual(sop2.assembly('s_and_b64', [0, 2, 4]), 's_and_b64 s[0:1], s[2:3], s[4:5]')
        self.assertEqual(sop2.assembly('s_lshl_b64', [0, 2, 5]), 's_lshl_b64 s[0:1], s[2:3], s5')
        self.assertEqual(sop2.assembly('s_add_u32', [0, 2, 5]), 's_add_u32 s0, s2, s5')

    def test_expected_rejection_cannot_hide_tool_failure(self):
        sop2.run([sys.executable, '-c', 'raise SystemExit(1)'], accepted=False)
        with self.assertRaisesRegex(ValueError, 'unexpected exit'):
            sop2.run([sys.executable, '-c', 'raise SystemExit(2)'], accepted=False)
        with self.assertRaisesRegex(ValueError, 'unexpected exit'):
            sop2.run([sys.executable, '-c', 'pass'], accepted=False)
