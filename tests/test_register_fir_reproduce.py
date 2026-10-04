import hashlib
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from register_fir_reproduce import reproduce


class RegisterReproductionTests(unittest.TestCase):
    def test_source_hash_mismatch_refuses_before_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "register-branch-convert.fsl").write_text("changed")
            with patch("register_fir_reproduce.checked") as call:
                with self.assertRaisesRegex(ValueError, "source hash"):
                    reproduce(root / "fslc", root, root, {"source_sha256": "0"*64})
                call.assert_not_called()

    def test_package_hash_mismatch_refuses_before_emission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "register-branch-convert.fsl").write_bytes(b"source")
            (root / "register-branch-convert.fslc").write_bytes(b"changed")
            lock = {"source_sha256": hashlib.sha256(b"source").hexdigest(), "package_sha256": "0"*64}
            with patch("register_fir_reproduce.checked") as call:
                with self.assertRaisesRegex(ValueError, "package hash"):
                    reproduce(root / "fslc", root, root, lock)
                self.assertEqual(call.call_count, 1)
                self.assertEqual(call.call_args.args[1], "compile")
