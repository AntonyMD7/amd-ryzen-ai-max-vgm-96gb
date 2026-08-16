from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / ".github" / "actions" / "secret-exposure-scan"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


preflight = load_module("p049_preflight", ACTION / "preflight.py")
sanitizer = load_module("p049_sanitizer", ACTION / "sanitize_report.py")


class PreflightTests(unittest.TestCase):
    def test_stages_regular_files_without_git_history(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            workspace.mkdir()
            (workspace / "README.md").write_text("hello\n", encoding="utf-8")
            (workspace / ".git").mkdir()
            (workspace / ".git" / "private-history").write_text("not staged\n", encoding="utf-8")
            staging = Path(td) / "stage"
            result = preflight.stage_scope(workspace, ".", staging)
            self.assertEqual(result["file_count"], 1)
            self.assertFalse(result["git_history_scanned"])
            self.assertTrue((staging / "README.md").exists())
            self.assertFalse((staging / ".git").exists())

    def test_refuses_parent_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            workspace.mkdir()
            with self.assertRaises(preflight.PreflightError):
                preflight.stage_scope(workspace, "../outside", Path(td) / "stage")

    def test_refuses_root_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            outside = Path(td) / "outside"
            workspace.mkdir(); outside.mkdir()
            (outside / "x.txt").write_text("x", encoding="utf-8")
            (workspace / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(preflight.PreflightError):
                preflight.stage_scope(workspace, "link", Path(td) / "stage")

    def test_refuses_symlinked_file(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            workspace.mkdir()
            target = workspace / "real.txt"
            target.write_text("x", encoding="utf-8")
            (workspace / "alias.txt").symlink_to(target)
            with self.assertRaises(preflight.PreflightError):
                preflight.stage_scope(workspace, ".", Path(td) / "stage")

    def test_refuses_empty_scope(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            workspace.mkdir()
            with self.assertRaises(preflight.PreflightError):
                preflight.stage_scope(workspace, ".", Path(td) / "stage")


class SanitizerTests(unittest.TestCase):
    def _preflight(self):
        return {"file_count": 2, "total_bytes": 15, "scope_sha256": "a" * 64}

    def test_drops_secret_match_path_and_identity(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            raw.write_text(json.dumps([{
                "RuleID": "github-pat",
                "Secret": "TOP-SECRET-MUST-NOT-APPEAR",
                "Match": "token=TOP-SECRET-MUST-NOT-APPEAR",
                "File": "private/name.txt",
                "StartLine": 4,
                "EndLine": 4,
                "Author": "Person Name",
                "Email": "person@example.test",
            }]), encoding="utf-8")
            result = sanitizer.sanitize(raw, 1, "8.30.0", self._preflight())
            rendered = json.dumps(result)
            self.assertEqual(result["status"], "FINDINGS")
            self.assertEqual(result["finding_count"], 1)
            self.assertEqual(result["rule_ids"], ["github-pat"])
            for forbidden in (
                "TOP-SECRET-MUST-NOT-APPEAR", "private/name.txt", "Person Name", "person@example.test"
            ):
                self.assertNotIn(forbidden, rendered)
            self.assertFalse(result["privacy"]["secret_values_retained"])
            self.assertFalse(result["privacy"]["source_paths_retained"])

    def test_clean_exit_requires_zero_findings(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            raw.write_text("[]\n", encoding="utf-8")
            result = sanitizer.sanitize(raw, 0, "8.30.0", self._preflight())
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["finding_count"], 0)

    def test_code_one_without_findings_fails_honestly(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            raw.write_text("[]\n", encoding="utf-8")
            with self.assertRaises(sanitizer.ReportError):
                sanitizer.sanitize(raw, 1, "8.30.0", self._preflight())

    def test_nonstandard_exit_is_error_not_clean(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            raw.write_text("[]\n", encoding="utf-8")
            result = sanitizer.sanitize(raw, 2, "8.30.0", self._preflight())
            self.assertEqual(result["status"], "ERROR")


class ActionPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.action = (ACTION / "action.yml").read_text(encoding="utf-8")
        cls.config = (ACTION / "gitleaks.toml").read_text(encoding="utf-8")

    def test_pins_reviewed_gitleaks_asset_and_hash(self):
        self.assertIn("v8.30.0", self.action)
        self.assertIn("79a3ab579b53f71efd634f3aaf7e04a0fa0cf206b7ed434638d1547a2470a66e", self.action)
        self.assertNotIn("latest", self.action.lower())

    def test_uses_working_tree_dir_mode_not_git_history_mode(self):
        self.assertIn('"$TOOL" dir', self.action)
        self.assertNotIn('"$TOOL" git ', self.action)
        self.assertIn("git_history_scanned", (ACTION / "sanitize_report.py").read_text(encoding="utf-8"))

    def test_repository_bypasses_are_disabled(self):
        self.assertIn("--config \"$GITHUB_ACTION_PATH/gitleaks.toml\"", self.action)
        self.assertIn("--gitleaks-ignore-path \"$GITHUB_ACTION_PATH/.gitleaksignore\"", self.action)
        self.assertIn("--ignore-gitleaks-allow", self.action)
        self.assertIn("useDefault = true", self.config)

    def test_archive_decode_and_target_bounds_are_fixed(self):
        self.assertIn("--max-archive-depth=0", self.action)
        self.assertIn("--max-decode-depth=0", self.action)
        self.assertIn("--max-target-megabytes=10", self.action)

    def test_raw_diagnostics_are_never_printed(self):
        self.assertNotIn("cat \"$WORK/scan.stdout\"", self.action)
        self.assertNotIn("cat \"$WORK/scan.stderr\"", self.action)
        self.assertNotIn("cat \"$raw\"", self.action)
        self.assertIn("rm -f \"$raw\"", self.action)

    def test_runtime_canary_is_mandatory(self):
        self.assertIn("P049_DETECTION_CANARY=PASS", self.action)
        self.assertIn("P049_CLEAN_CANARY=PASS", self.action)
        self.assertIn("github-pat", self.action)

    def test_no_token_or_arbitrary_argument_input(self):
        input_block = self.action.split("outputs:", 1)[0]
        self.assertNotIn("token:", input_block.lower())
        self.assertNotIn("args:", input_block.lower())
        self.assertNotIn("config:", input_block.lower())


if __name__ == "__main__":
    unittest.main()
