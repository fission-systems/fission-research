import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import owned_pipeline_reproduce as owned


class OwnedPipelineTests(unittest.TestCase):
    def test_legacy_dependency_graph_refuses(self):
        owned.check_graph(["fission-fsl", "fission-loader", "fission-core"])
        for forbidden in owned.FORBIDDEN_CRATES:
            with self.assertRaisesRegex(ValueError, "legacy/decoder dependency"):
                owned.check_graph(["fission-fsl", forbidden])

    def test_failed_open_of_legacy_asset_is_also_a_violation(self):
        for extension in [
            "sla",
            "slaspec",
            "sinc",
            "cspec",
            "pspec",
            "ldefs",
            "opinion",
            "fpk",
            "fidb",
        ]:
            self.assertIsNotNone(
                owned.LEGACY.search(
                    f'openat(AT_FDCWD, "/missing/input.{extension}", O_RDONLY) = -1 ENOENT'
                )
            )
        self.assertIsNone(
            owned.LEGACY.search('openat(AT_FDCWD, "/out/profile.fslxc", O_WRONLY) = 3')
        )

    def test_input_hash_mismatch_refuses_before_running_binary(self):
        with patch.object(owned, "digest", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "fixture input hash mismatch"):
                owned.preflight()


if __name__ == "__main__":
    unittest.main()
