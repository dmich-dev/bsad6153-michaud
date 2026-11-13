"""DRAFT / FOR REVIEW: parameterized PostgreSQL loader for fetch.py output.

Metadata only. Never reads credentials from input data or emits connection strings.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
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
    return rate if rate >= 0 else None


def validate_metadata(row):
    """Reject wrong shapes; absent optional metadata remains SQL NULL."""
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


def read_run(run_dir, minimum_models):
    """Validate manifest, exact identities and relationships before any writes."""
    try:
        folder = Path(run_dir)
        models = json.loads((folder / 'models.json').read_text())['data']
        endpoints = json.loads((folder / 'endpoints.json').read_text())['data']
        summary = json.loads((folder / 'summary.json').read_text())
        if not isinstance(summary, dict):
            raise LoadError('Fetch summary must be an object')
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
            if not (row.get('tag') or row.get('name')):
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


def load_run(conn, run_dir, *, minimum_models=500):
    """Validate then atomically insert. Caller owns the connection, not secrets."""
    models, endpoints, observed = read_run(run_dir, minimum_models)
    with conn.transaction():
        return _insert_rows(conn, models, endpoints, observed)


def _insert_rows(conn, models, endpoints, observed):
    canonical = {}
    for row in models:
        slug = row.get('canonical_slug')
        if slug and slug not in canonical:
            conn.execute('INSERT INTO canonical_models(canonical_slug) VALUES (%s) ON CONFLICT (canonical_slug) DO NOTHING', (slug,))
            canonical[slug] = conn.execute('SELECT canonical_model_id FROM canonical_models WHERE canonical_slug=%s', (slug,)).fetchone()[0]
    entries = {}
    for row in models:
        pricing = row.get('pricing')
        architecture = row.get('architecture') or {}
        payload_hash = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        conn.execute('''
            INSERT INTO catalog_entries(catalog_id, canonical_model_id, name, catalog_created_at,
                context_length, max_completion_tokens, prompt_usd_per_token, completion_usd_per_token,
                input_modalities, output_modalities, supported_parameters, pricing, raw_payload,
                payload_sha256, source_observed_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (catalog_id) DO NOTHING
        ''', (row['id'], canonical.get(row.get('canonical_slug')), row.get('name'),
              datetime.fromtimestamp(row['created'], timezone.utc) if row.get('created') is not None else None,
              row.get('context_length'), (row.get('top_provider') or {}).get('max_completion_tokens'),
              token_rate(pricing, 'prompt'), token_rate(pricing, 'completion'),
              architecture.get('input_modalities'), architecture.get('output_modalities'),
              row.get('supported_parameters'), Jsonb(pricing) if pricing is not None else None,
              Jsonb(row), payload_hash, observed))
        entries[row['id']] = conn.execute('SELECT catalog_entry_id FROM catalog_entries WHERE catalog_id=%s', (row['id'],)).fetchone()[0]
    providers = {}
    for row in endpoints:
        provider = row['provider_name']
        if provider not in providers:
            conn.execute('INSERT INTO providers(provider_name) VALUES (%s) ON CONFLICT (provider_name) DO NOTHING', (provider,))
            providers[provider] = conn.execute('SELECT provider_id FROM providers WHERE provider_name=%s', (provider,)).fetchone()[0]
    for row in endpoints:
        pricing = row.get('pricing')
        payload_hash = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        conn.execute('''
            INSERT INTO serving_endpoints(catalog_entry_id, provider_id, tag, name, service_tier,
                context_length, max_completion_tokens, prompt_usd_per_token, completion_usd_per_token,
                supported_parameters, pricing, raw_payload, payload_sha256, source_observed_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (catalog_entry_id, provider_id, tag, name, service_tier) DO NOTHING
        ''', (entries[row['model_id']], providers[row['provider_name']], row.get('tag'), row.get('name'),
              row.get('service_tier'), row.get('context_length'), row.get('max_completion_tokens'),
              token_rate(pricing, 'prompt'), token_rate(pricing, 'completion'),
              row.get('supported_parameters'), Jsonb(pricing) if pricing is not None else None,
              Jsonb(row), payload_hash, observed))
    counts = {
        'canonical_models': conn.execute('SELECT count(*) FROM canonical_models').fetchone()[0],
        'catalog_entries': conn.execute('SELECT count(*) FROM catalog_entries').fetchone()[0],
        'providers': conn.execute('SELECT count(*) FROM providers').fetchone()[0],
        'serving_endpoints': conn.execute('SELECT count(*) FROM serving_endpoints').fetchone()[0],
    }
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
            result = load_run(conn, args.run_dir)
        print(json.dumps(result, indent=2))
        return 0
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
