import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from register_layout_migrate import MigrationError, layout_source

PREFIX = '''define space ram type=ram_space size=4 default;
define space register type=register_space size=4;
define register offset=0 size=4 [ A X ];
define register offset=0 size=2 [ AH _ XH _ ];
define register offset=0 size=1 [ AB _ _ _ XB _ _ _ ];
define token instr(64) field=(0,7);'''


class RegisterLayoutMigrationTest(unittest.TestCase):
    def migrate(self, prefix=PREFIX, entry='define endian=little; @include "BPF.sinc"'):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            folder = root / "utils/sleigh-specs/languages/BPF"
            folder.mkdir(parents=True)
            (folder / "BPF.sinc").write_text(prefix)
            (folder / "BPF_le.slaspec").write_text(entry)
            return layout_source(root, "BPF")

    def test_holes_byte_offsets_and_aliases_are_retained(self):
        text, record = self.migrate()
        self.assertEqual([(r["name"], r["offset"], r["size_bytes"]) for r in record["registers"]],
                         [("A",0,4),("X",4,4),("AH",0,2),("XH",4,2),("AB",0,1),("XB",4,1)])
        self.assertEqual(len(record["overlapping_pairs"]), 6)
        self.assertIn('register "XH" "register" 4 2;', text)
        self.assertIn('default_space "ram";', text)
        self.assertIn('space "register" register 4 byte little;', text)

    def test_unsupported_declarations_and_entry_shapes_are_refused(self):
        for prefix in [
            PREFIX.replace('size=4 default', 'size=4 wordsize=2 default'),
            PREFIX.replace('size=4 [ A X ]', 'size=4 [ A A ]'),
            PREFIX.replace('size=4 [ A X ]', 'size=0 [ A X ]'),
            PREFIX.replace('define token', '@if OTHER\ndefine token'),
            PREFIX.replace('offset=0 size=4', 'offset=4294967295 size=4'),
            PREFIX + ' define register offset=8 size=4 [ EXTRA ];',
            PREFIX.replace(' type=ram_space size=4 default', ' type=ram_space size=4'),
        ]:
            with self.subTest(prefix=prefix), self.assertRaises(MigrationError):
                self.migrate(prefix)
        with self.assertRaises(MigrationError):
            self.migrate(entry='define endian=big; @include "BPF.sinc"')
        with self.assertRaises(MigrationError):
            self.migrate(entry='define endian=little; @include "BPF.sinc" @include "other.sinc"')


if __name__ == "__main__":
    unittest.main()
