import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import quantum_integer_probe as q


class QuantumInteger(unittest.TestCase):
    def test_fixture_matches_inventory_and_lock(self):
        self.assertEqual((q.FIXTURE / "circuits.fsl").read_text(), q.source())
        self.assertEqual(len(q.CASES), 42)
        lock = json.loads((q.FIXTURE / "source.lock.json").read_text())
        for name, digest in lock["files"].items():
            self.assertEqual(q.dense.digest(q.FIXTURE / name), digest)
        self.assertEqual(q.dense.digest(Path(q.__file__)), lock["validator_sha256"])
        self.assertEqual(
            q.dense.digest(Path(q.dense.__file__)), lock["dense_oracle_sha256"]
        )

    def test_signed_u64_patterns_and_zero_iteration_slots(self):
        vector = [1 + 0j, 0j, 0j, 0j]
        _, values, _ = q.oracle(q.CASES["arithmetic_u64_0"], vector)[0]
        self.assertEqual(values[:4], (2**64 - 1, 1, 0, 2**64 - 2))
        _, values, _ = q.oracle(q.CASES["conversion_i_128"], vector)[0]
        self.assertEqual(values[1], 2**64 - 128)
        _, values, _ = q.oracle(q.CASES["counter_u64_0"], vector)[0]
        self.assertEqual(values[4:7], (None, None, None))

    def test_two_entry_cycle_preserves_trace_and_coherent_phase(self):
        # On an eigenstate the four alternating X/Z effects yield a global
        # phase; density stays unchanged, while final SSA distinguishes entries.
        for basis in (0, 1):
            vector = [complex(i == basis) for i in range(4)]
            record, values, rho = q.oracle(q.CASES["two_entry_cycle"], vector)[0]
            self.assertEqual(record, ((0, basis),))
            self.assertEqual(values[2], 1 if basis else 0)
            self.assertEqual(values[7], 0 if basis else 1)
            self.assertEqual(rho[basis][basis], 1)

    def test_comparator_refuses_integer_or_state_corruption(self):
        vector = [1 + 0j, 0j, 0j, 0j]
        case = q.CASES["arithmetic_u64_0"]
        expected = q.oracle(case, vector)
        observed = {
            "hardware_execution": False,
            "qubits": 2,
            "branches": [
                {
                    "probability": 1.0,
                    "values": list(expected[0][1]),
                    "measurements": [],
                    "amplitudes": [[v.real, v.imag] for v in vector],
                }
            ],
            "density_matrix": [[v.real, v.imag] for row in expected[0][2] for v in row],
            "total_probability": 1.0,
        }
        self.assertEqual(q.compare(observed, expected, case[3]), 0.0)
        for field, value in (
            ("values", [255] + list(expected[0][1][1:])),
            ("amplitudes", [[float("nan"), 0], [0, 0], [0, 0], [0, 0]]),
            ("measurements", [[0, 1]]),
        ):
            bad = copy.deepcopy(observed)
            bad["branches"][0][field] = value
            with self.assertRaises(ValueError):
                q.compare(bad, expected, case[3])

    def test_clean_archived_reports_share_the_native_pin(self):
        lock = json.loads((q.FIXTURE / "source.lock.json").read_text())
        for name in (
            "validation-local.json",
            "ideal-regression-local.json",
            "channels-regression-local.json",
            "execution-regression-local.json",
        ):
            report = json.loads((q.FIXTURE / name).read_text())
            self.assertEqual(report["status"], "passed")
            self.assertFalse(report["compiler_dirty"])
            self.assertEqual(report["compiler_commit"], lock["compiler_commit"])
        report = json.loads((q.FIXTURE / "validation-local.json").read_text())
        self.assertEqual(report["comparisons"], 1344)
        self.assertEqual(report["package_sha256"], lock["package_sha256"])
        self.assertEqual(report["validator_sha256"], lock["validator_sha256"])

    def test_linux_reports_reproduce_local_packages_and_instruments(self):
        lock = json.loads((q.FIXTURE / "source.lock.json").read_text())
        for prefix in (
            "validation",
            "ideal-regression",
            "channels-regression",
            "execution-regression",
        ):
            local = json.loads((q.FIXTURE / (prefix + "-local.json")).read_text())
            linux = json.loads(
                (q.FIXTURE / (prefix + "-linux-39024432407.json")).read_text()
            )
            for key in (
                "status",
                "compiler_commit",
                "validator_sha256",
                "package_sha256",
            ):
                self.assertEqual(linux[key], local[key])
            self.assertFalse(linux["compiler_dirty"])
            self.assertEqual(linux["compiler_commit"], lock["compiler_commit"])
        report = json.loads(
            (q.FIXTURE / "validation-linux-39024432407.json").read_text()
        )
        self.assertEqual(report["comparisons"], 1344)
        self.assertEqual(report["inputs"], 882)
        self.assertEqual(report["projection_refusals"], 42)
        self.assertEqual(report["partial_checks"], 1)
