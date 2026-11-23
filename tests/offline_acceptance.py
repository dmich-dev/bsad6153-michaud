"""Reproducible assistant-run LOCAL acceptance capture, never student evidence.

Requires an EMPTY disposable m3_acceptance* PostgreSQL database on this host's
scratch Unix socket. Reads only explicit synthetic test DSNs from the environment.
It refuses cloud hosts and existing tables. Source credentials are never loaded.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psycopg

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from http_fixture import FixtureServer
from test_m3 import module

TABLES=['canonical_models','catalog_entries','providers','serving_endpoints']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    receipt=dict(evidence_scope='local_synthetic',actor='assistant automated execution',
                 started_at=datetime.now(timezone.utc).isoformat(),student_predictions_claimed=False,
                 genuine_scheduled_runs=0,steps=[])
    output=args.output_dir
    owner=os.environ['M3_TEST_DSN'];app=os.environ['M3_APP_DSN']
    env=dict(os.environ,DATABASE_URL=owner,APP_DATABASE_URL=app,OPENROUTER_API_KEY='')

    def run(path,*arguments,expected=0,override=None):
        command=[sys.executable,'-I','-B',str(ROOT/path),*arguments]
        done=subprocess.run(command,env=dict(env,**(override or {})),cwd=ROOT,capture_output=True,text=True,timeout=30)
        record=dict(command=[sys.executable,'-I','-B',path,*arguments],exit_code=done.returncode,
                    stdout=done.stdout,stderr=done.stderr)
        receipt['steps'].append(record)
        assert done.returncode==expected,(path,'unexpected exit')
        assert 'Traceback' not in done.stdout+done.stderr
        assert 'SYNTHETIC-SECRET-MUST-NOT-LOG' not in done.stdout+done.stderr
        return done

    with psycopg.connect(owner,autocommit=True) as conn:
        assert conn.info.dbname.startswith('m3_acceptance')
        assert conn.info.host.startswith('/home/hermes-worker/.hermes/cache/scratch/')
        assert conn.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public'").fetchone()[0]==0,'database must be EMPTY'
        receipt['server_version']=conn.execute('SHOW server_version').fetchone()[0]
        for source in ['db/schema.sql','db/milestone3.sql','db/roles.sql']:
            conn.execute((ROOT/source).read_text())
        run('scripts/check_db.py','--app')
        with psycopg.connect(app,autocommit=True) as reader:
            assert reader.execute('SELECT current_user').fetchone()[0]=='app_reader'
            privileges=[]
            for table in TABLES+['sync_runs']:
                for kind,query in [('SELECT','SELECT count(*) FROM '+table),('DELETE','DELETE FROM '+table),('INSERT','INSERT INTO '+table+' DEFAULT VALUES')]:
                    try:
                        values=reader.execute(query).fetchall()
                        assert kind=='SELECT'
                        privileges.append(dict(sql=query,result=values))
                    except psycopg.Error as error:
                        assert kind!='SELECT' and error.sqlstate=='42501'
                        privileges.append(dict(sql=query,result='permission denied',sqlstate=error.sqlstate))
            receipt['access_roles']=privileges
        with FixtureServer(statuses=[429,503]) as fixture:
            sync_args=['--local-fixture-url',fixture.url,'--page-size','2','--endpoint-models','2']
            predictions=[]
            def sync(label,status,fetched,inserted,updated,extra=(),override=None):
                # This prediction is recorded BEFORE invoking the real CLI.
                prediction=dict(label=label,status=status,records_fetched=fetched,records_inserted=inserted,records_updated=updated)
                predictions.append(prediction)
                done=run('ingest/sync.py',*sync_args,*extra,expected=0 if status=='success' else 1,override=override)
                actual=json.loads(done.stdout)
                for key in ['status','records_fetched','records_inserted','records_updated']:
                    assert actual[key]==prediction[key],(label,key)
                prediction['actual']=actual
                return actual
            first=sync('first_full_snapshot_with_429_and_503','success',7,12,0)
            baseline=output/'golden-before.json'
            run('evals/check_reference.py','--scope','local_synthetic','--output',str(baseline))
            replay=sync('immediate_rerun','success',7,0,0)
            fixture.data['models'][0]['context_length']=512000
            fixture.data['endpoints'][0]['pricing']['prompt']='0.000003'
            changed=sync('simulated_source_change','success',7,0,2)
            sync('unchanged_after_change','success',7,0,0)
            run('evals/check_reference.py','--scope','local_synthetic','--baseline',str(baseline),'--output',str(output/'golden-after.json'))
            fixture.unauthorized=True
            sync('synthetic_invalid_api_key','failed',0,0,0,override={'OPENROUTER_API_KEY':'SYNTHETIC-SECRET-MUST-NOT-LOG'})
            fixture.unauthorized=False
            fixture.statuses=[503,503,503]
            before_requests=len(fixture.requests)
            sync('bounded_three_attempt_outage','failed',0,0,0,extra=['--retry-attempts','3'])
            assert len(fixture.requests)-before_requests==3

            def fingerprints():
                return {table:hashlib.sha256(json.dumps(conn.execute('SELECT * FROM '+table+' ORDER BY 1').fetchall(),default=str).encode()).hexdigest() for table in TABLES}
            before=fingerprints()
            fixture.data['models'][0]['name']='Synthetic changed name for rollback and recovery'
            conn.execute("""CREATE FUNCTION local_reject() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'SYNTHETIC-SECRET-MUST-NOT-LOG'; END $$""")
            conn.execute('CREATE TRIGGER local_break BEFORE INSERT OR UPDATE ON serving_endpoints FOR EACH ROW EXECUTE FUNCTION local_reject()')
            sync('late_trigger_failure','failed',7,0,0)
            after=fingerprints()
            assert before==after
            receipt['rollback_fingerprints']=dict(before=before,after=after,identical=True)
            conn.execute('DROP TRIGGER local_break ON serving_endpoints')
            conn.execute("""CREATE FUNCTION local_pause() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN PERFORM pg_sleep(2); RETURN NEW; END $$""")
            conn.execute('CREATE TRIGGER local_pause BEFORE INSERT OR UPDATE ON serving_endpoints FOR EACH ROW EXECUTE FUNCTION local_pause()')
            command=[sys.executable,'-I','-B',str(ROOT/'ingest/sync.py'),*sync_args]
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    if conn.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event='PgSleep'").fetchone()[0]: break
                    time.sleep(.05)
                else: raise AssertionError('child did not enter real transaction')
                interrupted_id=conn.execute('SELECT max(run_id) FROM sync_runs').fetchone()[0]
                visible=conn.execute('SELECT status,records_fetched,records_inserted FROM sync_runs WHERE run_id=%s',(interrupted_id,)).fetchone()
                assert visible==('partial',7,0)
                assert fingerprints()==before
                child.kill();stdout,stderr=child.communicate(timeout=5)
                assert child.returncode<0
                receipt['interruption']=dict(action='Actual SIGKILL of CLI while PostgreSQL transaction was paused',run_id=interrupted_id,
                    visible_before_kill=visible,process_exit_code=child.returncode,stdout=stdout.decode(),stderr=stderr.decode())
            finally:
                if child.poll() is None: child.kill();child.communicate(timeout=5)
            conn.execute('DROP TRIGGER local_pause ON serving_endpoints')
            assert fingerprints()==before
            sync('recovery_after_process_kill','success',7,0,1)
            recovered=conn.execute('SELECT status,error_message,records_inserted,records_updated FROM sync_runs WHERE run_id=%s',(interrupted_id,)).fetchone()
            assert recovered==('failed','interrupted_run_recovered',0,0)
            receipt['interruption']['row_after_recovery']=recovered
            receipt['predictions']=predictions
            receipt['http_requests']=fixture.requests
        count_before=conn.execute('SELECT count(*) FROM sync_runs').fetchone()[0]
        run('ingest/sync.py',expected=1,override={'DATABASE_URL':'invalid DSN SYNTHETIC-SECRET-MUST-NOT-LOG'})
        assert conn.execute('SELECT count(*) FROM sync_runs').fetchone()[0]==count_before
        receipt['unreachable_database_attempt_logged']=False
        receipt['unreachable_database_note']='No connection means no row can be guaranteed. CLI/CI failure is the fallback evidence.'
        run('scripts/status.py')
        run('scripts/quality_report.py','--scope','local_synthetic','--output',str(output/'quality-local.json'))
        cursor=conn.execute('SELECT run_id,started_at,finished_at,status,records_fetched,records_inserted,records_updated,error_message,trigger,table_counts FROM sync_runs ORDER BY run_id')
        receipt['sync_runs']=dict(columns=[c.name for c in cursor.description],rows=cursor.fetchall())
        receipt['source_hashes']={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for folder in ['ingest','scripts','db','evals','tests'] for path in (ROOT/folder).rglob('*') if path.is_file() and '__pycache__' not in path.parts}
    receipt['finished_at']=datetime.now(timezone.utc).isoformat();receipt['status']='PASS'
    with (output/'acceptance.json').open('x') as file:
        json.dump(receipt,file,default=str,indent=2,sort_keys=True);file.write('\n')
    print(json.dumps(dict(status='PASS',steps=len(receipt['steps']),sync_attempts=len(receipt['sync_runs']['rows']),
                          genuine_scheduled_runs=0,output=str(output))))


if __name__=='__main__':
    main()
