"""Offline checks. No test uses an environment credential or reaches Supabase."""
from pathlib import Path
import hashlib
import sys
import unittest
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ingest'))


class ProductionContract(unittest.TestCase):
    def test_tls_and_identity_are_pinned_independently_of_dsn_options(self):
        import sync
        self.assertTrue(hasattr(sync, 'connection_parameters'))
        project = 'a' * 20
        # Generated test-only URI components; no persisted configuration or key.
        from secrets import token_urlsafe
        password = quote(token_urlsafe(12) + '@:', safe='')
        def uri(user, host, suffix=':5432/postgres'):
            return f'postgresql://{user}:{password}@{host}{suffix}'
        pool = 'aws-0-us-east-1.pooler.supabase.com'
        direct = 'db.' + project + '.supabase.co'
        for good in [uri('catalog_sync_writer', direct), uri('catalog_sync_writer.' + project, pool)]:
            cfg = sync.connection_parameters(good)
            self.assertEqual(cfg['sslmode'], 'verify-full')
            self.assertEqual(cfg['gssencmode'], 'disable')
            self.assertEqual(cfg['sslrootcert'], str(ROOT/'db'/'supabase-root-2021.crt'))
            self.assertEqual(hashlib.sha256(Path(cfg['sslrootcert']).read_bytes()).hexdigest(), '700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7')
        for bad in [uri('postgres', direct), uri('app_reader.' + project, pool),
                    uri('catalog_sync_writer', direct, ':6543/postgres'), uri('catalog_sync_writer', direct, ':5432/postgres?sslmode=disable'),
                    uri('catalog_sync_writer', direct + '.invalid'), uri('catalog_sync_writer','127.0.0.1'),
                    uri('catalog_sync_writer', direct, ':5432/other'), 'service=wrong', '',
                    uri('catalog_sync_writer', direct, ':5432/postgres?hostaddr=127.0.0.1')]:
            with self.assertRaises(ValueError):
                sync.connection_parameters(bad)

    def test_production_cli_has_no_fixture_or_source_selector(self):
        import subprocess
        proc = subprocess.run([sys.executable, '-I', '-B', str(ROOT/'ingest/sync.py'), '--help'],
                              capture_output=True, text=True, check=True)
        self.assertIn('--trigger', proc.stdout)
        self.assertNotIn('--local-fixture-url', proc.stdout)
        self.assertNotIn('--page-size', proc.stdout)

    def test_missing_or_wrong_identity_fails_without_echoing_configuration(self):
        import os
        import subprocess
        from secrets import token_urlsafe
        marker = token_urlsafe(18)
        for value in ['', 'postgresql://postgres:' + marker + '@127.0.0.1/postgres']:
            # Keep the interpreter's deployment library path, not ambient DB settings.
            env = {k: os.environ[k] for k in ('PATH','TMPDIR','LD_LIBRARY_PATH') if k in os.environ}
            proc = subprocess.run([sys.executable,'-I','-B',str(ROOT/'ingest/sync.py'),'--trigger','manual'],
                                  env=dict(env,DATABASE_URL=value),capture_output=True,text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertNotIn(marker, proc.stdout+proc.stderr)
            self.assertNotIn('Traceback', proc.stdout+proc.stderr)

    def test_source_detail_selector_rejects_query_traversal_and_confused_routes(self):
        import fetch
        client = fetch.Client(ROOT)
        prefix = '/api/v1/models/'
        for value in [prefix + 'org/model/endpoints', prefix + 'org/model.v2:free/endpoints']:
            self.assertEqual(client.checked_url(value), fetch.BASE_URL + value)
        for value in [prefix + 'org/%2e%2e/endpoints', prefix + 'org/%252f/endpoints',
                      prefix + 'org/model%2fother/endpoints', prefix + 'org/x\\y/endpoints',
                      prefix + 'org/x\n/endpoints', '//other.invalid/api/v1/models/o/m/endpoints',
                      '/api/v1/models?limit=2&offset=0&output_modalities=all']:
            with self.assertRaises(fetch.RetrievalError):
                client.checked_url(value)
