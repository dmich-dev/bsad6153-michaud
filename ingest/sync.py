"""Transactional metadata snapshot synchronization."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load import token_rate, validate_metadata, LoadError


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


class IncompleteSnapshot(ValueError):
    """Incomplete retrieval is logged as partial, with no data committed."""


def validate_snapshot(data):
    if data.get('complete') is not True:
        raise IncompleteSnapshot()
    observed=data['observed']
    if not isinstance(observed,datetime) or observed.tzinfo is None or observed.utcoffset() is None:
        raise LoadError('Invalid observation timestamp')
    if not data['models'] or not data['endpoints']:
        raise LoadError('Empty snapshot cannot prove source coverage')
    models,endpoints={},{}
    for row in data['models']:
        identity=row.get('id') if isinstance(row,dict) else None
        if not isinstance(identity,str) or not identity or any(c.isspace() for c in identity):
            raise LoadError('Invalid exact catalog identity')
        validate_metadata(row)
        if identity in models and models[identity]!=row:
            raise LoadError('Conflicting catalog identity')
        models[identity]=row
    for row in data['endpoints']:
        if not isinstance(row,dict) or row.get('model_id') not in models:
            raise LoadError('Endpoint missing fetched parent')
        validate_metadata(row)
        provider=row.get('provider_name')
        if not isinstance(provider,str) or not provider.strip():
            raise LoadError('Invalid provider identity')
        if any(row.get(k) is not None and not isinstance(row[k],str) for k in ('tag','name','service_tier')):
            raise LoadError('Invalid endpoint identity')
        if not any((row.get(field) or '').strip() for field in ('tag','name')):
            raise LoadError('Endpoint needs tag or name')
        key=tuple(row.get(k) for k in ('model_id','provider_name','tag','name','service_tier'))
        if key in endpoints and endpoints[key]!=row:
            raise LoadError('Conflicting endpoint identity')
        endpoints[key]=row
    return dict(data,models=list(models.values()),endpoints=list(endpoints.values()))


def _upsert(conn, table, values, conflict, counts):
    """Only trusted code supplies table/column identifiers; source values are bound."""
    columns = list(values)
    if 'payload_sha256' in values:
        updates = sql.SQL(',').join(sql.SQL('{}=EXCLUDED.{}').format(sql.Identifier(c), sql.Identifier(c))
                                   for c in columns if c not in conflict)
        action = sql.SQL('DO UPDATE SET {}, last_updated_at=clock_timestamp() WHERE {}.payload_sha256 IS DISTINCT FROM EXCLUDED.payload_sha256').format(updates, sql.Identifier(table))
    else:
        action = sql.SQL('DO NOTHING')
    query = sql.SQL('INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) {} RETURNING (xmax=0)').format(
        sql.Identifier(table), sql.SQL(',').join(map(sql.Identifier,columns)),
        sql.SQL(',').join(sql.Placeholder() for _ in columns),
        sql.SQL(',').join(map(sql.Identifier,conflict)), action)
    result = conn.execute(query, tuple(values.values())).fetchone()
    if result:
        counts[table]['inserted' if result[0] else 'updated'] += 1


def _apply(conn, data):
    counts = {t:dict(inserted=0,updated=0) for t in
              ['canonical_models','catalog_entries','providers','serving_endpoints']}
    canonical, entries, providers = {}, {}, {}
    for row in data['models']:
        slug=row.get('canonical_slug')
        if slug and slug not in canonical:
            _upsert(conn,'canonical_models',dict(canonical_slug=slug),['canonical_slug'],counts)
            canonical[slug]=conn.execute('SELECT canonical_model_id FROM canonical_models WHERE canonical_slug=%s',(slug,)).fetchone()[0]
    for row in data['models']:
        pricing=row.get('pricing')
        arch=row.get('architecture') or {}
        values=dict(catalog_id=row['id'],canonical_model_id=canonical.get(row.get('canonical_slug')),
                    name=row.get('name'), catalog_created_at=datetime.fromtimestamp(row['created'],timezone.utc) if row.get('created') is not None else None,
                    context_length=row.get('context_length'),max_completion_tokens=(row.get('top_provider') or {}).get('max_completion_tokens'),
                    prompt_usd_per_token=token_rate(pricing,'prompt'),completion_usd_per_token=token_rate(pricing,'completion'),
                    input_modalities=arch.get('input_modalities'),output_modalities=arch.get('output_modalities'),
                    supported_parameters=row.get('supported_parameters'), pricing=Jsonb(pricing) if pricing is not None else None,
                    raw_payload=Jsonb(row),payload_sha256=digest(row),source_observed_at=data['observed'])
        _upsert(conn,'catalog_entries',values,['catalog_id'],counts)
        entries[row['id']]=conn.execute('SELECT catalog_entry_id FROM catalog_entries WHERE catalog_id=%s',(row['id'],)).fetchone()[0]
    for row in data['endpoints']:
        provider=row['provider_name']
        if provider not in providers:
            _upsert(conn,'providers',dict(provider_name=provider),['provider_name'],counts)
            providers[provider]=conn.execute('SELECT provider_id FROM providers WHERE provider_name=%s',(provider,)).fetchone()[0]
    for row in data['endpoints']:
        pricing=row.get('pricing')
        values=dict(catalog_entry_id=entries[row['model_id']],provider_id=providers[row['provider_name']],
                    tag=row.get('tag'),name=row.get('name'),service_tier=row.get('service_tier'),
                    context_length=row.get('context_length'),max_completion_tokens=row.get('max_completion_tokens'),
                    prompt_usd_per_token=token_rate(pricing,'prompt'),completion_usd_per_token=token_rate(pricing,'completion'),
                    supported_parameters=row.get('supported_parameters'), pricing=Jsonb(pricing) if pricing is not None else None,
                    raw_payload=Jsonb(row),payload_sha256=digest(row),source_observed_at=data['observed'])
        _upsert(conn,'serving_endpoints',values,['catalog_entry_id','provider_id','tag','name','service_tier'],counts)
    return counts


def run_sync(conn, fetch_snapshot, *, trigger='manual'):
    if not conn.autocommit:
        raise ValueError('Sync requires an autocommit connection for durable attempt logging')
    if trigger not in ('manual','schedule'):
        raise ValueError('Unsupported trigger')
    locked=conn.execute('SELECT pg_try_advisory_lock(6153,3)').fetchone()[0]
    try:
        run_id=conn.execute("INSERT INTO sync_runs(status,trigger,error_message) VALUES ('partial',%s,'attempt_in_progress') RETURNING run_id",(trigger,)).fetchone()[0]
        if not locked:
            conn.execute("UPDATE sync_runs SET status='failed',finished_at=clock_timestamp(),error_message='concurrent_run' WHERE run_id=%s",(run_id,))
            return dict(run_id=run_id,status='failed',records_fetched=0,records_inserted=0,records_updated=0,table_counts={},error_message='concurrent_run')
        # A session lock is held across fetch and commit. With no competing sync,
        # any older unfinished row belongs to a dead process, not a live writer.
        conn.execute("UPDATE sync_runs SET status='failed',finished_at=clock_timestamp(),error_message='interrupted_run_recovered',records_inserted=0,records_updated=0 WHERE finished_at IS NULL AND run_id<>%s",(run_id,))
        return _run_locked(conn,fetch_snapshot,run_id)
    finally:
        if locked and not conn.closed:
            conn.execute('SELECT pg_advisory_unlock(6153,3)')


def _run_locked(conn,fetch_snapshot,run_id):
    fetched=0
    try:
        data=fetch_snapshot()
        fetched=len(data['models'])+len(data['endpoints'])
        conn.execute('UPDATE sync_runs SET records_fetched=%s WHERE run_id=%s',(fetched,run_id))
        data=validate_snapshot(data)
        with conn.transaction():
            counts=_apply(conn,data)
            inserted=sum(x['inserted'] for x in counts.values())
            updated=sum(x['updated'] for x in counts.values())
            conn.execute("UPDATE sync_runs SET finished_at=clock_timestamp(),status='success',records_fetched=%s,records_inserted=%s,records_updated=%s,error_message=NULL,table_counts=%s WHERE run_id=%s",(fetched,inserted,updated,Jsonb(counts),run_id))
            fingerprint=digest(dict(models=sorted(data['models'],key=lambda r:r['id']),endpoints=sorted(data['endpoints'],key=digest)))
            conn.execute("INSERT INTO sync_state(source,last_success_run_id,observed_at,snapshot_sha256,mode) VALUES ('openrouter_catalog',%s,%s,%s,'full_snapshot_hash_diff') ON CONFLICT(source) DO UPDATE SET last_success_run_id=EXCLUDED.last_success_run_id,observed_at=EXCLUDED.observed_at,snapshot_sha256=EXCLUDED.snapshot_sha256",(run_id,data['observed'],fingerprint))
        return dict(run_id=run_id,status='success',records_fetched=fetched,records_inserted=inserted,records_updated=updated,table_counts=counts,error_message=None)
    except (Exception,KeyboardInterrupt) as error:
        safe='database_error' if isinstance(error,psycopg.Error) else 'interrupted' if isinstance(error,KeyboardInterrupt) else 'source_or_validation_error'
        status='partial' if isinstance(error,IncompleteSnapshot) and fetched else 'failed'
        if isinstance(error,IncompleteSnapshot): safe='incomplete_source_snapshot'
        # A commit may have succeeded even when its context exit was interrupted
        # or raised a driver error. Only an unfinished attempt may be finalized.
        row=conn.execute("UPDATE sync_runs SET finished_at=clock_timestamp(),status=%s,records_fetched=%s,records_inserted=0,records_updated=0,error_message=%s WHERE run_id=%s AND finished_at IS NULL RETURNING status,records_fetched,records_inserted,records_updated,table_counts,error_message",(status,fetched,safe,run_id)).fetchone()
        if row is None:
            row=conn.execute('SELECT status,records_fetched,records_inserted,records_updated,table_counts,error_message FROM sync_runs WHERE run_id=%s AND finished_at IS NOT NULL',(run_id,)).fetchone()
        if row is None:
            raise RuntimeError('Durable sync outcome unavailable') from None
        return dict(run_id=run_id,**dict(zip(('status','records_fetched','records_inserted','records_updated','table_counts','error_message'),row)))


def fetch_from_source():
    """Only the public OpenRouter metadata endpoint is selectable in production."""
    import tempfile
    from fetch import Client, collect
    with tempfile.TemporaryDirectory(prefix='m3-fetch-') as folder:
        summary = collect(Client(folder))
        return dict(models=json.loads((Path(folder)/'models.json').read_text())['data'],
                    endpoints=json.loads((Path(folder)/'endpoints.json').read_text())['data'],
                    observed=datetime.fromisoformat(summary['finished_at']), complete=summary['complete'])


def connection_parameters(uri):
    """Build libpq fields; never forward connection strings or local path/query overrides."""
    if not uri or not uri.isascii() or any(ord(c) <= 32 or ord(c) == 127 for c in uri):
        raise ValueError('A dedicated writer URI is required')
    target = urlsplit(uri)
    host, user = target.hostname or '', target.username or ''
    direct = re.fullmatch(r'db\.[a-z0-9]{20}\.supabase\.co', host) and user == 'catalog_sync_writer'
    pool = (re.fullmatch(r'aws-[0-9]+-[a-z0-9-]+\.pooler\.supabase\.com', host)
            and re.fullmatch(r'catalog_sync_writer\.[a-z0-9]{20}', user))
    if (target.scheme != 'postgresql' or not (pool or direct) or target.port not in (None, 5432)
            or target.path != '/postgres' or not target.password or '?' in uri or '#' in uri
            or uri.count('@') != 1 or re.search(r'%(?![0-9a-fA-F]{2})', uri)):
        raise ValueError('Unsupported database connection settings')
    password = unquote(target.password, errors='strict')
    if '\x00' in password:
        raise ValueError('Invalid database connection settings')
    ca = Path(__file__).resolve().parents[1] / 'db' / 'supabase-root-2021.crt'
    return dict(host=host, port=5432, dbname='postgres', user=user, password=password,
                sslmode='verify-full', sslrootcert=str(ca), gssencmode='disable',
                connect_timeout=10, autocommit=True, prepare_threshold=None)


def main(argv=None):
    import argparse
    import signal
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trigger', choices=('manual', 'schedule'), required=True)
    args = parser.parse_args(argv)
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt()
    try:
        # No service files, ambient libpq routing overrides, dotenv or .pgpass fallback.
        if any(k.startswith('PG') for k in os.environ):
            raise ValueError('Unexpected libpq environment')
        config = connection_parameters(os.environ.get('DATABASE_URL'))
        signal.signal(signal.SIGTERM, interrupted)
        with psycopg.connect(**config) as conn:
            if conn.execute('SELECT session_user, current_user').fetchone() != ('catalog_sync_writer', 'catalog_sync_writer'):
                raise ValueError('Unexpected database identity')
            conn.execute("SET search_path = pg_catalog, public, pg_temp; SET statement_timeout='120s'; SET lock_timeout='10s'")
            result = run_sync(conn, fetch_from_source, trigger=args.trigger)
        print(json.dumps(result, sort_keys=True))
        return 0 if result['status'] == 'success' and result['records_fetched'] > 0 else 1
    except (Exception, KeyboardInterrupt):
        print('Sync failed: check private configuration, run history and database availability. No audit row is guaranteed before connection.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
