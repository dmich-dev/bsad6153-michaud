"""Synthetic loader runtime regressions; never cloud/catalog observation evidence."""
import copy
from typing import Any
import json
import os
from pathlib import Path
import tempfile
import unittest
import test_database as base_tests


class CountRequests:
    """Count explicitly synchronous connection.execute requests, not SQL rows."""
    def __init__(self, connection):
        self.connection = connection
        self.requests = 0
    def execute(self, *args, **kwargs):
        self.requests += 1
        return self.connection.execute(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(self.connection, name)


@unittest.skipUnless(base_tests.psycopg and os.environ.get('MILESTONE2_TEST_DSN'),
                     'explicit disposable PostgreSQL required')
class LoaderRuntimeTests(unittest.TestCase):
    conn: Any
    schema: str
    setUp = base_tests.PostgreSQLTests.setUp
    tearDown = base_tests.PostgreSQLTests.tearDown
    fixture = base_tests.PostgreSQLTests.fixture
    loader = base_tests.PostgreSQLTests.loader

    def large_fixture(self, folder):
        sample = self.fixture(folder)
        model = sample['models'][0]
        models = []
        for n in range(500):
            row = copy.deepcopy(model)
            row['id'] = f'synthetic/model-{n:04d}'
            row['canonical_slug'] = f'synthetic/canonical-{n:04d}'
            models.append(row)
        endpoints = copy.deepcopy(sample['endpoints'])
        for row in endpoints:
            row['model_id'] = models[0]['id']
        (folder / 'models.json').write_text(json.dumps({'data': models}))
        (folder / 'endpoints.json').write_text(json.dumps({'data': endpoints}))
        summary = json.loads((folder / 'summary.json').read_text())
        summary.update(unique_catalog_ids=500, unique_canonical_slugs=500)
        (folder / 'summary.json').write_text(json.dumps(summary))

    def test_large_load_has_bounded_synchronous_requests_not_per_record_lookups(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.large_fixture(folder)
            proxy = CountRequests(self.conn)
            result = self.loader().load_run(proxy, folder)
        self.assertEqual(result['counts']['catalog_entries'], 500)
        self.assertLessEqual(proxy.requests, 12,
                             'WAN replay must not synchronously request INSERT + ID SELECT for every source row')

    def test_progress_reports_real_stages_before_final_success(self):
        import inspect
        loader = self.loader()
        self.assertIn('progress', inspect.signature(loader.load_run).parameters,
                      'quiet cloud loads need flushed phase progress, not an apparently hung terminal')
        events = []
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            result = loader.load_run(self.conn, folder, minimum_models=1, progress=events.append)
        self.assertIn('Validating', events[0])
        for name in base_tests.TABLES:
            self.assertTrue(any(name in e for e in events), name)
        self.assertIn('Checking', events[-1])
        self.assertFalse(any('committed' in e.lower() or 'success' in e.lower() for e in events),
                         'phase callbacks must not announce a commit before the transaction exits')
        self.assertEqual(result['counts'], dict(zip(base_tests.TABLES, [1, 1, 2, 3])))

    def test_load_limits_server_waits_locally_without_changing_session_defaults(self):
        observed = []
        def check_limits(message):
            if message.startswith('Loading canonical_models'):
                values = dict(self.conn.execute(
                    "SELECT name, setting::int FROM pg_settings WHERE name IN ('statement_timeout', 'lock_timeout')").fetchall())
                observed.append(values)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            self.loader().load_run(self.conn, folder, minimum_models=1, progress=check_limits)
        self.assertEqual(len(observed), 1)
        self.assertGreater(observed[0]['statement_timeout'], 0,
                           'cloud statements need a finite timeout, not an unlimited quiet wait')
        self.assertLessEqual(observed[0]['statement_timeout'], 30000)
        self.assertGreater(observed[0]['lock_timeout'], 0)
        self.assertLessEqual(observed[0]['lock_timeout'], 5000)
        defaults = dict(self.conn.execute(
            "SELECT name, setting::int FROM pg_settings WHERE name IN ('statement_timeout', 'lock_timeout')").fetchall())
        self.assertEqual(defaults, {'statement_timeout': 0, 'lock_timeout': 0})




    def test_cli_interrupt_is_safe_nonzero_without_claiming_rollback_or_success(self):
        from contextlib import redirect_stdout, redirect_stderr
        from unittest.mock import patch
        import io
        loader = self.loader()
        output = io.StringIO()
        status = None
        with patch.dict(os.environ, {'DATABASE_URL': 'synthetic-interrupt-configuration'}, clear=True), \
             patch.object(loader, 'load_dotenv'), \
             patch.object(loader.psycopg, 'connect'), \
             patch.object(loader, 'load_run', side_effect=KeyboardInterrupt), \
             redirect_stdout(output), redirect_stderr(output):
            try:
                status = loader.main(['--run-dir', 'synthetic-unused-folder'])
            except KeyboardInterrupt:
                pass
        self.assertEqual(status, 130, 'Ctrl+C must be a clean interrupted result, not an unhandled traceback')
        self.assertIn('interrupted', output.getvalue().lower())
        self.assertNotIn('Traceback', output.getvalue())
        self.assertNotIn('synthetic-interrupt-configuration', output.getvalue())
        self.assertNotIn('rolled back', output.getvalue().lower(),
                         'an interrupt can arrive after commit; do not fabricate a rollback')
        self.assertNotIn('success', output.getvalue().lower())

    def test_interrupt_after_parent_batch_rolls_back_real_database_transaction(self):
        def interrupt(message):
            if message.startswith('Loading catalog_entries'):
                raise KeyboardInterrupt
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            with self.assertRaises(KeyboardInterrupt):
                self.loader().load_run(self.conn, folder, minimum_models=1, progress=interrupt)
        for table in base_tests.TABLES:
            query = base_tests.sql.SQL('SELECT count(*) FROM {}').format(base_tests.sql.Identifier(table))
            self.assertEqual(self.conn.execute(query).fetchone()[0], 0)
        self.assertEqual(self.conn.execute('SELECT 1').fetchone()[0], 1)

    def test_real_lock_wait_times_out_and_leaves_no_partial_data(self):
        import time
        locker = base_tests.psycopg.connect(os.environ['MILESTONE2_TEST_DSN'])
        try:
            locker.execute(base_tests.sql.SQL('LOCK TABLE {}.canonical_models IN ACCESS EXCLUSIVE MODE').format(
                base_tests.sql.Identifier(self.schema)))
            started = time.monotonic()
            with tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                self.fixture(folder)
                with self.assertRaises(base_tests.psycopg.errors.LockNotAvailable):
                    self.loader().load_run(self.conn, folder, minimum_models=1)
            self.assertLess(time.monotonic() - started, 15, 'a blocked demo must not wait indefinitely')
        finally:
            locker.rollback()
            locker.close()
        for table in base_tests.TABLES:
            query = base_tests.sql.SQL('SELECT count(*) FROM {}').format(base_tests.sql.Identifier(table))
            self.assertEqual(self.conn.execute(query).fetchone()[0], 0)
