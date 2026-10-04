import hashlib
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from sequence_fir_reproduce import reproduce, verify_envelope


class SequenceReproductionTests(unittest.TestCase):
    def envelope(self):
        package, raw = b"compiled-package", b"raw-window"
        data = (b"FSLSEQ\0\x01" + struct.pack("<QIIII", 0x1000, 7, 2, len(package), len(raw))
                + hashlib.sha256(package).digest() + hashlib.sha256(raw).digest() + package + raw)
        return data, package, raw

    def test_independent_origin_contract(self):
        data, package, raw = self.envelope()
        verify_envelope(data, package, raw, 0x1000, 7, 2)
        with self.assertRaises(ValueError):
            verify_envelope(data, package, raw, 0x1004, 7, 2)
        with self.assertRaises(ValueError):
            verify_envelope(data, package, raw, 0x1000, 6, 2)

    def test_corrupt_hash_window_and_trailing_bytes_refuse(self):
        data, package, raw = self.envelope()
        for index in [0, 7, 24, 32, 64, len(data)-1]:
            bad = bytearray(data)
            bad[index] ^= 0xff
            with self.assertRaises(ValueError):
                verify_envelope(bad, package, raw, 0x1000, 7, 2)
        with self.assertRaises(ValueError):
            verify_envelope(data+b"trailing", package, raw, 0x1000, 7, 2)

    def test_source_mismatch_refuses_before_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "fixture.fsl").write_bytes(b"changed")
            lock = {"fixtures": [{"name": "scalar-chain", "source": "fixture.fsl", "source_sha256": "0"*64}]}
            with patch("sequence_fir_reproduce.checked") as call:
                with self.assertRaisesRegex(ValueError, "source hash"):
                    reproduce(root/"fslc", root, root, lock)
                call.assert_not_called()
