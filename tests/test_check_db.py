"""Synthetic diagnostic/CLI regressions; never evidence of a Supabase connection."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_db.py"
PRIVATE = "synthetic-private-value-do-not-echo"


def clean_environment(**values):
    """Do not inherit credentials, libpq defaults, or dotenv settings."""
    return {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "TMPDIR": tempfile.gettempdir(),
        "LC_ALL": "C.UTF-8",
        **values,
    }


def load_script():
    spec = importlib.util.spec_from_file_location("check_db_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckDbTests(unittest.TestCase):
    def test_import_has_no_configuration_connection_or_output_side_effects(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        exit_code = None
        module = None
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("dotenv.load_dotenv") as dotenv,
            patch("psycopg.connect", side_effect=AssertionError("unexpected test connection")) as connect,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            try:
                module = load_script()
            except SystemExit as error:
                exit_code = error.code
        self.assertIsNone(exit_code, "import must not run the CLI or exit")
        dotenv.assert_not_called()
        connect.assert_not_called()
        self.assertEqual(stdout.getvalue() + stderr.getvalue(), "")
        assert module is not None
        self.assertTrue(callable(module.main))

    def test_project_dotenv_encoding_or_io_error_is_sanitized_before_connect(self):
        module = load_script()
        errors = (
            UnicodeDecodeError("utf-8", b"\xff", 0, 1, PRIVATE),
            PermissionError(PRIVATE),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                stdout, stderr = io.StringIO(), io.StringIO()
                with (
                    patch.dict(os.environ, {}, clear=True),
                    patch.object(module, "load_dotenv", side_effect=error) as dotenv,
                    patch.object(module.psycopg, "connect") as connect,
                    redirect_stdout(stdout), redirect_stderr(stderr),
                ):
                    status = module.main([])
                self.assertEqual(status, 1)
                dotenv.assert_called_once_with(SCRIPT.resolve().parents[1] / ".env")
                connect.assert_not_called()
                self.assertEqual(stderr.getvalue(), "")
                self.assertEqual(
                    stdout.getvalue(), "[FAIL] Could not read project .env configuration.\n"
                )
                self.assertNotIn(PRIVATE, stdout.getvalue())

    def test_interrupt_and_unexpected_errors_are_not_hidden(self):
        module = load_script()
        for stage in ("dotenv", "connect", "execute"):
            for error in (KeyboardInterrupt(), RuntimeError("synthetic implementation bug")):
                with self.subTest(stage=stage, error=type(error).__name__):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with (
                        patch.dict(os.environ, {"DATABASE_URL": PRIVATE}, clear=True),
                        patch.object(module, "load_dotenv") as dotenv,
                        patch.object(module.psycopg, "connect") as connect,
                        redirect_stdout(stdout), redirect_stderr(stderr),
                    ):
                        if stage == "dotenv":
                            dotenv.side_effect = error
                        elif stage == "connect":
                            connect.side_effect = error
                        else:
                            connection = connect.return_value.__enter__.return_value
                            connection.execute.side_effect = error
                        with self.assertRaises(type(error)):
                            module.main([])
                    self.assertEqual(stdout.getvalue() + stderr.getvalue(), "")

    def test_whitespace_configuration_is_rejected_before_connect(self):
        module = load_script()
        for argv, variable in (([], "DATABASE_URL"), (["--app"], "APP_DATABASE_URL")):
            with self.subTest(variable=variable):
                stdout, stderr = io.StringIO(), io.StringIO()
                with (
                    patch.dict(os.environ, {variable: " \t\r\n "}, clear=True),
                    patch.object(module, "load_dotenv"),
                    patch.object(module.psycopg, "connect") as connect,
                    redirect_stdout(stdout),
                    redirect_stderr(stderr),
                ):
                    connection = connect.return_value.__enter__.return_value
                    connection.execute.return_value.fetchone.return_value = (
                        "PostgreSQL synthetic, test fixture", "synthetic_user"
                    )
                    status = module.main(argv)
                self.assertEqual(status, 1)
                connect.assert_not_called()
                self.assertIn(f"{variable} is not set.", stdout.getvalue())
                self.assertEqual(stderr.getvalue(), "")

    def test_missing_project_dotenv_does_not_discover_parent_configuration(self):
        with tempfile.TemporaryDirectory(prefix="check-db-parent-") as directory:
            parent = Path(directory)
            project = parent / "project"
            scripts = project / "scripts"
            scripts.mkdir(parents=True)
            script = scripts / "check_db.py"
            script.write_bytes(SCRIPT.read_bytes())
            (parent / ".env").write_text(f"DATABASE_URL={PRIVATE}\n")
            environment = clean_environment()
            del environment["PYTHON_DOTENV_DISABLED"]
            guard = (
                "import runpy, sys; from unittest.mock import patch; "
                "guard = patch('psycopg.connect', "
                "side_effect=AssertionError('unexpected test connection')); "
                "guard.start(); runpy.run_path(sys.argv[1], run_name='__main__')"
            )
            result = subprocess.run(
                [sys.executable, "-B", "-c", guard, str(script)],
                cwd=project,
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
            )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1)
        self.assertIn("DATABASE_URL is not set.", output)
        self.assertNotIn(PRIVATE, output)
        self.assertNotIn("Traceback", output)

    def test_malformed_password_uri_cli_is_sanitized_for_owner_and_app(self):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict

        password = "SYNTHETIC_OWNER_PASSWORD_DO_NOT_LOG"
        uri = f"postgresql://synthetic_owner:{password}%ZZ@127.0.0.1:1/synthetic_db"
        self.assertIn(password, uri)
        # Real libpq rejects the password escape, not a refused connection.
        with self.assertRaises(psycopg.ProgrammingError) as error:
            conninfo_to_dict(uri)
        self.assertIn("invalid percent-encoded token", str(error.exception))
        self.assertIn(password, str(error.exception))
        guard = """
import runpy
import sys
from unittest.mock import patch
script, *args = sys.argv[1:]
sys.argv = [script, *args]
def forbid_network(event, arguments):
    if event.startswith('socket.'):
        raise AssertionError('unexpected test network operation')
sys.addaudithook(forbid_network)
with patch('socket.getaddrinfo',
           side_effect=AssertionError('unexpected hostname resolution')) as resolve, \\
     patch('psycopg.Connection._connect_gen',
           side_effect=AssertionError('unexpected libpq connection')) as connect:
    try:
        runpy.run_path(script, run_name='__main__')
    finally:
        resolve.assert_not_called()
        connect.assert_not_called()
"""
        for args, variable in (([], "DATABASE_URL"), (["--app"], "APP_DATABASE_URL")):
            with self.subTest(variable=variable):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", guard, str(SCRIPT), *args],
                    env=clean_environment(**{variable: uri}),
                    capture_output=True, text=True, timeout=10,
                )
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 1)
                self.assertNotIn(password, output)
                self.assertNotIn(uri, output)
                self.assertNotIn("Traceback", output)
                self.assertIn(f"[FAIL] Could not connect using {variable}.", output)
                self.assertNotIn("[ok]", output)
                self.assertEqual(result.stderr, "")
                self.assertEqual(
                    result.stdout,
                    f"[FAIL] Could not connect using {variable}.\n"
                    "       Check: Supabase Session pooler string? Correct password? Project paused?\n",
                )

    def test_invalid_idna_host_cli_is_sanitized_without_network(self):
        guard = """
import runpy
import sys
from unittest.mock import patch
script, *args = sys.argv[1:]
sys.argv = [script, *args]
def forbid_network(event, arguments):
    if event.startswith('socket.'):
        raise AssertionError('unexpected test network operation')
sys.addaudithook(forbid_network)
with patch('psycopg.Connection._connect_gen',
           side_effect=AssertionError('unexpected libpq connection')) as connect:
    try:
        runpy.run_path(script, run_name='__main__')
    finally:
        connect.assert_not_called()
"""
        dsn = f"host=. user=synthetic_user password={PRIVATE} dbname=synthetic_db"
        for args, variable in (([], "DATABASE_URL"), (["--app"], "APP_DATABASE_URL")):
            with self.subTest(variable=variable):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", guard, str(SCRIPT), *args],
                    env=clean_environment(**{variable: dsn}),
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stderr, "", result.stderr)
                self.assertEqual(
                    result.stdout,
                    f"[FAIL] Could not connect using {variable}.\n"
                    "       Check: Supabase Session pooler string? Correct password? Project paused?\n",
                )
                self.assertNotIn(PRIVATE, result.stdout + result.stderr)
                self.assertNotIn(dsn, result.stdout + result.stderr)

    def test_operational_error_cli_never_prints_driver_text(self):
        guard = """
import runpy
import sys
import psycopg
from unittest.mock import patch
script, message = sys.argv[1:]
sys.argv = [script]
with patch('psycopg.connect', side_effect=psycopg.OperationalError(message)):
    runpy.run_path(script, run_name='__main__')
"""
        for message in (PRIVATE + "\nsynthetic second diagnostic line", ""):
            with self.subTest(empty_message=not message):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", guard, str(SCRIPT), message],
                    env=clean_environment(DATABASE_URL=PRIVATE),
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stderr, "")
                self.assertEqual(
                    result.stdout,
                    "[FAIL] Could not connect using DATABASE_URL.\n"
                    "       Check: Supabase Session pooler string? Correct password? Project paused?\n",
                )

    def test_success_preserves_selected_dsn_timeout_query_and_display(self):
        module = load_script()
        environment = {
            "DATABASE_URL": " \thost=synthetic-owner.invalid password='test-only owner' \n",
            "APP_DATABASE_URL": " \thost=synthetic-app.invalid password='test-only app' \n",
        }
        cases = (
            ([], ["check_db.py", "--app"], "DATABASE_URL"),
            (["--app"], ["check_db.py"], "APP_DATABASE_URL"),
            (None, ["check_db.py", "--app"], "APP_DATABASE_URL"),
        )
        for argv, process_argv, variable in cases:
            with self.subTest(argv=argv, variable=variable):
                stdout, stderr = io.StringIO(), io.StringIO()
                with (
                    patch.dict(os.environ, environment, clear=True),
                    patch.object(sys, "argv", process_argv),
                    patch.object(module, "load_dotenv"),
                    patch.object(module.psycopg, "connect") as connect,
                    redirect_stdout(stdout), redirect_stderr(stderr),
                ):
                    connection = connect.return_value.__enter__.return_value
                    connection.execute.return_value.fetchone.return_value = (
                        "PostgreSQL synthetic version, synthetic build details", "synthetic_user"
                    )
                    status = module.main(argv)
                self.assertEqual(status, 0)
                connect.assert_called_once_with(environment[variable], connect_timeout=10)
                connection.execute.assert_called_once_with("select version(), current_user")
                connection.execute.return_value.fetchone.assert_called_once_with()
                connect.return_value.__exit__.assert_called_once_with(None, None, None)
                self.assertEqual(stderr.getvalue(), "")
                self.assertEqual(
                    stdout.getvalue(),
                    f"[ok] Connected using {variable}\n"
                    "     Database user: synthetic_user\n"
                    "     Server: PostgreSQL synthetic version\n",
                )

    def test_missing_or_empty_selected_configuration_never_uses_the_other_url(self):
        module = load_script()
        for argv, variable, other in (
            ([], "DATABASE_URL", "APP_DATABASE_URL"),
            (["--app"], "APP_DATABASE_URL", "DATABASE_URL"),
        ):
            for value in (None, ""):
                with self.subTest(variable=variable, value=value):
                    environment = {other: PRIVATE}
                    if value is not None:
                        environment[variable] = value
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with (
                        patch.dict(os.environ, environment, clear=True),
                        patch.object(module, "load_dotenv"),
                        patch.object(module.psycopg, "connect") as connect,
                        redirect_stdout(stdout), redirect_stderr(stderr),
                    ):
                        status = module.main(argv)
                    self.assertEqual(status, 1)
                    connect.assert_not_called()
                    self.assertEqual(stderr.getvalue(), "")
                    self.assertEqual(
                        stdout.getvalue(),
                        f"[FAIL] {variable} is not set. Add it to your .env file (see .env.example).\n",
                    )

    def test_query_and_context_driver_failures_are_sanitized(self):
        module = load_script()
        for stage in ("execute", "fetchone", "exit"):
            with self.subTest(stage=stage):
                stdout, stderr = io.StringIO(), io.StringIO()
                with (
                    patch.dict(os.environ, {"APP_DATABASE_URL": PRIVATE}, clear=True),
                    patch.object(module, "load_dotenv"),
                    patch.object(module.psycopg, "connect") as connect,
                    redirect_stdout(stdout), redirect_stderr(stderr),
                ):
                    connection = connect.return_value.__enter__.return_value
                    cursor = connection.execute.return_value
                    cursor.fetchone.return_value = ("PostgreSQL synthetic", "synthetic_user")
                    error = module.psycopg.ProgrammingError(PRIVATE + "\nsynthetic diagnostic")
                    if stage == "execute":
                        connection.execute.side_effect = error
                    elif stage == "fetchone":
                        cursor.fetchone.side_effect = error
                    else:
                        connect.return_value.__exit__.side_effect = error
                    status = module.main(["--app"])
                self.assertEqual(status, 1)
                self.assertEqual(stderr.getvalue(), "")
                self.assertEqual(
                    stdout.getvalue(),
                    "[FAIL] Could not connect using APP_DATABASE_URL.\n"
                    "       Check: Supabase Session pooler string? Correct password? Project paused?\n",
                )
                connect.return_value.__exit__.assert_called_once()

    def test_project_dotenv_cli_success_respects_environment_precedence(self):
        guard = """
import runpy
import sys
from unittest.mock import patch
script, expected, *args = sys.argv[1:]
sys.argv = [script, *args]
with patch('psycopg.connect') as connect:
    connection = connect.return_value.__enter__.return_value
    connection.execute.return_value.fetchone.return_value = (
        'PostgreSQL synthetic version, synthetic build', 'synthetic_user'
    )
    try:
        runpy.run_path(script, run_name='__main__')
    except SystemExit as error:
        status = error.code
    connect.assert_called_once_with(expected, connect_timeout=10)
    connection.execute.assert_called_once_with('select version(), current_user')
    sys.exit(status)
"""
        with tempfile.TemporaryDirectory(prefix="check-db-project-") as directory:
            parent = Path(directory)
            project = parent / "project"
            scripts = project / "scripts"
            scripts.mkdir(parents=True)
            script = scripts / "check_db.py"
            script.write_bytes(SCRIPT.read_bytes())
            file_values = {
                "DATABASE_URL": "synthetic-owner-from-project-file",
                "APP_DATABASE_URL": "synthetic-app-from-project-file",
            }
            (project / ".env").write_text(
                "".join(f"{key}={value}\n" for key, value in file_values.items())
            )
            (parent / ".env").write_text(f"DATABASE_URL={PRIVATE}\nAPP_DATABASE_URL={PRIVATE}\n")
            for args, variable in (([], "DATABASE_URL"), (["--app"], "APP_DATABASE_URL")):
                for override in (False, True):
                    with self.subTest(variable=variable, environment_override=override):
                        environment = clean_environment()
                        del environment["PYTHON_DOTENV_DISABLED"]
                        expected = file_values[variable]
                        if override:
                            expected = "synthetic-explicit-environment-configuration"
                            environment[variable] = expected
                        result = subprocess.run(
                            [sys.executable, "-B", "-c", guard, str(script), expected, *args],
                            cwd=parent, env=environment,
                            capture_output=True, text=True, timeout=10,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(result.stderr, "")
                        self.assertEqual(
                            result.stdout,
                            f"[ok] Connected using {variable}\n"
                            "     Database user: synthetic_user\n"
                            "     Server: PostgreSQL synthetic version\n",
                        )

    def test_invalid_dsn_cli_fails_without_private_value_or_traceback(self):
        # Real psycopg parsing rejects this before any connection is attempted.
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            env=clean_environment(DATABASE_URL=PRIVATE),
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(PRIVATE, output)
        self.assertNotIn("Traceback", output)
        self.assertIn("[FAIL] Could not connect using DATABASE_URL.", output)
        self.assertNotIn("[ok]", output)


if __name__ == "__main__":
    unittest.main()
