import hashlib
import importlib.util
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('reproduce', pathlib.Path(__file__).resolve().parents[1] / 'tools/reproduce.py')
reproduce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reproduce)


class ReproductionTests(unittest.TestCase):
    def test_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'artifact'
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                reproduce.verify(path, hashlib.sha256(b'original').hexdigest())

    def test_missing_input_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with self.assertRaises(FileNotFoundError):
                reproduce.reproduce(root, {'inputs': [{'path': 'missing', 'sha256': '0'*64}], 'jobs': []}, root)

    def test_regeneration_and_stale_golden(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / 'probe.py').write_text('print("stable")')
            (root / 'golden').write_bytes(b'stable\n')
            work = root / 'work'
            work.mkdir()
            job = {'name': 'fixture', 'artifact': 'golden', 'sha256': hashlib.sha256(b'stable\n').hexdigest(),
                   'args': ['probe.py'], 'stdout': True}
            manifest = {'inputs': [], 'jobs': [job]}
            self.assertEqual(reproduce.reproduce(root, manifest, work)[0]['status'], 'identical')
            (root / 'probe.py').write_text('print("drift")')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                reproduce.reproduce(root, manifest, work)
            self.assertEqual((root / 'golden').read_bytes(), b'stable\n')
