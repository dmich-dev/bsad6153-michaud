"""Synthetic preflight regressions; owned PostgreSQL only, no cloud evidence."""
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from typing import Any
from unittest.mock import patch

import test_database as base_tests


ROOT = Path(__file__).resolve().parents[1]


def loader_module():
    spec = importlib.util.spec_from_file_location('preflight_loader', ROOT / 'ingest/load.py')
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(folder):
    """Entirely synthetic UTF-8 saved run; never reads the saved real catalog."""
    model = {'id': 'synthetic/café', 'canonical_slug': 'synthetic/café-v1',
             'name': 'Synthetic café 模型 🚀',
             'pricing': {'prompt': '0.000002', 'completion': '-1'},
             'extra': {'values': [None, True, 3, 0.125, '1e131072']}}
    endpoint = {'model_id': model['id'], 'provider_name': 'Fournisseur café',
                'tag': ' route/é ', 'name': ' Déploiement 模型 ', 'service_tier': None,
                'pricing': {'prompt': '0', 'completion': '0.000008'}}
    summary = {'complete': True, 'catalog_finished': True, 'source': 'https://openrouter.ai',
               'finished_at': '2026-11-07T12:00:00+00:00', 'unique_catalog_ids': 1,
               'unique_canonical_slugs': 1, 'related_endpoints': 1, 'issues': [],
               'extra': 'Synthetic résumé'}
    documents = {'models.json': {'data': [model]}, 'endpoints.json': {'data': [endpoint]},
                 'summary.json': summary}
    write_documents(folder, documents)
    return documents


def write_documents(folder, documents):
    for name, data in documents.items():
        (folder / name).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


class NoDatabaseWork:
    """Fail at transaction entry, earlier than every possible SQL write."""
    def transaction(self):
        raise AssertionError('invalid input reached conn.transaction()')


@unittest.skipUnless(base_tests.psycopg, 'loader dependency psycopg required')
class LoaderPreflightTests(unittest.TestCase):
    def setUp(self):
        self.loader = loader_module()

    def test_unrepresentable_token_rates_fail_before_transaction(self):
        for document in ('models.json', 'endpoints.json'):
            for field in ('prompt', 'completion'):
                for value in ('1e131072', '1e-20000', '1e-16384', '0e-16384', '1e999999999', '0e1073741824'):
                    with self.subTest(document=document, field=field, value=value), tempfile.TemporaryDirectory() as directory:
                        folder = Path(directory)
                        documents = fixture(folder)
                        documents[document]['data'][0]['pricing'][field] = value
                        write_documents(folder, documents)
                        with self.assertRaises(self.loader.LoadError):
                            self.loader.load_run(NoDatabaseWork(), folder, minimum_models=1)

    def test_valid_rates_remain_exact_without_context_rounding_or_raw_changes(self):
        values = ('0', '-0', '0.0000', '0e131072', '0e1073741823', '1e131071', '1e-16383',
                  '123456789012345678901234567890.123456789012345678901234567890')
        with localcontext() as context:
            context.prec = 3
            for value in values:
                with self.subTest(value=value):
                    rate = self.loader.token_rate({'prompt': value}, 'prompt')
                    self.assertEqual(rate.as_tuple(), Decimal(value).as_tuple())
            for value in ('-1', '-1e131072', '-1e-20000'):
                with self.subTest(negative_sentinel=value):
                    self.assertIsNone(self.loader.token_rate({'prompt': value}, 'prompt'))
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            documents = fixture(folder)
            models, endpoints, _ = self.loader.read_run(folder, 1)
            self.assertEqual(models, documents['models.json']['data'])
            self.assertEqual(endpoints, documents['endpoints.json']['data'])
            self.assertIsInstance(models[0]['extra']['values'][-1], str)

    def test_nonfinite_json_at_any_depth_fails_before_transaction(self):
        for document in ('models.json', 'endpoints.json', 'summary.json'):
            for literal in ('NaN', 'Infinity', '-Infinity', '1e400', '-1e400'):
                with self.subTest(document=document, literal=literal), tempfile.TemporaryDirectory() as directory:
                    folder = Path(directory)
                    documents = fixture(folder)
                    # Place the value outside all recognized typed fields.
                    target = documents[document] if document == 'summary.json' else documents[document]['data'][0]
                    target['unknown'] = {'nested': [{'value': '__NONFINITE_TEST_VALUE__'}]}
                    write_documents(folder, documents)
                    path = folder / document
                    text = path.read_text(encoding='utf-8').replace('"__NONFINITE_TEST_VALUE__"', literal)
                    path.write_text(text, encoding='utf-8')
                    with self.assertRaises(self.loader.LoadError):
                        self.loader.load_run(NoDatabaseWork(), folder, minimum_models=1)

    def test_unrepresentable_json_strings_fail_before_transaction(self):
        for document in ('models.json', 'endpoints.json', 'summary.json'):
            for position in ('key', 'value', 'nested_key', 'nested_value'):
                for invalid in ('\x00', '\ud800', '\udbff', '\udc00', '\udfff'):
                    with self.subTest(document=document, position=position, invalid=repr(invalid)), tempfile.TemporaryDirectory() as directory:
                        folder = Path(directory)
                        documents = fixture(folder)
                        target = documents[document] if document == 'summary.json' else documents[document]['data'][0]
                        text = 'synthetic-sensitive-text' + invalid
                        if position == 'key':
                            target[text] = 'ordinary value'
                        elif position == 'value':
                            target['unknown'] = text
                        elif position == 'nested_key':
                            target['unknown'] = {'nested': [{text: 'ordinary value'}]}
                        else:
                            target['unknown'] = {'nested': [{'value': [text]}]}
                        # JSON escapes can carry NUL/surrogates through valid UTF-8.
                        (folder / document).write_text(json.dumps(documents[document]), encoding='utf-8')
                        with self.assertRaises(self.loader.LoadError) as caught:
                            self.loader.load_run(NoDatabaseWork(), folder, minimum_models=1)
                        diagnostic = str(caught.exception)
                        diagnostic.encode('utf-8')
                        self.assertNotIn('synthetic-sensitive-text', diagnostic)
                        self.assertNotIn(str(folder), diagnostic)
                        self.assertNotIn(invalid, diagnostic)

    def test_metadata_validation_rejects_unrepresentable_json_strings(self):
        for invalid in ('\x00', '\ud800', '\udbff', '\udc00', '\udfff'):
            for row in ({invalid: 'ordinary'}, {'unknown': {'nested': [{invalid: 'ordinary'}]}},
                        {'unknown': {'nested': [{'value': [invalid]}]}}):
                with self.subTest(row=repr(row)):
                    with self.assertRaises(self.loader.LoadError):
                        self.loader.validate_metadata(row)

    def test_valid_json_text_preserves_unicode_identifiers_and_raw_hashes(self):
        cases = (('astral', '🚀', False), ('accent', 'café', False),
                 ('combining', 'cafe\u0301', False), ('escaped_pair', '🚀', True),
                 ('literal_backslash', r'\u0000', False), ('nan_name', 'NaN', False),
                 ('infinity_name', 'Infinity', False))
        for label, text, escaped in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                documents = fixture(folder)
                model = documents['models.json']['data'][0]
                endpoint = documents['endpoints.json']['data'][0]
                model.update(id='synthetic/' + text, canonical_slug='synthetic/' + text + '-v1',
                             name=' NaN Research | ' + text + ' ', supported_parameters=[text, r'\u0000'])
                endpoint.update(model_id=model['id'], provider_name=' Infinity Models | ' + text + ' ',
                                tag=' route/' + text + ' ', name=' NaN route | ' + text + ' ',
                                service_tier=' Infinity tier | ' + text + ' ')
                for target in (model, endpoint, documents['summary.json']):
                    target['unknown'] = {text: [{'value': [text, r'\u0000'], 'NaN': 'Infinity'}]}
                for name, data in documents.items():
                    (folder / name).write_text(json.dumps(data, ensure_ascii=escaped), encoding='utf-8')
                if escaped:
                    self.assertIn(r'\ud83d\ude80', (folder / 'models.json').read_text(encoding='utf-8'))
                before = {name: (folder / name).read_bytes() for name in documents}
                expected_hashes = [hashlib.sha256(json.dumps(
                    row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()
                    for row in (model, endpoint)]
                models, endpoints, _ = self.loader.read_run(folder, 1)
                self.assertEqual(models, [model])
                self.assertEqual(endpoints, [endpoint])
                actual_hashes = [hashlib.sha256(json.dumps(
                    row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()
                    for row in (models[0], endpoints[0])]
                self.assertEqual(actual_hashes, expected_hashes)
                self.assertEqual({name: (folder / name).read_bytes() for name in documents}, before)

    def test_metadata_validation_rejects_nonfinite_or_nonserializable_raw_values(self):
        for value in (float('nan'), float('inf'), float('-inf'), {'not-json'}, Decimal('1.2')):
            with self.subTest(type=type(value).__name__, value=repr(value)):
                with self.assertRaises(self.loader.LoadError):
                    self.loader.validate_metadata({'unknown': {'nested': [value]}})

    def test_finite_json_strings_and_types_are_not_reinterpreted(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            documents = fixture(folder)
            model = documents['models.json']['data'][0]
            model['unknown'] = {'strings': ['NaN', 'Infinity', '-Infinity', '1e400'],
                                'nested': [None, False, 42, 1.25]}
            write_documents(folder, documents)
            models, _, _ = self.loader.read_run(folder, 1)
            self.assertEqual(models[0], model)
            self.assertIs(type(models[0]['unknown']['nested'][-1]), float)

    def test_utf8_survives_legacy_default_codec_simulation_not_native_windows(self):
        # Linux-only cp1252 default-codec simulation; NOT native Windows evidence.
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            documents = fixture(folder)
            original_read_text = Path.read_text
            observed = []

            def legacy_default(path, *args, **kwargs):
                if path.parent == folder:
                    encoding = args[0] if args else kwargs.get('encoding')
                    observed.append((path.name, encoding))
                    if encoding is None:
                        kwargs['encoding'] = 'cp1252'
                return original_read_text(path, *args, **kwargs)

            with patch.object(Path, 'read_text', legacy_default):
                models, endpoints, _ = self.loader.read_run(folder, 1)
            self.assertEqual(models, documents['models.json']['data'])
            self.assertEqual(endpoints, documents['endpoints.json']['data'])
            self.assertEqual(observed, [('models.json', 'utf-8'), ('endpoints.json', 'utf-8'),
                                        ('summary.json', 'utf-8')])

    def test_invalid_utf8_fails_with_safe_error_before_transaction(self):
        for document in ('models.json', 'endpoints.json', 'summary.json'):
            with self.subTest(document=document), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                fixture(folder)
                path = folder / document
                path.write_bytes(path.read_bytes() + b'\xff')
                with self.assertRaises(self.loader.LoadError) as caught:
                    self.loader.load_run(NoDatabaseWork(), folder, minimum_models=1)
                self.assertNotIn(str(folder), str(caught.exception))

    def test_endpoint_without_usable_tag_or_name_fails_before_transaction(self):
        for tag, name in ((' ', None), (None, '\t'), ('', '\u2003'), (' \t ', '\n'),
                          ('\u00a0', '\u2003'), (None, None)):
            with self.subTest(tag=tag, name=name), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                documents = fixture(folder)
                documents['endpoints.json']['data'][0].update(tag=tag, name=name)
                write_documents(folder, documents)
                with self.assertRaises(self.loader.LoadError):
                    self.loader.load_run(NoDatabaseWork(), folder, minimum_models=1)

    def test_usable_endpoint_component_is_preserved_without_normalization(self):
        for tag, name in ((' \troute/é ', None), (None, ' Déploiement 模型 '),
                          (' ', ' Exact name '), (' Exact route ', '\t')):
            with self.subTest(tag=tag, name=name), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                documents = fixture(folder)
                documents['endpoints.json']['data'][0].update(tag=tag, name=name)
                write_documents(folder, documents)
                _, endpoints, _ = self.loader.read_run(folder, 1)
                self.assertEqual(endpoints, documents['endpoints.json']['data'])


@unittest.skipUnless(base_tests.psycopg and os.environ.get('MILESTONE2_TEST_DSN'),
                     'explicit disposable PostgreSQL required')
class LoaderPreflightPostgreSQLTests(unittest.TestCase):
    conn: Any
    schema: str
    setUp = base_tests.PostgreSQLTests.setUp
    tearDown = base_tests.PostgreSQLTests.tearDown

    def test_postgresql_confirms_numeric_storage_boundaries(self):
        # Compare Decimal parameters as the actual loader sends them, not floats.
        for value in ('0', '-0', '0.0000', '0e131072', '0e1073741823', '1e131071', '1e-16383',
                      '123456789012345678901234567890.123456789012345678901234567890'):
            with self.subTest(accepted=value):
                # Ask the server to accept the value, without returning a
                # 131072-digit expansion across the wire into Python/logs.
                self.assertTrue(self.conn.execute(
                    'SELECT %s::numeric IS NOT NULL', (Decimal(value),)).fetchone()[0])
        for value in ('1e131072', '1e-20000', '1e-16384', '0e-16384', '0e1073741824'):
            with self.subTest(rejected=value), self.assertRaises(base_tests.psycopg.errors.NumericValueOutOfRange):
                self.conn.execute('SELECT %s::numeric', (Decimal(value),))

    def test_precision_zero_negative_sentinels_unicode_and_hashes_roundtrip(self):
        loader = loader_module()
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            documents = fixture(folder)
            model = documents['models.json']['data'][0]
            endpoint = documents['endpoints.json']['data'][0]
            precise = '0.000000000000123456789012345678901234567890'
            model['pricing'] = {'prompt': precise, 'completion': '-1e131072'}
            endpoint['pricing'] = {'prompt': '0', 'completion': '1e-16383'}
            write_documents(folder, documents)
            first = loader.load_run(self.conn, folder, minimum_models=1)
            before = [self.conn.execute(base_tests.sql.SQL('SELECT * FROM {} ORDER BY 1').format(
                base_tests.sql.Identifier(table))).fetchall() for table in base_tests.TABLES]
            second = loader.load_run(self.conn, folder, minimum_models=1)
            after = [self.conn.execute(base_tests.sql.SQL('SELECT * FROM {} ORDER BY 1').format(
                base_tests.sql.Identifier(table))).fetchall() for table in base_tests.TABLES]
        self.assertEqual(first['counts'], dict(zip(base_tests.TABLES, [1, 1, 1, 1])))
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        for table, row, expected_rates in (
                ('catalog_entries', model, (Decimal(precise), None)),
                ('serving_endpoints', endpoint, (Decimal('0'), Decimal('1e-16383')))):
            stored = self.conn.execute(base_tests.sql.SQL(
                'SELECT raw_payload, pricing, payload_sha256, prompt_usd_per_token, completion_usd_per_token FROM {}').format(
                    base_tests.sql.Identifier(table))).fetchone()
            self.assertEqual(stored[0], row)
            self.assertEqual(stored[1], row['pricing'])
            expected_hash = hashlib.sha256(json.dumps(
                row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()
            self.assertEqual(stored[2], expected_hash)
            self.assertEqual(stored[3:], expected_rates)
        self.assertEqual(self.conn.execute('SELECT tag, name FROM serving_endpoints').fetchone(),
                         (endpoint['tag'], endpoint['name']))


if __name__ == '__main__':
    unittest.main()
