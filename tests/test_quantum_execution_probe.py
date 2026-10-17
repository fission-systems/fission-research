import json
import math
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import quantum_execution_probe as q


class QuantumExecution(unittest.TestCase):
    def test_time_units_and_explicit_rounding_bound(self):
        self.assertEqual(
            q.picoseconds(Decimal("1.0000005"), "us"), (1000000, "0.5000000")
        )
        for value, unit in [
            (Decimal("NaN"), "us"),
            (Decimal(-1), "us"),
            (Decimal(1), "unknown"),
            (Decimal(2) ** 64, "s"),
        ]:
            with self.assertRaises(ValueError):
                q.picoseconds(value, unit)

    def test_historical_snapshot_and_owned_source(self):
        props, rows = q.inventory()
        self.assertEqual(props["backend_name"], "ibmq_manila")
        self.assertTrue(props["last_update_date"].startswith("2024-05-27"))
        self.assertEqual(len(rows), 20)
        self.assertEqual((q.FIXTURE / "execution.fsl").read_text(), q.source())
        for row in rows:
            self.assertLessEqual(row["t2_ps"], 2 * row["t1_ps"])
            self.assertEqual(row["logical_model_slot"], 0)
            for residual in row["rounding_residual_ps"].values():
                self.assertLessEqual(abs(Decimal(residual)), Decimal("0.5"))

    def test_closed_form_relaxation_retains_entangled_partner(self):
        h = 1 / math.sqrt(2)
        rho = q.relaxation_density([h + 0j, 0j, 0j, 1j * h], 1, 2, 3)
        self.assertAlmostEqual(rho[3][3].real, 0.5 * math.exp(-0.5))
        self.assertAlmostEqual(rho[0][3].imag, -0.5 * math.exp(-1 / 3))
        self.assertAlmostEqual((rho[2][2] + rho[3][3]).real, 0.5)
        self.assertAlmostEqual(sum(rho[i][i].real for i in range(4)), 1)

    def test_archived_clean_reports_and_source_hashes(self):
        for root in [q.FIXTURE, q.ROOT / "experiments/quantum/eqasm-words"]:
            lock = json.loads((root / "source.lock.json").read_text())
            for name, key in lock.get("files", {}).items():
                self.assertEqual(q.common.digest(root / name), key)
            report = json.loads((root / "validation-local.json").read_text())
            self.assertFalse(report["compiler_dirty"])
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["compiler_commit"], lock["compiler_commit"])
            self.assertEqual(
                q.common.digest(root / "validation-local.json"), lock["report_sha256"]
            )


if __name__ == "__main__":
    unittest.main()
