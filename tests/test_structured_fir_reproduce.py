import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from structured_fir_reproduce import reproduce


class StructuredReproductionTests(unittest.TestCase):
    def test_source_hash_mismatch_refuses_before_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "stack-branch-join.fsl").write_text("changed")
            with patch("structured_fir_reproduce.checked") as call:
                with self.assertRaises(ValueError):
                    reproduce(root / "fslc", root, root, {"source_sha256": "0"*64})
                call.assert_not_called()
