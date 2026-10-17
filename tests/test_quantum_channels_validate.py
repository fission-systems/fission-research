"""Independent oracle checks; no native executable required for these tests."""

import copy
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import quantum_channels_validate as q


class QuantumChannels(unittest.TestCase):
    def test_fixture_inventory(self):
        self.assertEqual(q.FIXTURE.read_text(), q.fixture_source())
        self.assertEqual(len(q.CASES), 33)

    def test_archived_evidence_hashes_and_clean_revision(self):
        lock = json.loads(q.LOCK.read_text())
        root = q.FIXTURE.parent
        for path, key in [
            (q.FIXTURE, "source_sha256"),
            (Path(q.__file__), "validator_sha256"),
            (Path(q.dense.__file__), "dense_oracle_sha256"),
            (root / "validation-local.json", "report_sha256"),
            (root / "ideal-regression-local.json", "ideal_regression_sha256"),
        ]:
            self.assertEqual(q.dense.digest(path), lock[key])
        report = json.loads((root / "validation-local.json").read_text())
        ideal = json.loads((root / "ideal-regression-local.json").read_text())
        for r in [report, ideal]:
            self.assertEqual(r["compiler_commit"], lock["compiler_commit"])
            self.assertFalse(r["compiler_dirty"])
            self.assertEqual(r["status"], "passed")
        self.assertEqual(report["comparisons"], 678)
        self.assertEqual(ideal["comparisons"], 308)
        self.assertEqual(report["package_sha256"], lock["package_sha256"])
        self.assertEqual(report["validator_sha256"], lock["validator_sha256"])

    def test_archived_linux_oracle_reports(self):
        lock = json.loads(q.LOCK.read_text())
        for name, key, count in [
            ("validation-linux-39019757014.json", "linux_report_sha256", 678),
            (
                "ideal-regression-linux-39019757014.json",
                "linux_ideal_regression_sha256",
                308,
            ),
        ]:
            path = q.FIXTURE.parent / name
            self.assertEqual(q.dense.digest(path), lock[key])
            report = json.loads(path.read_text())
            self.assertEqual(report["compiler_commit"], lock["compiler_commit"])
            self.assertFalse(report["compiler_dirty"])
            self.assertEqual(report["comparisons"], count)
            self.assertEqual(report["status"], "passed")
        report = json.loads(
            (q.FIXTURE.parent / "validation-linux-39019757014.json").read_text()
        )
        for key in ["package_sha256", "validator_sha256", "dense_oracle_sha256"]:
            self.assertEqual(report[key], lock[key])

    def test_amplitude_damping_keeps_entangled_partner(self):
        h = 1 / math.sqrt(2)
        rho = [
            [a * b.conjugate() for b in [h + 0j, 0j, 0j, h + 0j]]
            for a in [h + 0j, 0j, 0j, h + 0j]
        ]
        out = q.channel(2, ("amplitude_damping", 0, 0.25), rho)
        self.assertAlmostEqual(out[0][0].real, 0.5)
        self.assertAlmostEqual(out[2][2].real, 0.125)
        self.assertAlmostEqual(out[3][3].real, 0.375)
        self.assertAlmostEqual(out[0][3].real, math.sqrt(0.75) / 2)
        self.assertAlmostEqual(out[2][2].real + out[3][3].real, 0.5)

    def test_dephasing_is_not_measurement_or_coherent_phase_rotation(self):
        rho = [[0.5 + 0j, 0.5j], [-0.5j, 0.5 + 0j]]
        out = q.channel(1, ("phase_flip", 0, 0.5), rho)
        self.assertEqual(out[0][1], 0j)
        self.assertAlmostEqual(out[0][0].real, 0.5)
        observed = {
            "hardware_execution": False,
            "qubits": 1,
            "total_probability": 1,
            "density_matrix": [[0.5, 0], [0, 0], [0, 0], [0.5, 0]],
            "branches": [
                {
                    "probability": 0.5,
                    "amplitudes": [[1, 0], [0, 0]],
                    "values": [],
                    "measurements": [],
                },
                {
                    "probability": 0.5,
                    "amplitudes": [[0, 0], [1, 0]],
                    "values": [],
                    "measurements": [],
                },
            ],
        }
        expected = [((), (), out)]
        self.assertLess(q.compare(observed, expected, 1, 0), 1e-14)
        for field in ("values", "measurements"):
            bad = copy.deepcopy(observed)
            bad["branches"][0][field] = [0] if field == "values" else [[0, 0]]
            with self.assertRaises(ValueError):
                q.compare(bad, expected, 1, 0)
        bad = copy.deepcopy(observed)
        bad["density_matrix"][0][0] = float("nan")
        with self.assertRaises(ValueError):
            q.compare(bad, expected, 1, 0)
        # Same basis histogram, wrong coherence: must fail the density check.
        bad = copy.deepcopy(observed)
        bad["branches"] = [
            {
                "probability": 1,
                "amplitudes": [[1 / math.sqrt(2), 0], [1 / math.sqrt(2), 0]],
                "values": [],
                "measurements": [],
            }
        ]
        with self.assertRaises(ValueError):
            q.compare(bad, expected, 1, 0)

    def test_cfg_routes_classical_values_and_variable_measurement_history(self):
        qubits, count, _, ops = q.CASES["cfg_noise"]
        states = q.oracle(qubits, count, ops, [1 + 0j, 0j, 0j, 0j])
        lengths = {len(record) for record, _, _ in states}
        self.assertEqual(lengths, {2, 3})
        self.assertAlmostEqual(
            sum(sum(rho[i][i].real for i in range(4)) for _, _, rho in states), 1
        )
        for record, values, _ in states:
            self.assertEqual(values[5], values[0] ^ values[4])
            self.assertEqual(values[1] is not None, values[0] == 1)
            self.assertEqual(values[3] is not None, values[0] == 0)


if __name__ == "__main__":
    unittest.main()
