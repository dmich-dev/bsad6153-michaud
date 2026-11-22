"""Execute the reviewed quality-check SELECTs as app_reader; save dated results."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import psycopg
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]


def measure(conn):
    source=ROOT/'db/quality_checks.sql'
    parts=re.split(r'^-- check: ([a-z_]+)\s*$',source.read_text(),flags=re.M)
    checks={}
    with conn.transaction():
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        if conn.execute('SELECT current_user').fetchone()[0]!='app_reader': raise ValueError()
        conn.execute("SET LOCAL statement_timeout='10s'")
        for i in range(1,len(parts),2):
            cursor=conn.execute(parts[i+1],prepare=True)
            checks[parts[i]]=dict(columns=[c.name for c in cursor.description],rows=cursor.fetchall())
    return dict(measured_at=datetime.now(timezone.utc).isoformat(),database_user='app_reader',
                quality_sql_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),checks=checks)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scope',required=True,choices=['local_synthetic','live_supabase'])
    args=parser.parse_args(argv)
    try:
        load_dotenv(ROOT/'.env',override=False)
        if not os.environ.get('APP_DATABASE_URL'): raise ValueError()
        with psycopg.connect(os.environ['APP_DATABASE_URL'],autocommit=True,connect_timeout=10) as conn:
            result=measure(conn)
        result['evidence_scope']=args.scope
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as file:
            json.dump(result,file,default=str,indent=2,sort_keys=True);file.write('\n')
        print(json.dumps(dict(checks_executed=len(result['checks']),evidence_scope=args.scope)))
        return 0
    except Exception:
        print('Quality check failed: use private app_reader configuration and a new output path. No raw error is printed.')
        return 1


if __name__=='__main__':
    raise SystemExit(main())
