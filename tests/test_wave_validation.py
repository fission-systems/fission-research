import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from gfx900_wave_validate import check_hashes


class WaveLockTest(unittest.TestCase):
    def test_every_pinned_hash_is_required(self):
        lock = {key: key for key in ["source_sha256", "package_sha256", "corpus_sha256"]}
        check_hashes(dict(lock), lock)
        for key in lock:
            bad = dict(lock)
            bad[key] = "changed"
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_hashes(bad, lock)


if __name__ == "__main__":
    unittest.main()
