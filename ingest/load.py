"""DRAFT / FOR REVIEW: parameterized PostgreSQL loader for fetch.py output.

Metadata only. Never reads credentials from input data or emits connection strings.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from psycopg.types.json import Jsonb


class LoadError(ValueError):
    """Credential-free validation diagnostic; never includes raw source values."""


def token_rate(pricing, field):
    """Negative routing/unknown rates are not credits or usable token prices."""
    if pricing is None or pricing.get(field) is None:
        return None
    value = pricing[field]
    if not isinstance(value, str):
        raise LoadError('Token rates must be exact decimal strings')
    try:
        rate = Decimal(value)
    except InvalidOperation:
        raise LoadError('Invalid decimal token rate') from None
    if not rate.is_finite():
        raise LoadError('Non-finite token rate')
    if rate < 0:
        return None
    # PostgreSQL numeric: 131072 integer digits, 16383 fractional digits.
    # Inspect the exact tuple, not normalize()/quantize() (context rounding),
    # float conversion, or fixed-point formatting of enormous exponents.
    exponent = int(rate.as_tuple().exponent)
    if (exponent < -16383 or (rate and rate.adjusted() >= 131072)
            or (not rate and exponent > (2**31 - 1) // 2)):
        # Even zero's scientific exponent must fit PostgreSQL's text parser.
        raise LoadError('Token rate exceeds PostgreSQL numeric range')
    return rate


def _validate_json_strings(value):
    """Reject text PostgreSQL cannot store, without changing source content."""
    if isinstance(value, str):
        if '\x00' in value or any('\ud800' <= char <= '\udfff' for char in value):
            raise LoadError('JSON text contains NUL or invalid Unicode')
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_json_strings(key)
            _validate_json_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_json_strings(item)


def validate_metadata(row):
    """Reject wrong shapes; absent optional metadata remains SQL NULL."""
    try:
        json.dumps(row, allow_nan=False)
    except (TypeError, ValueError):
        raise LoadError('Invalid or non-finite raw JSON metadata') from None
    _validate_json_strings(row)
    for field in ('pricing', 'architecture', 'top_provider'):
        if row.get(field) is not None and not isinstance(row[field], dict):
            raise LoadError('Invalid metadata object')
    for obj, field, maximum in [
        (row, 'context_length', 9223372036854775807),
        (row, 'max_completion_tokens', 9223372036854775807),
        (row.get('top_provider') or {}, 'max_completion_tokens', 9223372036854775807),
        (row, 'created', 253402300799),
    ]:
        value = obj.get(field)
        if value is not None and (type(value) is not int or not 0 <= value <= maximum):
            raise LoadError('Invalid integer metadata range or type')
    for obj, field in [(row, 'supported_parameters'),
                       (row.get('architecture') or {}, 'input_modalities'),
                       (row.get('architecture') or {}, 'output_modalities')]:
        value = obj.get(field)
        if value is not None and (not isinstance(value, list) or any(not isinstance(x, str) for x in value)):
            raise LoadError('Metadata arrays must contain text values')
    slug = row.get('canonical_slug')
    if slug is not None and (not isinstance(slug, str) or not slug or any(c.isspace() for c in slug)):
        raise LoadError('Invalid canonical identifier; values are never repaired')
    if row.get('name') is not None and not isinstance(row['name'], str):
        raise LoadError('Metadata label must be text')
    token_rate(row.get('pricing'), 'prompt')
    token_rate(row.get('pricing'), 'completion')


def _finite_json_number(text):
    """Keep normal JSON float semantics, but reject constants and overflow."""
    value = float(text)
    if not math.isfinite(value):
        raise LoadError('Non-finite JSON number')
    return value


def read_run(run_dir, minimum_models):
    """Validate manifest, exact identities and relationships before any writes."""
    try:
        folder = Path(run_dir)
        models = json.loads((folder / 'models.json').read_text(encoding='utf-8'),
                            parse_constant=_finite_json_number, parse_float=_finite_json_number)['data']
        endpoints = json.loads((folder / 'endpoints.json').read_text(encoding='utf-8'),
                               parse_constant=_finite_json_number, parse_float=_finite_json_number)['data']
        summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'),
                             parse_constant=_finite_json_number, parse_float=_finite_json_number)
        if not isinstance(summary, dict):
            raise LoadError('Fetch summary must be an object')
        _validate_json_strings(summary)
        if any(type(summary.get(k)) is not int or summary[k] < 0 for k in
               ('unique_catalog_ids', 'unique_canonical_slugs', 'related_endpoints')):
            raise LoadError('Fetch summary counts must be nonnegative integers')
        if (summary.get('complete') is not True or summary.get('catalog_finished') is not True
                or summary.get('source') != 'https://openrouter.ai' or summary.get('issues') != []):
            raise LoadError('Only complete, issue-free OpenRouter fetch output is accepted')
        observed = datetime.fromisoformat(summary['finished_at'])
        if observed.tzinfo is None or observed.utcoffset() is None:
            raise LoadError('Fetch timestamp must include a timezone')
        if not isinstance(models, list) or not isinstance(endpoints, list):
            raise LoadError('Expected model and endpoint arrays')
        unique_models = {}
        for row in models:
            identity = row.get('id') if isinstance(row, dict) else None
            if (not isinstance(identity, str) or not identity or any(c.isspace() for c in identity)):
                raise LoadError('Invalid catalog identifier; values are never repaired')
            validate_metadata(row)
            if identity in unique_models and unique_models[identity] != row:
                raise LoadError('Conflicting duplicate catalog identity')
            unique_models[identity] = row
        unique_endpoints = {}
        for row in endpoints:
            if not isinstance(row, dict) or row.get('model_id') not in unique_models:
                raise LoadError('Endpoint is missing its fetched parent')
            validate_metadata(row)
            provider = row.get('provider_name')
            if not isinstance(provider, str) or not provider.strip():
                raise LoadError('Invalid provider identity')
            for field in ('tag', 'name', 'service_tier'):
                if row.get(field) is not None and not isinstance(row[field], str):
                    raise LoadError('Invalid endpoint identity component')
            if not any((row.get(field) or '').strip() for field in ('tag', 'name')):
                raise LoadError('Endpoint needs a routing tag or name')
            identity = tuple(row.get(k) for k in ('model_id', 'provider_name', 'tag', 'name', 'service_tier'))
            if identity in unique_endpoints and unique_endpoints[identity] != row:
                raise LoadError('Conflicting duplicate endpoint identity')
            unique_endpoints[identity] = row
        canonical_count = len({r['canonical_slug'] for r in unique_models.values() if r.get('canonical_slug') is not None})
        if (type(minimum_models) is not int or minimum_models < 1
                or len(unique_models) < minimum_models or not unique_endpoints):
            raise LoadError('Insufficient unique catalog records or no related endpoints')
        if (summary.get('unique_catalog_ids') != len(unique_models)
                or summary.get('unique_canonical_slugs') != canonical_count
                or summary.get('related_endpoints') != len(unique_endpoints)):
            raise LoadError('Unique source counts disagree with the fetch summary')
        return list(unique_models.values()), list(unique_endpoints.values()), observed
    except LoadError:
        raise
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        raise LoadError('Unreadable or malformed fetch output; no data loaded') from None


def _report(progress, message):
    if progress is not None:
        progress(message)


def load_run(conn, run_dir, *, minimum_models=500, progress=None):
    """Validate then atomically insert. Progress reports stages, never a commit."""
    _report(progress, 'Validating saved input...')
    models, endpoints, observed = read_run(run_dir, minimum_models)
    with conn.transaction():
        conn.execute("SELECT set_config('statement_timeout', %s, true)", ('30000',))
        conn.execute("SELECT set_config('lock_timeout', %s, true)", ('5000',))
        return _insert_rows(conn, models, endpoints, observed, progress=progress)


def _insert_rows(conn, models, endpoints, observed, *, progress=None):
    # executemany uses Psycopg's pipeline support: bind every value, but avoid
    # one synchronous WAN round trip per INSERT and per natural-ID lookup.
    slugs = list(dict.fromkeys(row['canonical_slug'] for row in models if row.get('canonical_slug')))
    canonical = {}
    _report(progress, f'Loading canonical_models ({len(slugs)} source identities)...')
    if slugs:
        with conn.cursor() as cursor:
            cursor.executemany(
                'INSERT INTO canonical_models(canonical_slug) VALUES (%s) ON CONFLICT (canonical_slug) DO NOTHING',
                [(slug,) for slug in slugs])
        canonical = dict(conn.execute(
            'SELECT canonical_slug, canonical_model_id FROM canonical_models WHERE canonical_slug = ANY(%s::text[])',
            (slugs,)).fetchall())

    _report(progress, f'Loading catalog_entries ({len(models)} source records)...')
    catalog_values = []
    for row in models:
        pricing = row.get('pricing')
        architecture = row.get('architecture') or {}
        payload_hash = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        catalog_values.append((row['id'], canonical.get(row.get('canonical_slug')), row.get('name'),
            datetime.fromtimestamp(row['created'], timezone.utc) if row.get('created') is not None else None,
            row.get('context_length'), (row.get('top_provider') or {}).get('max_completion_tokens'),
            token_rate(pricing, 'prompt'), token_rate(pricing, 'completion'),
            architecture.get('input_modalities'), architecture.get('output_modalities'),
            row.get('supported_parameters'), Jsonb(pricing) if pricing is not None else None,
            Jsonb(row), payload_hash, observed))
    with conn.cursor() as cursor:
        cursor.executemany('''INSERT INTO catalog_entries(
            catalog_id, canonical_model_id, name, catalog_created_at,
            context_length, max_completion_tokens, prompt_usd_per_token, completion_usd_per_token,
            input_modalities, output_modalities, supported_parameters, pricing, raw_payload,
            payload_sha256, source_observed_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (catalog_id) DO NOTHING''', catalog_values)
    entries = dict(conn.execute(
        'SELECT catalog_id, catalog_entry_id FROM catalog_entries WHERE catalog_id = ANY(%s::text[])',
        ([row['id'] for row in models],)).fetchall())

    provider_names = list(dict.fromkeys(row['provider_name'] for row in endpoints))
    providers = {}
    _report(progress, f'Loading providers ({len(provider_names)} source providers)...')
    if provider_names:
        with conn.cursor() as cursor:
            cursor.executemany(
                'INSERT INTO providers(provider_name) VALUES (%s) ON CONFLICT (provider_name) DO NOTHING',
                [(name,) for name in provider_names])
        providers = dict(conn.execute(
            'SELECT provider_name, provider_id FROM providers WHERE provider_name = ANY(%s::text[])',
            (provider_names,)).fetchall())
    _report(progress, f'Loading serving_endpoints ({len(endpoints)} source offerings)...')
    endpoint_values = []
    for row in endpoints:
        pricing = row.get('pricing')
        payload_hash = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        endpoint_values.append((entries[row['model_id']], providers[row['provider_name']], row.get('tag'), row.get('name'), row.get('service_tier'),
            row.get('context_length'), row.get('max_completion_tokens'),
            token_rate(pricing, 'prompt'), token_rate(pricing, 'completion'),
            row.get('supported_parameters'), Jsonb(pricing) if pricing is not None else None,
            Jsonb(row), payload_hash, observed))
    if endpoint_values:
        with conn.cursor() as cursor:
            cursor.executemany('''INSERT INTO serving_endpoints(
                catalog_entry_id, provider_id, tag, name, service_tier,
                context_length, max_completion_tokens, prompt_usd_per_token, completion_usd_per_token,
                supported_parameters, pricing, raw_payload, payload_sha256, source_observed_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (catalog_entry_id, provider_id, tag, name, service_tier) DO NOTHING''', endpoint_values)
    _report(progress, 'Checking resulting table counts...')
    counts = dict(conn.execute('''
        SELECT 'canonical_models', count(*) FROM canonical_models
        UNION ALL SELECT 'catalog_entries', count(*) FROM catalog_entries
        UNION ALL SELECT 'providers', count(*) FROM providers
        UNION ALL SELECT 'serving_endpoints', count(*) FROM serving_endpoints
    ''').fetchall())
    return {'counts': counts}


def main(argv=None):
    """Student runs privately; the assistant must never receive real owner secrets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path, help='Complete fetch.py output directory')
    args = parser.parse_args(argv)
    try:
        load_dotenv(Path.cwd() / '.env', override=False)
        url = os.environ.get('DATABASE_URL')
        if not url:
            print('Load failed: DATABASE_URL is not configured privately.')
            return 2
        with psycopg.connect(url, connect_timeout=10, autocommit=True) as conn:
            result = load_run(conn, args.run_dir,
                progress=lambda message: print('[load] ' + message, file=sys.stderr, flush=True))
        print(json.dumps(result, indent=2))
        return 0
    except KeyboardInterrupt:
        print('Load interrupted; completion was not confirmed. Check database counts before retrying.')
        return 130
    except LoadError as error:
        print('Load failed:', error)
        return 2
    except (psycopg.Error, OSError, ValueError, TypeError):
        # Driver errors can contain hostnames, usernames, source data or secrets.
        # Deliberately do not echo them or exception tracebacks.
        print('Load failed: database or local configuration error; no partial load committed.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
