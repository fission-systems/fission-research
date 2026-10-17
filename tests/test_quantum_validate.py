import copy
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import quantum_validate as q


class QuantumReferenceTests(unittest.TestCase):
    def test_archived_artifacts_and_source_provenance(self):
        root = q.FIXTURE.parent
        lock = json.loads(q.LOCK.read_text())
        report = json.loads((root / "validation-local.json").read_text())
        self.assertEqual(q.digest(q.FIXTURE), lock["source_sha256"])
        self.assertEqual(
            q.digest(q.ROOT / "tools/quantum_validate.py"), lock["validator_sha256"]
        )
        self.assertEqual(
            q.digest(root / "validation-local.json"), lock["report_sha256"]
        )
        self.assertEqual(
            q.digest(root / "outputs/bell-basis0.json"), lock["sample_sha256"]
        )
        self.assertEqual(
            q.digest(root / "x86-regression-local.json"), lock["x86_regression_sha256"]
        )
        for name, sha in lock["qasm_sha256"].items():
            self.assertEqual(q.digest(root / "outputs" / (name + ".qasm")), sha)
        self.assertEqual(report["compiler_commit"], lock["compiler_commit"])
        self.assertFalse(report["compiler_dirty"])
        self.assertEqual(report["comparisons"], 308)

    def test_fixture_hash_mismatch_refuses_before_native_execution(self):
        with patch.object(q, "digest", return_value="wrong"), patch.object(
            q, "run"
        ) as invoke:
            with self.assertRaisesRegex(ValueError, "fixture hash mismatch"):
                q.validate(Path("/not-run"))
            invoke.assert_not_called()

    def test_complex_interference_identity(self):
        initial = [1 / math.sqrt(2), 1j / math.sqrt(2)]
        result = q.oracle(1, [("h", 0), ("z", 0), ("h", 0)], initial)[()]
        expected = [
            [a * complex(b).conjugate() for b in reversed(initial)]
            for a in reversed(initial)
        ]
        self.assertLess(
            max(abs(a - b) for ra, rb in zip(result, expected) for a, b in zip(ra, rb)),
            1e-14,
        )

    def test_reset_preserves_partner_mixture(self):
        result = q.oracle(
            2, [("h", 0), ("cx", 0, 1), ("reset", 0)], [1 + 0j, 0j, 0j, 0j]
        )[()]
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(
                    result[i][j].real, 0.5 if i == j and i in [0, 2] else 0
                )
                self.assertAlmostEqual(result[i][j].imag, 0)

    def test_same_histogram_does_not_hide_lost_coherence(self):
        expected = q.oracle(2, [("h", 0), ("cx", 0, 1)], [1 + 0j, 0j, 0j, 0j])
        fake = {
            "total_probability": 1,
            "qubits": 2,
            "branches": [
                {
                    "probability": 0.5,
                    "amplitudes": [[1, 0], [0, 0], [0, 0], [0, 0]],
                    "values": [],
                    "measurements": [],
                },
                {
                    "probability": 0.5,
                    "amplitudes": [[0, 0], [0, 0], [0, 0], [1, 0]],
                    "values": [],
                    "measurements": [],
                },
            ],
            "density_matrix": [[0.5 if i in [0, 15] else 0, 0] for i in range(16)],
        }
        with self.assertRaisesRegex(ValueError, "channel mismatch"):
            q.compare(fake, expected, 4)

    def test_nonfinite_and_wrong_shape_never_pass_comparison(self):
        valid = {
            "total_probability": 1,
            "qubits": 1,
            "branches": [
                {
                    "probability": 1,
                    "amplitudes": [[1, 0], [0, 0]],
                    "values": [],
                    "measurements": [],
                }
            ],
            "density_matrix": [[1, 0], [0, 0], [0, 0], [0, 0]],
        }
        expected = q.oracle(1, [("x", 0), ("x", 0)], [1 + 0j, 0j])
        q.compare(valid, expected, 2)
        bad = copy.deepcopy(valid)
        bad["branches"][0]["amplitudes"][0][0] = float("nan")
        with self.assertRaises(ValueError):
            q.compare(bad, expected, 2)
        bad = copy.deepcopy(valid)
        bad["density_matrix"].pop()
        with self.assertRaises(ValueError):
            q.compare(bad, expected, 2)


if __name__ == "__main__":
    unittest.main()
