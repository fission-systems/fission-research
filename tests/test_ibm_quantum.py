import base64
from collections import Counter
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ibm_quantum as q

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/quantum/ibm-open-plan"


def snapshot():
    return q.read_json(FIXTURE / "synthetic-snapshot.json")


def bit_array(rows, bits, descr="|u1", shape=None):
    width = (bits + 7) // 8
    header = repr(
        {"descr": descr, "fortran_order": False, "shape": shape or (len(rows), width)}
    ).encode()
    header += b" " * ((64 - (10 + len(header) + 1) % 64) % 64) + b"\n"
    raw = (
        b"\x93NUMPY\x01\x00"
        + struct.pack("<H", len(header))
        + header
        + b"".join(v.to_bytes(width, "big") for v in rows)
    )
    return {
        "__type__": "BitArray",
        "__value__": {
            "num_bits": bits,
            "array": {
                "__type__": "ndarray",
                "__value__": base64.b64encode(zlib.compress(raw)).decode(),
            },
        },
    }


def result(final, trace=None, bits=1, trace_bits=1):
    fields = {"out": bit_array(final, bits)}
    if trace is not None:
        fields["trace"] = bit_array(trace, trace_bits)
    return {
        "__type__": "PrimitiveResult",
        "__value__": {
            "pub_results": [
                {
                    "__type__": "SamplerPubResult",
                    "__value__": {
                        "data": {
                            "__type__": "DataBin",
                            "__value__": {
                                "field_names": list(fields),
                                "shape": [],
                                "fields": fields,
                            },
                        },
                        "metadata": {},
                    },
                }
            ],
            "metadata": {},
        },
    }


class AdapterContract(unittest.TestCase):
    def test_target_explicit_gate_support_and_no_fabricated_routing(self):
        self.assertEqual(q.target(snapshot(), [7, 3]), ("cz", [[7, 3], [3, 5], [7, 5]]))
        for mutate in [
            lambda s: s["catalog_plan"].update(name="paygo"),
            lambda s: s["configuration"].update(simulator=True),
            lambda s: s["status"].update(operational=False),
            lambda s: s["configuration"]["gates"][0].update(coupling_map=[[0]]),
            lambda s: s["configuration"]["gates"].append(
                s["configuration"]["gates"][0]
            ),
            lambda s: s["configuration"].update(supported_instructions=[]),
        ]:
            s = snapshot()
            mutate(s)
            with self.assertRaises(ValueError):
                q.target(s, [7, 3])
        for layout in ([7, 7], [8], [], [-1], [True]):
            with self.assertRaises(ValueError):
                q.target(snapshot(), layout)

    def test_single_job_payload_caps_and_runtime_cost_placement(self):
        p = q.payload("ibm_test", "OPENQASM 3.0;", 1024, 60)
        self.assertEqual(p["cost"], 60)
        self.assertNotIn("session_id", p)
        self.assertNotIn("max_execution_time", p["params"]["options"])
        self.assertEqual(p["params"]["options"]["default_shots"], 1024)
        for shots, seconds in [(0, 60), (4097, 60), (1024, 0), (1024, 61), (True, 60)]:
            with self.assertRaises(ValueError):
                q.payload("ibm_test", "", shots, seconds)

    def test_codec_preserves_shot_order_and_big_endian_byte_layout(self):
        rows = [0, 1, 256, 511]
        self.assertEqual(q.unpack_bits(bit_array(rows, 9), 9, 4), rows)
        m = {"trace_values": [0], "physical_qubits": [7], "shots": 4}
        self.assertEqual(
            q.counts_from_result(result([0, 1, 0, 1], [0, 1, 0, 1]), m),
            Counter({0: 2, 3: 2}),
        )
        with self.assertRaises(ValueError):
            q.unpack_bits(bit_array([512], 9), 9, 1)

    def test_codec_refuses_objects_parameterization_and_partial_results(self):
        for array in [
            bit_array([0], 1, descr="|O"),
            bit_array([0], 1, shape=(1, 1, 1)),
        ]:
            with self.assertRaises(ValueError):
                q.unpack_bits(array, 1, 1)
        array = bit_array([0], 1)
        raw = base64.b64decode(array["__value__"]["array"]["__value__"])
        array["__value__"]["array"]["__value__"] = base64.b64encode(
            raw + b"extra"
        ).decode()
        with self.assertRaises(ValueError):
            q.unpack_bits(array, 1, 1)
        m = {"trace_values": [], "physical_qubits": [7], "shots": 4}
        with self.assertRaises(ValueError):
            q.counts_from_result(result([0, 1]), m)
        bad = result([0] * 4)
        bad["__value__"]["pub_results"] *= 2
        with self.assertRaises(ValueError):
            q.counts_from_result(bad, m)

    def test_statistical_comparison_detects_wrong_joint_correlation(self):
        m = {"trace_values": [0], "physical_qubits": [7], "shots": 1024}
        report = q.compare_counts(Counter({0: 512, 3: 512}), {"0": 0.5, "3": 0.5}, m)
        self.assertEqual(report["status"], "compared")
        self.assertEqual(report["total_variation_distance"], 0)
        self.assertTrue(report["ideal_sampling_compatible"])
        wrong = q.compare_counts(Counter({1: 512, 2: 512}), {"0": 0.5, "3": 0.5}, m)
        self.assertEqual(wrong["total_variation_distance"], 1)
        self.assertFalse(wrong["ideal_sampling_compatible"])
        with self.assertRaises(ValueError):
            q.compare_counts(Counter({0: 1023}), {"0": 1.0}, m)

    def test_credentials_and_paid_plan_rejection_precede_any_device_request(self):
        calls = []

        def transport(method, url, headers, body=None):
            calls.append((method, url, headers, body))
            if url.endswith("/identity/token"):
                return {"access_token": "synthetic-bearer"}
            if url.endswith("/instance"):
                return {"plan_id": "paid-plan"}
            if url.endswith("/paid-plan"):
                return {"id": "paid-plan", "kind": "plan", "name": "paygo"}
            self.fail("paid account reached a device endpoint")

        with self.assertRaises(ValueError):
            q.Client("", "", transport)
        self.assertEqual(calls, [])
        client = q.Client(
            "synthetic-key",
            "crn:v1:bluemix:public:quantum-computing:us-east:a/test:instance::",
            transport,
        )
        with self.assertRaises(ValueError):
            client.snapshot("ibm_test")
        self.assertEqual(len(calls), 3)
        self.assertNotIn("Service-CRN", calls[-1][2])


@unittest.skipUnless(
    os.environ.get("FSLC"), "set FSLC for native projection integration"
)
class NativeAdapter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cli = Path(os.environ["FSLC"])
        self.package = self.root / "circuits.fslc"
        q.run(
            [
                self.cli,
                "compile",
                ROOT / "experiments/quantum/ideal-circuits/circuits.fsl",
                self.package,
            ]
        )
        self.bundle = self.root / "bundle"
        q.prepare(
            self.cli,
            self.package,
            "feedforward",
            snapshot(),
            [7],
            0,
            "Z",
            1024,
            60,
            self.bundle,
        )

    def live_bundle(self):
        # Explicit mocked provider evidence only. No network is used by this test.
        s = q.read_json(self.bundle / "snapshot.json")
        s["synthetic"] = False
        s["crn_sha256"] = q.digest(b"synthetic-crn")
        q.write_json(self.bundle / "snapshot.json", s)
        manifest = q.read_json(self.bundle / "manifest.json")
        manifest["files"]["snapshot.json"] = q.digest(
            (self.bundle / "snapshot.json").read_bytes()
        )
        q.write_json(self.bundle / "manifest.json", manifest)
        return s

    def test_offline_bundle_binds_request_and_reference_and_detects_tampering(self):
        m, s, p, expected = q.load_bundle(self.bundle)
        self.assertFalse(m["hardware_execution"])
        self.assertTrue(s["synthetic"])
        self.assertEqual(p["program_id"], "sampler")
        self.assertAlmostEqual(sum(expected.values()), 1)
        (self.bundle / "circuit.qasm").write_text("modified")
        with self.assertRaises(ValueError):
            q.load_bundle(self.bundle)

    def test_synthetic_snapshot_never_reaches_submission(self):
        class Fake:
            def snapshot(inner, backend):
                return snapshot()

            def call(inner, *args):
                self.fail("synthetic bundle reached POST")

        with self.assertRaises(ValueError):
            q.submit(Fake(), self.bundle, self.root / "receipt")

    def test_submission_is_one_post_and_collects_joint_results(self):
        s = self.live_bundle()
        posts = []

        class Fake:
            crn = "synthetic-crn"

            def snapshot(inner, backend):
                return s

            def call(inner, method, path, body=None):
                if method == "POST":
                    posts.append(body)
                    return {
                        "id": "synthetic-job",
                        "backend": s["configuration"]["backend_name"],
                    }
                if path.endswith("/results"):
                    return result([0] * 1024, [0] * 512 + [1] * 512, trace_bits=2)
                return {
                    "backend": s["configuration"]["backend_name"],
                    "state": {"status": "Completed"},
                    "id": "synthetic-job",
                }

        receipt = self.root / "receipt"
        q.submit(Fake(), self.bundle, receipt)
        self.assertEqual(len(posts), 1)
        # feedforward trace contains m then final measurement; only first can vary.
        output = self.root / "observed"
        self.assertTrue(q.collect(Fake(), self.bundle, receipt, output))
        report = q.read_json(output / "comparison.json")
        self.assertTrue(report["hardware_execution"])  # mock provider completion
        self.assertTrue(report["ideal_sampling_compatible"])

    def test_no_retry_on_uncertain_submission_and_no_second_post_to_same_receipt(self):
        s = self.live_bundle()
        posts = []

        class Fake:
            def snapshot(inner, backend):
                return s

            def call(inner, method, path, body=None):
                posts.append(path)
                raise ValueError("mock timeout")

        receipt = self.root / "receipt"
        with self.assertRaises(ValueError):
            q.submit(Fake(), self.bundle, receipt)
        self.assertEqual(
            q.read_json(receipt / "receipt.json")["state"], "submission_outcome_unknown"
        )
        with self.assertRaises(FileExistsError):
            q.submit(Fake(), self.bundle, receipt)
        self.assertEqual(posts, ["/jobs"])

    def test_allowance_and_changed_target_refuse_before_post(self):
        s = self.live_bundle()

        class Fake:
            def snapshot(inner, backend):
                return s

            def call(inner, *args):
                self.fail("failed preflight reached POST")

        s["usage"]["usage_consumed_seconds"] = 590
        with self.assertRaises(ValueError):
            q.submit(Fake(), self.bundle, self.root / "receipt")
        s["usage"]["usage_consumed_seconds"] = 0
        s["configuration"]["backend_version"] = "changed"
        with self.assertRaises(ValueError):
            q.submit(Fake(), self.bundle, self.root / "receipt")


class ArchivedEvidence(unittest.TestCase):
    def test_locked_inputs_and_clean_reports(self):
        lock = q.read_json(FIXTURE / "source.lock.json")
        for name, sha in lock["inputs"].items():
            self.assertEqual(q.digest((ROOT / name).read_bytes()), sha)
        for name, sha in lock["files"].items():
            self.assertEqual(q.digest((FIXTURE / name).read_bytes()), sha)
        for name in [
            "validation-local.json",
            "ideal-regression-local.json",
            "channels-regression-local.json",
            "execution-regression-local.json",
            "integer-regression-local.json",
        ]:
            report = q.read_json(FIXTURE / name)
            self.assertEqual(report["status"], "passed")
            self.assertFalse(report["compiler_dirty"])
            self.assertEqual(report["compiler_commit"], lock["compiler_commit"])
        report = q.read_json(FIXTURE / "validation-local.json")
        self.assertEqual(report["comparisons"], 684)
        self.assertEqual(report["codec_comparisons"], 684)
        self.assertFalse(report["hardware_execution"])
        self.assertEqual(report["network_requests"], 0)

    def test_review_example_is_synthetic_and_keeps_bell_x_correlation(self):
        root = FIXTURE / "example-bell-xx"
        manifest, snapshot, request, expected = q.load_bundle(root)
        self.assertTrue(snapshot["synthetic"])
        self.assertEqual(manifest["observation_axes"], "XX")
        self.assertEqual(request["backend"], "synthetic_ibm_cz")
        self.assertEqual(set(expected), {"0", "3"})
        result = q.read_json(root / "modeled-runtime-result.json")
        counts = q.counts_from_result(result, manifest)
        self.assertEqual(counts, Counter({0: 512, 3: 512}))
        self.assertFalse(
            q.read_json(root / "modeled-comparison.json")["hardware_execution"]
        )

    def test_linux_qualification_matches_local_pin_and_packages(self):
        for prefix in (
            "validation",
            "ideal-regression",
            "channels-regression",
            "execution-regression",
            "integer-regression",
        ):
            local = q.read_json(FIXTURE / (prefix + "-local.json"))
            linux = q.read_json(FIXTURE / (prefix + "-linux-39025890375.json"))
            for key in (
                "status",
                "compiler_commit",
                "validator_sha256",
                "package_sha256",
            ):
                self.assertEqual(local[key], linux[key])
            self.assertFalse(linux["compiler_dirty"])
        report = q.read_json(FIXTURE / "validation-linux-39025890375.json")
        self.assertFalse(report["hardware_execution"])
        self.assertEqual(report["network_requests"], 0)
        self.assertEqual(report["comparisons"], 684)
        self.assertEqual(report["codec_comparisons"], 684)
