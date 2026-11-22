"""Explicitly disposable local integration support; contains no test cases."""
import importlib.util
import os
from pathlib import Path
import unittest
import psycopg
ROOT=Path(__file__).resolve().parents[1]
TABLES=['canonical_models','catalog_entries','providers','serving_endpoints']

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

class M3Case(unittest.TestCase):
    def setUp(self):
            self.assertIn('M3_TEST_DSN', os.environ, 'disposable DB must be explicit, never silently skip')
            self.conn = psycopg.connect(os.environ['M3_TEST_DSN'], autocommit=True)
            self.addCleanup(self.conn.close)
            self.assertTrue(self.conn.info.dbname.startswith('m3_'))
            self.assertTrue(self.conn.info.host.startswith('/home/hermes-worker/.hermes/cache/scratch/'))
            self.conn.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
            self.conn.execute((ROOT / 'db/schema.sql').read_text())

    def migrate(self):
            path = ROOT / 'db/milestone3.sql'
            self.assertTrue(path.exists(), 'Milestone 3 run logging migration is missing')
            self.conn.execute(path.read_text())

    def sync(self):
            path = ROOT / 'ingest/sync.py'
            self.assertTrue(path.exists(), 'transactional changed-only sync is missing')
            return module('ingest/sync.py','m3_sync')

    def cli(self, path, *args, env=None):
            import subprocess,sys
            values=dict(os.environ,DATABASE_URL=os.environ['M3_TEST_DSN'],APP_DATABASE_URL=os.environ['M3_APP_DSN'],OPENROUTER_API_KEY='')
            values.update(env or {})
            return subprocess.run([sys.executable,'-I','-B',str(ROOT/path),*args],env=values,cwd=ROOT,capture_output=True,text=True,timeout=20)
