"""Opt-in real PostgreSQL tests; synthetic fixtures are never catalog evidence.

MILESTONE2_TEST_DSN must refer to an expendable local database. Tests create/drop
only their own unique schema. Ordinary discovery skips these without that variable.
"""
from datetime import datetime, timezone
from decimal import Decimal
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
import uuid

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None

ROOT = Path(__file__).resolve().parents[1]
TABLES = ['canonical_models', 'catalog_entries', 'providers', 'serving_endpoints']


@unittest.skipUnless(psycopg and os.environ.get('MILESTONE2_TEST_DSN'), 'explicit disposable PostgreSQL required')
class PostgreSQLTests(unittest.TestCase):
    def setUp(self):
        self.conn = psycopg.connect(os.environ['MILESTONE2_TEST_DSN'], autocommit=True)
        self.schema = 'test_m2_' + uuid.uuid4().hex
        self.conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(self.schema)))
        self.conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
        self.conn.execute((ROOT / 'db/schema.sql').read_text())

    def tearDown(self):
        self.conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(self.schema)))
        self.conn.close()

    def test_schema_encodes_four_real_entities_with_audits_keys_and_relationships(self):
        tables = self.conn.execute('SELECT table_name FROM information_schema.tables WHERE table_schema=%s', (self.schema,)).fetchall()
        self.assertEqual(sorted(t[0] for t in tables), sorted(TABLES))
        for table in TABLES:
            columns = self.conn.execute('SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema=%s AND table_name=%s', (self.schema, table)).fetchall()
            for audit in ['first_seen_at', 'last_updated_at']:
                self.assertIn((audit, 'timestamp with time zone', 'NO'), columns)
            kinds = self.conn.execute('SELECT constraint_type FROM information_schema.table_constraints WHERE table_schema=%s AND table_name=%s', (self.schema, table)).fetchall()
            self.assertIn(('PRIMARY KEY',), kinds)
            self.assertIn(('UNIQUE',), kinds)
        relationships = self.conn.execute("SELECT count(*) FROM information_schema.table_constraints WHERE table_schema=%s AND constraint_type='FOREIGN KEY'", (self.schema,)).fetchone()[0]
        self.assertEqual(relationships, 3)

    def loader(self):
        path = ROOT / 'ingest/load.py'
        self.assertTrue(path.exists(), 'parameterized transactional loader is not implemented')
        spec = importlib.util.spec_from_file_location('milestone2_loader', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, folder):
        # Real historical linked sample, used ONLY as a small test fixture.
        sample = json.loads((ROOT / 'data/sample/openrouter_sample.json').read_text())
        (folder / 'models.json').write_text(json.dumps({'data': sample['models']}))
        (folder / 'endpoints.json').write_text(json.dumps({'data': sample['endpoints']}))
        (folder / 'summary.json').write_text(json.dumps({
            'complete': True, 'catalog_finished': True, 'source': 'https://openrouter.ai',
            'finished_at': sample['observed_at'], 'unique_catalog_ids': 1,
            'unique_canonical_slugs': 1, 'related_endpoints': 3, 'issues': []}))
        return sample

    def test_load_transforms_sample_exactly_and_satisfies_parent_first_foreign_keys(self):
        loader = self.loader()
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sample = self.fixture(folder)
            result = loader.load_run(self.conn, folder, minimum_models=1)
        self.assertEqual(result['counts'], dict(zip(TABLES, [1, 1, 2, 3])))
        row = self.conn.execute('SELECT c.catalog_id, m.canonical_slug, c.prompt_usd_per_token, c.context_length, c.catalog_created_at, c.raw_payload, c.pricing, c.source_observed_at FROM catalog_entries c JOIN canonical_models m USING(canonical_model_id)').fetchone()
        self.assertEqual(row[0:4], ('openai/gpt-4.1', 'openai/gpt-4.1-2025-04-14', Decimal('0.000002'), 1047576))
        self.assertEqual(row[4], datetime.fromtimestamp(sample['models'][0]['created'], timezone.utc))
        self.assertEqual(row[5], sample['models'][0])
        self.assertEqual(row[6], sample['models'][0]['pricing'])
        # November 1 falls in a DST fold in the server's America/Chicago zone.
        # Compare instants in UTC rather than cross-zone ambiguous-wall-time equality.
        self.assertEqual(row[7].astimezone(timezone.utc), datetime.fromisoformat(sample['observed_at']))
        self.assertEqual(self.conn.execute('SELECT count(*) FROM serving_endpoints e JOIN catalog_entries c USING(catalog_entry_id) JOIN providers p USING(provider_id)').fetchone()[0], 3)

    def test_replaying_a_complete_run_preserves_rows_audits_and_null_tier_identity(self):
        loader = self.loader()
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            first = loader.load_run(self.conn, folder, minimum_models=1)
            before = [self.conn.execute(sql.SQL('SELECT * FROM {} ORDER BY 1').format(sql.Identifier(t))).fetchall() for t in TABLES]
            try:
                second = loader.load_run(self.conn, folder, minimum_models=1)
            except psycopg.errors.UniqueViolation:
                self.fail('second load must not raise uniqueness errors or duplicate nullable-tier endpoints')
            after = [self.conn.execute(sql.SQL('SELECT * FROM {} ORDER BY 1').format(sql.Identifier(t))).fetchall() for t in TABLES]
        self.assertEqual(first['counts'], second['counts'])
        self.assertEqual(before, after)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM serving_endpoints WHERE service_tier IS NULL').fetchone()[0], 3)

    def test_database_failure_rolls_back_all_parents_and_earlier_children(self):
        loader = self.loader()
        self.conn.execute("""CREATE FUNCTION reject_test_endpoint() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN IF NEW.tag='azure/swedencentral' THEN RAISE EXCEPTION 'intentional test failure'; END IF; RETURN NEW; END $$""")
        self.conn.execute('CREATE TRIGGER reject_test_endpoint BEFORE INSERT ON serving_endpoints FOR EACH ROW EXECUTE FUNCTION reject_test_endpoint()')
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            with self.assertRaises(psycopg.errors.RaiseException):
                loader.load_run(self.conn, folder, minimum_models=1)
        counts = [self.conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(t))).fetchone()[0] for t in TABLES]
        self.assertEqual(counts, [0, 0, 0, 0], 'a late failure must not leave partial data')
        self.assertEqual(self.conn.execute('SELECT 1').fetchone(), (1,))

    def test_incomplete_insufficient_conflicting_or_orphan_input_is_rejected_before_writes(self):
        loader = self.loader()
        self.assertTrue(hasattr(loader, 'LoadError'), 'source validation must expose safe LoadError')
        for case in ['incomplete', 'too_few', 'count_mismatch', 'orphan', 'duplicate_conflict', 'bad_id', 'naive_time']:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                sample = self.fixture(folder)
                summary = json.loads((folder / 'summary.json').read_text())
                minimum = 1
                if case == 'incomplete':
                    summary['complete'] = False
                elif case == 'too_few':
                    minimum = 500
                elif case == 'count_mismatch':
                    summary['unique_catalog_ids'] = 999
                elif case == 'orphan':
                    sample['endpoints'][0]['model_id'] = 'unknown/no-parent'
                elif case == 'duplicate_conflict':
                    sample['models'].append(dict(sample['models'][0], name='conflicting test-only label'))
                elif case == 'bad_id':
                    sample['models'][0]['id'] = ' openai/gpt-4.1'
                elif case == 'naive_time':
                    summary['finished_at'] = '2026-11-01T12:00:00'
                (folder / 'models.json').write_text(json.dumps({'data': sample['models']}))
                (folder / 'endpoints.json').write_text(json.dumps({'data': sample['endpoints']}))
                (folder / 'summary.json').write_text(json.dumps(summary))
                with self.assertRaises(loader.LoadError):
                    loader.load_run(self.conn, folder, minimum_models=minimum)
                self.assertEqual([self.conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(t))).fetchone()[0] for t in TABLES], [0, 0, 0, 0])

    def test_unknown_negative_rates_and_optional_fields_preserve_raw_and_decimal_precision(self):
        loader = self.loader()
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sample = self.fixture(folder)
            model = sample['models'][0]
            model.update(canonical_slug=None, architecture=None, supported_parameters=None, created=None, context_length=None, top_provider=None)
            model['pricing'] = {'prompt': '-1', 'completion': '0.0000000000001234567890123456789', 'image': '0.04'}
            (folder / 'models.json').write_text(json.dumps({'data': sample['models']}))
            summary = json.loads((folder / 'summary.json').read_text())
            summary['unique_canonical_slugs'] = 0
            (folder / 'summary.json').write_text(json.dumps(summary))
            try:
                loader.load_run(self.conn, folder, minimum_models=1)
            except psycopg.errors.CheckViolation:
                self.fail('negative source rates must be preserved raw but excluded from usable prices')
        row = self.conn.execute('SELECT canonical_model_id, prompt_usd_per_token, completion_usd_per_token, input_modalities, output_modalities, supported_parameters, context_length, catalog_created_at, raw_payload, pricing FROM catalog_entries').fetchone()
        self.assertEqual(row[:8], (None, None, Decimal('0.0000000000001234567890123456789'), None, None, None, None, None))
        self.assertEqual(row[8], model)
        self.assertEqual(row[9], model['pricing'])

    def test_malformed_typed_metadata_is_rejected_with_safe_validation_errors(self):
        loader = self.loader()
        changes = [
            {'context_length': True}, {'context_length': -1}, {'context_length': '1024'},
            {'created': True}, {'created': 253402300800}, {'created': -1},
            {'pricing': {'prompt': 'NaN'}}, {'pricing': {'prompt': 'Infinity'}},
            {'pricing': {'prompt': True}}, {'pricing': {'prompt': 0.000002}},
            {'pricing': {'prompt': 'not-a-price'}}, {'pricing': []},
            {'architecture': []}, {'architecture': {'output_modalities': 'text'}},
            {'supported_parameters': [123]}, {'canonical_slug': ' spaced/slug'},
        ]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                sample = self.fixture(folder)
                sample['models'][0].update(change)
                (folder / 'models.json').write_text(json.dumps({'data': sample['models']}))
                with self.assertRaises(loader.LoadError):
                    loader.load_run(self.conn, folder, minimum_models=1)
                self.assertEqual(self.conn.execute('SELECT count(*) FROM catalog_entries').fetchone()[0], 0)

    def test_cli_requires_private_database_configuration_and_suppresses_connection_errors(self):
        loader = self.loader()
        self.assertTrue(hasattr(loader, 'main'), 'explicit safe CLI is missing')
        with tempfile.TemporaryDirectory() as directory:
            for value in ['', 'synthetic-secret-that-must-not-appear']:
                env = dict(os.environ, DATABASE_URL=value)
                result = subprocess.run([sys.executable, str(ROOT / 'ingest/load.py'), '--run-dir', directory], cwd=directory, env=env, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('synthetic-secret-that-must-not-appear', result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stdout + result.stderr)
                self.assertIn('Load failed', result.stdout + result.stderr)

    def query(self, number):
        text = re.sub(r'--[^\n]*', '', (ROOT / 'db/queries.sql').read_text())
        statements = [s.strip() for s in text.split(';') if s.strip()]
        self.assertGreaterEqual(len(statements), number, 'proposed business query not implemented')
        return statements[number - 1]

    def test_query1_shortlist_uses_exact_base_units_and_joined_identity(self):
        statement = self.query(1)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            self.loader().load_run(self.conn, folder, minimum_models=1)
        rows = self.conn.execute(statement).fetchall()
        self.assertEqual(rows[0][:2], ('openai/gpt-4.1', 'openai/gpt-4.1-2025-04-14'))
        self.assertEqual(rows[0][2:5], (Decimal('2'), Decimal('8'), Decimal('4')))
        self.assertEqual(len(rows), 1)

    def test_query2_preserves_distinct_provider_routes_and_endpoint_prices(self):
        statement = self.query(2)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            self.loader().load_run(self.conn, folder, minimum_models=1)
        rows = self.conn.execute(statement).fetchall()
        self.assertEqual(len(rows), 3)
        self.assertEqual({row[2] for row in rows}, {'azure', 'azure/swedencentral', 'openai'})
        by_tag = {row[2]: row for row in rows}
        self.assertEqual(by_tag['azure/swedencentral'][4], Decimal('2.2'))
        self.assertEqual(by_tag['openai'][1], 'OpenAI')

    def test_query2_distinguishes_name_only_routes_with_missing_or_null_tags(self):
        # Synthetic variants of the linked fixture, not observed source routes.
        names = ["Azure | Alpha customer's route", 'Azure | Zeta "priority" route']
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sample = self.fixture(folder)
            route = dict(sample['endpoints'][0])
            route.pop('tag')
            # Reverse insertion order; an absent tag and explicit null both map to NULL.
            sample['endpoints'] = [dict(route, name=names[1]),
                                   dict(route, tag=None, name=names[0])]
            (folder / 'endpoints.json').write_text(json.dumps({'data': sample['endpoints']}))
            summary = json.loads((folder / 'summary.json').read_text())
            summary['related_endpoints'] = 2
            (folder / 'summary.json').write_text(json.dumps(summary))
            self.loader().load_run(self.conn, folder, minimum_models=1)
        stored = self.conn.execute('SELECT name, tag, service_tier FROM serving_endpoints ORDER BY name').fetchall()
        self.assertEqual(stored, [(name, None, None) for name in names])
        rows = self.conn.execute(self.query(2)).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(set(rows)), 2,
                         'Q2 must distinguish name-only routes instead of displaying identical rows')
        expected_prefix = ('openai/gpt-4.1', 'Azure', None, None,
                           Decimal('2'), Decimal('8'), 1047576, 942818)
        self.assertEqual([row[:8] for row in rows], [expected_prefix, expected_prefix])
        self.assertEqual([row[8] for row in rows], names,
                         'Q2 must append endpoint names and order tied routes by name')

    def test_query3_groups_aliases_without_collapsing_catalog_rows(self):
        statement = self.query(3)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sample = self.fixture(folder)
            sample['models'].append(dict(sample['models'][0], id='test/alias'))
            (folder / 'models.json').write_text(json.dumps({'data': sample['models']}))
            summary = json.loads((folder / 'summary.json').read_text())
            summary['unique_catalog_ids'] = 2
            (folder / 'summary.json').write_text(json.dumps(summary))
            self.loader().load_run(self.conn, folder, minimum_models=1)
        rows = self.conn.execute(statement).fetchall()
        self.assertEqual(rows, [('openai/gpt-4.1-2025-04-14', 2, ['openai/gpt-4.1', 'test/alias'])])

    def test_query4_filters_catalog_addition_time_against_observation_not_release(self):
        statement = self.query(4)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sample = self.fixture(folder)
            added = int(datetime.fromisoformat(sample['observed_at']).timestamp()) - 86400
            sample['models'].append(dict(sample['models'][0], id='test/new', created=added))
            (folder / 'models.json').write_text(json.dumps({'data': sample['models']}))
            summary = json.loads((folder / 'summary.json').read_text())
            summary['unique_catalog_ids'] = 2
            (folder / 'summary.json').write_text(json.dumps(summary))
            self.loader().load_run(self.conn, folder, minimum_models=1)
        rows = self.conn.execute(statement).fetchall()
        self.assertEqual([r[0] for r in rows], ['test/new'])
        self.assertEqual(rows[0][1].timestamp(), added)

    def test_query5_counts_entry_coverage_without_multiplying_provider_rows(self):
        statement = self.query(5)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            self.loader().load_run(self.conn, folder, minimum_models=1)
        rows = self.conn.execute(statement).fetchall()
        self.assertEqual(rows, [(['text'], 1, 1, Decimal('100.00'))])

    def test_malformed_manifests_and_nested_endpoint_identity_fail_closed(self):
        loader = self.loader()
        for case in ['summary_array', 'summary_bool_count', 'model_envelope_array', 'endpoint_id_array']:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                sample = self.fixture(folder)
                if case == 'summary_array':
                    (folder / 'summary.json').write_text('[]')
                elif case == 'summary_bool_count':
                    summary = json.loads((folder / 'summary.json').read_text())
                    summary['unique_catalog_ids'] = True
                    (folder / 'summary.json').write_text(json.dumps(summary))
                elif case == 'model_envelope_array':
                    (folder / 'models.json').write_text('[]')
                else:
                    sample['endpoints'][0]['model_id'] = []
                    (folder / 'endpoints.json').write_text(json.dumps({'data': sample['endpoints']}))
                with self.assertRaises(loader.LoadError):
                    loader.load_run(self.conn, folder, minimum_models=1)
                self.assertEqual(self.conn.execute('SELECT count(*) FROM catalog_entries').fetchone()[0], 0)

    def test_literal_source_strings_cannot_execute_sql_or_change_payload_hashes(self):
        # Characterization/security regression of the already parameterized path.
        # No new production behavior is introduced in this test-only addition.
        loader = self.loader()
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sample = self.fixture(folder)
            identity = "test/x');--"
            sample['models'][0]['id'] = identity
            sample['models'][0]['name'] = "literal'); DROP TABLE providers; --"
            for row in sample['endpoints']:
                row['model_id'] = identity
                row['provider_name'] = "literal'); DROP TABLE catalog_entries; --"
            (folder / 'models.json').write_text(json.dumps({'data': sample['models']}))
            (folder / 'endpoints.json').write_text(json.dumps({'data': sample['endpoints']}))
            loader.load_run(self.conn, folder, minimum_models=1)
        row = self.conn.execute('SELECT catalog_id, name, raw_payload, payload_sha256 FROM catalog_entries').fetchone()
        self.assertEqual(row[:3], (identity, sample['models'][0]['name'], sample['models'][0]))
        import hashlib
        expected = hashlib.sha256(json.dumps(sample['models'][0], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(row[3], expected)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM providers').fetchone()[0], 1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM serving_endpoints').fetchone()[0], 3)

    def test_typed_domain_values_and_constraints_reject_impossible_metadata(self):
        columns = dict(self.conn.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_schema=%s AND table_name=%s', (self.schema, 'catalog_entries')).fetchall())
        self.assertEqual(columns.get('context_length'), 'bigint')
        self.assertEqual(columns.get('prompt_usd_per_token'), 'numeric')
        self.assertEqual(columns.get('catalog_created_at'), 'timestamp with time zone')
        required = {'source_observed_at', 'payload_sha256', 'raw_payload', 'output_modalities', 'supported_parameters'}
        self.assertTrue(required.issubset(columns))
        base = "INSERT INTO catalog_entries(catalog_id, source_observed_at, payload_sha256, raw_payload) VALUES (%s, now(), %s, '{}'::jsonb) RETURNING catalog_entry_id"
        entry = self.conn.execute(base, ('test/x', 'a' * 64)).fetchone()[0]
        for statement, args, error in [
            (base, ('test/x', 'a' * 64), psycopg.errors.UniqueViolation),
            (base, ('', 'a' * 64), psycopg.errors.CheckViolation),
            (base, ('test/y', 'not-a-hash'), psycopg.errors.CheckViolation),
            ('UPDATE catalog_entries SET context_length=-1 WHERE catalog_entry_id=%s', (entry,), psycopg.errors.CheckViolation),
            ('UPDATE catalog_entries SET prompt_usd_per_token=-1 WHERE catalog_entry_id=%s', (entry,), psycopg.errors.CheckViolation),
            ("UPDATE catalog_entries SET prompt_usd_per_token='NaN' WHERE catalog_entry_id=%s", (entry,), psycopg.errors.CheckViolation),
            ("UPDATE catalog_entries SET raw_payload='[]'::jsonb WHERE catalog_entry_id=%s", (entry,), psycopg.errors.CheckViolation),
            ('UPDATE catalog_entries SET canonical_model_id=999 WHERE catalog_entry_id=%s', (entry,), psycopg.errors.ForeignKeyViolation),
            ('UPDATE catalog_entries SET source_observed_at=NULL WHERE catalog_entry_id=%s', (entry,), psycopg.errors.NotNullViolation),
            ("UPDATE catalog_entries SET last_updated_at=first_seen_at-interval '1 second' WHERE catalog_entry_id=%s", (entry,), psycopg.errors.CheckViolation),
            ("INSERT INTO providers(provider_name) VALUES ('')", (), psycopg.errors.CheckViolation),
        ]:
            with self.subTest(statement=statement), self.assertRaises(error), self.conn.transaction():
                self.conn.execute(statement, args)


if __name__ == '__main__':
    unittest.main()
