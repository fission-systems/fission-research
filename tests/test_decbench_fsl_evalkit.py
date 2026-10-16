import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import decbench_fsl_evalkit as kit


class EvalKitTests(unittest.TestCase):
    def test_archived_baseline_provenance_and_ineligible_results(self):
        root = kit.ROOT / "experiments/decbench/sample-set"
        lock = json.loads((root / "source.lock.json").read_text())
        for name, sha in lock["artifacts"].items():
            self.assertEqual(kit.digest(root / name), sha)
        for name, sha in lock["tools"].items():
            self.assertEqual(kit.digest(kit.ROOT / name), sha)
        coverage = json.loads((root / "coverage.json").read_text())
        native = json.loads((root / "owned-pipeline-local.json").read_text())
        self.assertTrue(coverage["complete"])
        self.assertTrue(all(coverage["integrity"].values()))
        self.assertEqual(len(coverage["functions"]), 250)
        self.assertFalse(any(r["metric_eligible"] for r in coverage["functions"]))
        self.assertFalse(coverage["summary"]["submission_ready"])
        self.assertEqual(native["compiler_commit"], lock["compiler_commit"])
        self.assertFalse(native["compiler_dirty"])
        self.assertEqual(
            native["compiler_executable_sha256"],
            coverage["engine"]["executable_sha256"],
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.kit = self.root / "kit"
        (self.kit / "binaries").mkdir(parents=True)
        (self.kit / "binaries/bin_000.elf").write_bytes(b"never execute target")
        self.public = {"bin_000.elf": ["0x100"]}
        self.manifest()
        self.cli = Path(sys.executable)

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self):
        (self.kit / "functions.json").write_text(
            json.dumps(
                {
                    "kit_format_version": 1,
                    "public": self.public,
                    "private": {"ignored": "not a target selection or answer key"},
                }
            )
        )

    def test_only_public_selects_targets_and_private_is_not_in_report(self):
        metadata, selected = kit.targets(self.kit)
        self.assertEqual(metadata["target_count"], 1)
        self.assertEqual(selected[0][2], 0x100)
        self.assertNotIn("private", json.dumps(metadata))

    def test_bad_address_duplicate_and_traversal_refuse(self):
        for public in [
            {"../outside": ["0x100"]},
            {"bin_000.elf": ["0x100", "0x0100"]},
            {"bin_000.elf": ["0x10000000000000000"]},
            {"bin_000.elf": ["100"]},
            {"bin_000.elf": [256]},
            {"bin_000.elf": []},
        ]:
            self.public = public
            self.manifest()
            with self.assertRaises(ValueError):
                kit.targets(self.kit)

    def test_symlink_outside_binary_root_refuses(self):
        path = self.kit / "binaries/bin_000.elf"
        path.unlink()
        path.symlink_to(self.kit / "functions.json")
        with self.assertRaisesRegex(ValueError, "nonsymlink"):
            kit.targets(self.kit)

    def test_target_is_never_the_command_and_failure_is_checkpointed(self):
        output = self.root / "output"
        result = subprocess.CompletedProcess([], 1, b"", b"entry decode unsupported")
        with patch.object(kit.subprocess, "run", return_value=result) as invoke:
            report = kit.evaluate(self.kit, self.cli, output)
        command = invoke.call_args.args[0]
        self.assertEqual(command[0], str(self.cli.resolve()))
        self.assertEqual(command[1], "decompile-owned-entry")
        self.assertEqual(command[2], str((self.kit / "binaries/bin_000.elf").resolve()))
        self.assertTrue(report["complete"])
        self.assertEqual(
            report["summary"]["category_counts"], {"owned_decode_unsupported": 1}
        )
        self.assertFalse(report["summary"]["submission_ready"])
        self.assertEqual(report, json.loads((output / "report.json").read_text()))
        self.assertFalse((output / "results").exists())
        self.assertNotIn("ignored", json.dumps(report))

    def test_timeout_and_incomplete_bundle_are_not_success(self):
        with patch.object(
            kit.subprocess, "run", side_effect=subprocess.TimeoutExpired([], 1)
        ):
            report = kit.evaluate(self.kit, self.cli, self.root / "timeout")
        self.assertEqual(report["functions"][0]["status"], "timeout")
        with patch.object(
            kit.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0, b"", b""),
        ):
            report = kit.evaluate(self.kit, self.cli, self.root / "incomplete")
        self.assertEqual(report["functions"][0]["category"], "incomplete_bundle")
        with patch.object(kit.subprocess, "run", side_effect=OSError("invalid tool")):
            report = kit.evaluate(self.kit, self.cli, self.root / "tool-error")
        self.assertEqual(report["functions"][0]["category"], "tool_invocation_error")

    def test_changed_tool_invalidates_completion(self):
        tool = self.root / "trusted-tool"
        shutil.copy2(self.cli, tool)

        def changed(*args, **kwargs):
            tool.write_bytes(b"changed while evaluation was running")
            return subprocess.CompletedProcess([], 1, b"", b"entry decode unsupported")

        with patch.object(kit.subprocess, "run", side_effect=changed):
            report = kit.evaluate(self.kit, tool, self.root / "changed")
        self.assertFalse(report["complete"])
        self.assertFalse(report["integrity"]["tool_unchanged"])

    def test_overwrite_kit_tool_and_invalid_timeout_refuse_before_invocation(self):
        output = self.root / "exists"
        output.mkdir()
        for dest, cli, timeout in [
            (output, self.cli, 1),
            (self.kit / "out", self.cli, 1),
            (self.root / "new", self.kit / "binaries/bin_000.elf", 1),
            (self.root / "new", self.cli, float("nan")),
            (self.root / "new", self.cli, 0),
        ]:
            with patch.object(kit.subprocess, "run") as invoke:
                with self.assertRaises((ValueError, FileExistsError)):
                    kit.evaluate(self.kit, cli, dest, timeout)
                invoke.assert_not_called()

    @unittest.skipUnless(
        os.environ.get("FSL_X86"), "set FSL_X86 for native integration"
    )
    def test_real_owned_entry_projection_is_diagnostic_only(self):
        fixture_root = kit.ROOT / "experiments/x86/immediate"
        lock = json.loads((fixture_root / "source.lock.json").read_text())
        self.public = {}
        for index, fixture in enumerate(lock["fixtures"]):
            name = f"bin_{index:03}.elf"
            source = fixture_root / "fixtures" / (fixture["name"] + ".elf")
            self.assertEqual(
                kit.digest(source), lock["inputs"][f"fixtures/{source.name}"]
            )
            shutil.copyfile(source, self.kit / "binaries" / name)
            self.public[name] = ["0x401000"]
        self.manifest()
        report = kit.evaluate(
            self.kit, Path(os.environ["FSL_X86"]), self.root / "native"
        )
        self.assertEqual(
            report["summary"]["status_counts"], {"state_projection_only": 3}
        )
        self.assertEqual(report["summary"]["ordinary_c_functions_eligible"], 0)
        self.assertFalse((self.root / "native/results").exists())
        for row in report["functions"]:
            self.assertEqual(row["artifacts"]["profile.fslxc"], lock["package_sha256"])
            self.assertFalse(row["metric_eligible"])


if __name__ == "__main__":
    unittest.main()
