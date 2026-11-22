"""Read-only freshness/status query. Uses APP_DATABASE_URL, never the owner."""
import json
import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv

SQL="""
SELECT max(finished_at) FILTER (WHERE status='success') AS last_success_at,
       max(finished_at) FILTER (WHERE status='success' AND records_inserted+records_updated>0) AS last_data_change_at,
       count(*) FILTER (WHERE started_at>=now()-interval '7 days') AS attempts_7d,
       count(*) FILTER (WHERE started_at>=now()-interval '7 days' AND status='success') AS successes_7d,
       coalesce(sum(records_inserted) FILTER (WHERE finished_at>=now()-interval '7 days' AND status='success'),0) AS inserts_7d,
       coalesce(sum(records_updated) FILTER (WHERE finished_at>=now()-interval '7 days' AND status='success'),0) AS updates_7d,
       coalesce(max(finished_at) FILTER (WHERE status='success') < now()-interval '24 hours',true) AS stale
FROM public.sync_runs
"""

def status(conn):
    with conn.transaction():
        conn.execute('SET TRANSACTION READ ONLY')
        user=conn.execute('SELECT current_user').fetchone()[0]
        if user!='app_reader': raise ValueError('app_reader required')
        conn.execute("SET LOCAL statement_timeout='10s'")
        row=conn.execute(SQL).fetchone()
    return dict(database_user=user,last_success_at=row[0].isoformat() if row[0] else None,
                last_data_change_at=row[1].isoformat() if row[1] else None,
                last_7_days=dict(attempts=row[2],successes=row[3],records_inserted=int(row[4]),records_updated=int(row[5])),
                stale=row[6],freshness_target_hours=24)

def main():
    try:
        load_dotenv(Path(__file__).resolve().parents[1]/'.env',override=False)
        url=os.environ.get('APP_DATABASE_URL')
        if not url: raise ValueError()
        with psycopg.connect(url,autocommit=True,connect_timeout=10) as conn:
            result=status(conn)
        print(json.dumps(result,sort_keys=True));return 0
    except Exception:
        print('Status failed: configure APP_DATABASE_URL privately as app_reader and check database access.');return 1

if __name__=='__main__':
    raise SystemExit(main())
