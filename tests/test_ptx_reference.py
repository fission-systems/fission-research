import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from ptx_reference import Program, PtxError


class PtxReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT/'experiments/gpu/fir-projections/jvm-iadd.ptx').read_text()
        cls.program = Program(cls.text)

    def test_wrap_preserves_unwritten_bytes_and_depth(self):
        slots = [99, 0xffffffffffffffff, 1, 0x8877665544332211]
        result = self.program.execute(slots, 3, 4)
        self.assertEqual(result['slots'], [99, 0, 1, slots[3]])
        self.assertEqual(result['depth'], 2)
        self.assertEqual(result['status'], 0)
        self.assertEqual([x for x in result['trace'] if x[0] == 'write'],
                         [('write', 0x1008, 8), ('write', 0x10000, 8), ('write', 0x20000, 4)])

    def test_failed_preflight_preserves_storage(self):
        for depth, capacity, status in [(1, 4, 1), (5, 4, 3), (2, 1, 3)]:
            slots = [11, 22, 33, 44]
            result = self.program.execute(slots, depth, capacity)
            self.assertEqual((result['slots'], result['depth'], result['status']), (slots, depth, status))
            self.assertEqual([x for x in result['trace'] if x[0] == 'write'], [('write', 0x20000, 4)])

    def test_nonowners_and_null_status_do_not_access_memory(self):
        for axis in range(6):
            coordinates = [0]*6
            coordinates[axis] = 1
            result = self.program.execute([1, 2], 2, 2, coordinates)
            self.assertEqual(result['trace'], [])
            self.assertEqual(result['status'], 0xeeeeeeee)
        self.assertEqual(self.program.execute([1, 2], 2, 2, null='status')['trace'], [])
        for missing in ['stack', 'depth']:
            result = self.program.execute([1, 2], 2, 2, null=missing)
            self.assertEqual(result['status'], 3)
            self.assertEqual(result['slots'], [1, 2])

    def test_unmodeled_syntax_and_bad_execution_refuse(self):
        mutations = [self.text.replace('.target sm_70', '.target sm_80'),
                     self.text.replace('add.u64 %v2', 'mul.lo.u64 %v2'),
                     self.text.replace('bra DONE', 'bra UNKNOWN'),
                     self.text.replace('DONE:', 'DONE:\nDONE:')]
        for text in mutations:
            with self.assertRaises(PtxError): Program(text)
        uninitialized = Program(self.text.replace('add.u64 %v2, %v1, %v0', 'add.u64 %v2, %uninitialized, %v0'))
        with self.assertRaises(PtxError): uninitialized.execute([1, 2], 2, 2)
        with self.assertRaises(PtxError): self.program.execute([1], 2, 2)
        with self.assertRaises(PtxError): self.program.execute([1, 2], 2, 2, coordinates=[0]*5)


if __name__ == '__main__': unittest.main()
