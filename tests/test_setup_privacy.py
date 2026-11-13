"""Offline setup diagnostics using only disposable, synthetic project files."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_setup.py"
PRIVATE = "synthetic-private-value-do-not-echo"


class SetupPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="check-setup-synthetic-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        scripts = self.root / "scripts"
        scripts.mkdir()
        self.script = scripts / "check_setup.py"
        self.script.write_bytes(SCRIPT.read_bytes())
        (self.root / ".env").write_text("TEST_SECRET=synthetic-only\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(".env\n", encoding="utf-8")
        (self.root / ".env.example").write_text("TEST_SECRET=\n", encoding="utf-8")

    def run_setup(self, git_status=1, git_error=None, main=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        result = subprocess.CompletedProcess([], git_status, PRIVATE, PRIVATE)
        import_module = importlib.import_module

        def import_required(name, package=None):
            if name in ("requests", "psycopg", "dotenv", "streamlit", "anthropic", "openai"):
                return object()
            return import_module(name, package)

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("importlib.import_module", side_effect=import_required),
            patch("subprocess.run", return_value=result, side_effect=git_error) as git,
            redirect_stdout(stdout), redirect_stderr(stderr),
        ):
            try:
                if main is None:
                    runpy.run_path(str(self.script), run_name="__main__")
                    status = 0
                else:
                    status = main()
            except SystemExit as error:
                status = error.code
        git.assert_called_once_with(
            ["git", "ls-files", "--error-unmatch", ".env"],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn(PRIVATE, stdout.getvalue())
        return status, stdout.getvalue()

    def test_import_has_no_check_output_subprocess_or_exit_side_effects(self):
        spec = importlib.util.spec_from_file_location("check_setup_under_test", self.script)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        stdout, stderr = io.StringIO(), io.StringIO()
        exit_code = None
        with (
            patch.object(importlib, "import_module") as packages,
            patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 1)) as git,
            patch.object(Path, "exists", side_effect=AssertionError("unexpected import file check")) as exists,
            patch.object(Path, "read_text", side_effect=AssertionError("unexpected import file read")) as read,
            redirect_stdout(stdout), redirect_stderr(stderr),
        ):
            try:
                spec.loader.exec_module(module)
            except SystemExit as error:
                exit_code = error.code
        self.assertIsNone(exit_code, "import must not run the CLI or exit")
        packages.assert_not_called()
        git.assert_not_called()
        exists.assert_not_called()
        read.assert_not_called()
        self.assertEqual(stdout.getvalue() + stderr.getvalue(), "")
        self.assertTrue(callable(module.main))

    def test_repeated_main_calls_do_not_reuse_prior_failures(self):
        spec = importlib.util.spec_from_file_location("check_setup_repeat", self.script)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for git_status, expected_status in ((128, 1), (1, 0), (0, 1), (1, 0)):
            with self.subTest(git_status=git_status):
                status, output = self.run_setup(git_status=git_status, main=module.main)
                self.assertEqual(status, expected_status, output)

    def test_known_git_results_distinguish_tracked_from_untracked(self):
        for git_status, expected_status in ((0, 1), (1, 0)):
            with self.subTest(git_status=git_status):
                status, output = self.run_setup(git_status=git_status)
                self.assertEqual(status, expected_status)
                if git_status == 0:
                    self.assertIn("[FAIL] .env is tracked by Git", output)
                    self.assertIn("Setup NOT OK", output)
                    self.assertNotIn("Git is not tracking .env", output)
                else:
                    self.assertIn("[ok]   Git is not tracking .env", output)
                    self.assertIn("Setup OK", output)

    def test_missing_git_is_explicitly_skipped_not_nontracking_proof(self):
        status, output = self.run_setup(git_error=FileNotFoundError(PRIVATE))
        self.assertEqual(status, 0)
        self.assertIn("Git check was skipped", output)
        self.assertIn("[warn]", output)
        self.assertNotIn("Git is not tracking .env", output)

    def test_git_execution_or_decoding_errors_are_sanitized(self):
        errors = (
            PermissionError(PRIVATE),
            UnicodeDecodeError("utf-8", b"\xff", 0, 1, PRIVATE),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                status, output = self.run_setup(git_error=error)
                self.assertEqual(status, 1)
                self.assertIn("[FAIL] Could not verify whether Git is tracking .env", output)
                self.assertIn("Setup NOT OK", output)
                self.assertNotIn("Git is not tracking .env", output)
                self.assertNotIn("Traceback", output)

    def test_git_interrupt_and_unexpected_errors_are_not_hidden(self):
        for error in (KeyboardInterrupt(), RuntimeError("synthetic implementation bug")):
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(type(error)):
                    self.run_setup(git_error=error)

    def test_unexpected_git_exit_never_proves_env_is_untracked(self):
        for status in (128, 2, -9):
            with self.subTest(git_status=status):
                result, output = self.run_setup(git_status=status)
                self.assertEqual(result, 1, output)
                self.assertIn("[FAIL] Could not verify whether Git is tracking .env", output)
                self.assertIn("Setup NOT OK", output)
                self.assertNotIn("Git is not tracking .env", output)
                self.assertNotIn("Setup OK", output)


if __name__ == "__main__":
    unittest.main()
