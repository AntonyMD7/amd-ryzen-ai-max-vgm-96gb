from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / ".github/actions/broken-link-scan/preflight.py"
ACTION = ROOT / ".github/actions/broken-link-scan/action.yml"
SANITIZER = ROOT / ".github/actions/broken-link-scan/sanitize_report.py"


class P048PreflightTests(unittest.TestCase):
    def run_preflight(self, text: str, *, root_name: str = "docs") -> tuple[subprocess.CompletedProcess[str], str]:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            temp = Path(td) / "runner"
            root = workspace / root_name
            root.mkdir(parents=True)
            temp.mkdir()
            (root / "README.md").write_text(text, encoding="utf-8")
            output = Path(td) / "output"
            env = os.environ.copy()
            env.update({"GITHUB_WORKSPACE": str(workspace), "RUNNER_TEMP": str(temp), "GITHUB_OUTPUT": str(output)})
            cp = subprocess.run([sys.executable, str(PREFLIGHT), root_name], env=env, text=True, capture_output=True)
            return cp, output.read_text(encoding="utf-8") if output.exists() else ""

    def test_accepts_public_https_and_local_relative_link(self) -> None:
        cp, output = self.run_preflight("[upstream](https://github.com/lycheeverse/lychee)\n[local](./guide.md)\n")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("document_count=1", output)
        self.assertIn("absolute_url_count=1", output)

    def test_rejects_loopback_cloud_metadata_and_rfc1918(self) -> None:
        for url in (
            "http://127.0.0.1:8080/admin",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.0.8/private",
            "http://[::1]/",
        ):
            with self.subTest(url=url):
                cp, _ = self.run_preflight(f"[x]({url})\n")
                self.assertEqual(cp.returncode, 2)
                self.assertIn("forbidden", cp.stderr.lower())

    def test_rejects_embedded_credentials_and_non_http_scheme(self) -> None:
        for url in ("https://user:password@example.org/path", "ftp://example.org/file"):
            with self.subTest(url=url):
                cp, _ = self.run_preflight(f"{url}\n")
                self.assertEqual(cp.returncode, 2)

    def test_rejects_single_label_and_private_suffix_hosts(self) -> None:
        for url in ("http://printer/status", "http://service.local/", "https://api.internal/v1"):
            with self.subTest(url=url):
                cp, _ = self.run_preflight(url + "\n")
                self.assertEqual(cp.returncode, 2)

    def test_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            temp = Path(td) / "runner"
            workspace.mkdir()
            temp.mkdir()
            env = os.environ.copy()
            env.update({"GITHUB_WORKSPACE": str(workspace), "RUNNER_TEMP": str(temp)})
            cp = subprocess.run([sys.executable, str(PREFLIGHT), "../"], env=env, text=True, capture_output=True)
            self.assertEqual(cp.returncode, 2)

    def test_action_has_fixed_supply_chain_and_ssrf_guards(self) -> None:
        text = ACTION.read_text(encoding="utf-8")
        self.assertIn("github-hosted", text)
        self.assertIn("--exclude-all-private", text)
        self.assertIn("lychee-v${version}", text)
        self.assertIn("1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a", text)
        self.assertNotIn("github.token", text)
        self.assertNotIn("inputs.args", text)
        self.assertNotIn("--insecure", text)
        self.assertNotIn("--preprocess", text)

    def test_sanitizer_retains_hashes_not_urls(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            err = Path(td) / "err"
            out = Path(td) / "result.json"
            raw.write_text('{"url":"https://example.org/?token=secret"}\n', encoding="utf-8")
            err.write_text("https://user:pass@example.org/failed\n", encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, str(SANITIZER), str(raw), str(err), "2", "1", "99", "1", str(out)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(cp.returncode, 0, cp.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            serialized = json.dumps(data)
            self.assertEqual(data["status"], "FAIL")
            self.assertFalse(data["raw_report_retained"])
            self.assertFalse(data["full_urls_retained"])
            self.assertNotIn("example.org", serialized)
            self.assertNotIn("secret", serialized)
            self.assertEqual(len(data["raw_report_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
