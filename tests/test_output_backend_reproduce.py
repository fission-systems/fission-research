import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from output_backend_reproduce import reproduce


class BackendReproductionTests(unittest.TestCase):
    def test_input_mismatch_refuses_before_compiler(self):
        with tempfile.TemporaryDirectory() as d:
            fixture = pathlib.Path(d)
            (fixture / "source.fsl").write_text("changed")
            (fixture / "source.lock.json").write_text(
                json.dumps({"inputs": {"source.fsl": "wrong"}})
            )
            with patch("output_backend_reproduce.FIXTURES", fixture), patch(
                "output_backend_reproduce.run"
            ) as compiler:
                with self.assertRaisesRegex(ValueError, "input hash mismatch"):
                    reproduce(pathlib.Path("missing-compiler"), ["cc"], ["rustc"], True)
                compiler.assert_not_called()

    def test_parent_lock_mismatch_refuses_before_compiler(self):
        with tempfile.TemporaryDirectory() as d:
            fixture = pathlib.Path(d) / "fixture"
            golden = pathlib.Path(d) / "golden"
            fixture.mkdir()
            golden.mkdir()
            (fixture / "source.lock.json").write_text(json.dumps({"inputs": {}}))
            (golden / "source.lock.json").write_text(
                json.dumps({"fixture_lock_sha256": "wrong"})
            )
            with patch("output_backend_reproduce.FIXTURES", fixture), patch(
                "output_backend_reproduce.GOLDEN", golden
            ), patch("output_backend_reproduce.run") as compiler:
                with self.assertRaisesRegex(ValueError, "fixture lock hash mismatch"):
                    reproduce(pathlib.Path("missing-compiler"), ["cc"], ["rustc"])
                compiler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
