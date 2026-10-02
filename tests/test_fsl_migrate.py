import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from fsl_migrate import MigrationError, cspec_source

# Synthetic XML tests refusal and units without depending on a local clone.
SOURCE = '''<compiler_spec><data_organization><pointer_size value="8"/>
<size_alignment_map><entry size="8" alignment="8"/></size_alignment_map></data_organization>
<global><range space="ram"/></global><stackpointer register="SP" space="ram"/>
<default_proto><prototype name="c" extrapop="unknown" stackshift="8">
<input><pentry minsize="1" maxsize="8"><register name="A0"/></pentry></input>
<output killedbycall="true"><pentry minsize="1" maxsize="8"><register name="RET"/></pentry></output>
<unaffected><register name="SP"/><varnode space="ram" offset="0x10" size="8"/></unaffected>
</prototype></default_proto></compiler_spec>'''


class CspecMigrationTest(unittest.TestCase):
    def convert(self, source):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / "fixture.cspec"
            path.write_text(source)
            return cspec_source(path, root, "test.compiler")

    def test_order_units_and_unknown_cleanup_are_retained(self):
        text, record = self.convert(SOURCE)
        for expected in ['data pointer_size 8;', 'alignment 8 8;', 'extrapop unknown;',
                         'input_register "A0" 1 8;', 'output_register "RET" 1 8;',
                         'preserved_memory "ram" 16 8;', 'output_killed_by_call true;']:
            self.assertIn(expected, text)
        self.assertEqual(record["unsupported_nodes"], 0)

    def test_unmodeled_features_cannot_be_dropped(self):
        for source in [
            SOURCE.replace('<input>', '<input pointermax="8">'),
            SOURCE.replace('<register name="A0"/>', '<addr space="join" piece1="A0" piece2="A1"/>'),
            SOURCE.replace('</input>', '<rule><datatype name="struct"/><hidden_return/></rule></input>'),
            SOURCE.replace('<pointer_size value="8"/>', '<pointer_size value="8"/><pointer_size value="4"/>'),
            SOURCE.replace('minsize="1"', 'minsize="9"'),
            SOURCE.replace('<global>', '<global><register name="STATUS"/>'),
            SOURCE.replace('killedbycall="true"', 'killedbycall="maybe"'),
        ]:
            with self.subTest(source=source), self.assertRaises(MigrationError):
                self.convert(source)


if __name__ == "__main__":
    unittest.main()
