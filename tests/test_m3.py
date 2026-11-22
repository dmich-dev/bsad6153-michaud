"""Part A-D real PostgreSQL and loopback integration tests."""
import json
import os
import psycopg
import m3_support
from m3_support import ROOT,TABLES,module

class M3DatabaseTests(m3_support.M3Case):
    def test_full_snapshot_inserts_then_replays_with_zero_updates_then_changes_only_changed_rows(self):
            from fixtures import snapshot
            self.migrate()
            sync = self.sync()
            data = snapshot()
            first = sync.run_sync(self.conn, lambda: data)
            self.assertEqual((first['status'], first['records_fetched'], first['records_inserted'], first['records_updated']), ('success',7,12,0))
            before = self.conn.execute('SELECT catalog_id,last_updated_at FROM catalog_entries ORDER BY 1').fetchall()
            again = sync.run_sync(self.conn, lambda: data)
            if again['records_updated']:
                self.fail('an identical logical snapshot must not spuriously update rows')
            self.assertEqual((again['records_inserted'],again['records_updated']), (0,0))
            self.assertEqual(before,self.conn.execute('SELECT catalog_id,last_updated_at FROM catalog_entries ORDER BY 1').fetchall())
            data['models'][0]['context_length']=512000
            data['endpoints'][0]['pricing']['prompt']='0.000003'
            changed=sync.run_sync(self.conn,lambda:data)
            self.assertEqual((changed['records_inserted'],changed['records_updated']), (0,2))
            after=self.conn.execute('SELECT catalog_id,last_updated_at FROM catalog_entries ORDER BY 1').fetchall()
            self.assertGreater(after[0][1],before[0][1])
            self.assertEqual(after[1:],before[1:])
            self.assertEqual(self.conn.execute("SELECT count(*) FROM sync_runs WHERE status='success'").fetchone()[0],3)
            self.assertEqual(self.conn.execute('SELECT mode FROM sync_state').fetchone()[0],'full_snapshot_hash_diff')

    def test_late_database_failure_rolls_back_and_logs_safe_zero_committed_counts(self):
            from fixtures import snapshot
            self.migrate()
            sync=self.sync()
            self.conn.execute("""CREATE FUNCTION reject_route() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'synthetic-password-DO-NOT-LOG'; END $$""")
            self.conn.execute('CREATE TRIGGER break_test BEFORE INSERT ON serving_endpoints FOR EACH ROW EXECUTE FUNCTION reject_route()')
            result=sync.run_sync(self.conn, snapshot)
            self.assertEqual((result['status'],result['records_fetched'],result['records_inserted'],result['records_updated']),('failed',7,0,0))
            self.assertEqual([self.conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in TABLES],[0,0,0,0])
            row=self.conn.execute('SELECT status,finished_at,error_message FROM sync_runs').fetchone()
            self.assertEqual(row[0],'failed')
            self.assertIsNotNone(row[1])
            self.assertEqual(row[2],'database_error')
            self.assertNotIn('synthetic-password',json.dumps(result))
            self.assertEqual(self.conn.execute('SELECT count(*) FROM sync_state').fetchone()[0],0)
            self.conn.execute('DROP TRIGGER break_test ON serving_endpoints')
            self.assertEqual(sync.run_sync(self.conn,snapshot)['records_inserted'],12)

    def test_real_commit_boundary_preserves_success_after_interrupt_or_driver_error(self):
            from contextlib import contextmanager
            from fixtures import snapshot
            self.migrate()
            sync=self.sync()
            real=self.conn

            class CommitBoundary:
                def __getattr__(self,name): return getattr(real,name)

                @contextmanager
                def transaction(self):
                    with real.transaction():
                        yield
                        if timing=='rollback': raise error('SYNTHETIC boundary failure')
                    # The real PostgreSQL commit has completed before raising.
                    if timing=='committed': raise error('SYNTHETIC boundary failure')

            for timing,error in [('healthy',None),('rollback',KeyboardInterrupt),
                                 ('rollback',psycopg.OperationalError),('committed',KeyboardInterrupt),
                                 ('committed',psycopg.OperationalError)]:
                with self.subTest(timing=timing,error=error):
                    self.conn.execute('TRUNCATE serving_endpoints,catalog_entries,canonical_models,providers,sync_state,sync_runs RESTART IDENTITY CASCADE')
                    result=sync.run_sync(CommitBoundary(),snapshot)
                    # Read back through another actual database session, not the wrapper.
                    with psycopg.connect(os.environ['M3_TEST_DSN'],autocommit=True) as observer:
                        row=observer.execute('SELECT status,records_fetched,records_inserted,records_updated,table_counts,error_message,finished_at FROM sync_runs WHERE run_id=%s',(result['run_id'],)).fetchone()
                        committed=observer.execute('SELECT count(*) FROM catalog_entries').fetchone()[0]
                        checkpoint=observer.execute('SELECT last_success_run_id FROM sync_state').fetchone()
                    expected='failed' if timing=='rollback' else 'success'
                    self.assertEqual(row[0],expected,'durable committed success must not be rewritten as failed')
                    self.assertEqual(result['status'],expected)
                    self.assertEqual(tuple(result[k] for k in ('status','records_fetched','records_inserted','records_updated','table_counts','error_message')),row[:6])
                    self.assertIsNotNone(row[6])
                    if timing=='rollback':
                        self.assertEqual((committed,checkpoint,result['records_inserted'],result['records_updated']),(0,None,0,0))
                        self.assertEqual(result['error_message'],'interrupted' if error==KeyboardInterrupt else 'database_error')
                    else:
                        self.assertEqual((committed,checkpoint,result['records_inserted'],result['records_updated']),(4,(result['run_id'],),12,0))
                        self.assertEqual(sum(c['inserted'] for c in result['table_counts'].values()),12)
                        self.assertIsNone(result['error_message'])

    def test_existing_terminal_outcomes_are_read_back_without_rewriting_and_missing_is_not_fabricated(self):
            from fixtures import snapshot
            self.migrate()
            sync=self.sync()
            success=sync.run_sync(self.conn,snapshot)
            run_ids=[success['run_id']]
            for status in ('partial','failed'):
                run_ids.append(self.conn.execute("INSERT INTO sync_runs(status,trigger,finished_at,records_fetched,error_message) VALUES (%s,'manual',clock_timestamp(),29,'SYNTHETIC prior terminal result') RETURNING run_id",(status,)).fetchone()[0])
            def interrupted(): raise KeyboardInterrupt()
            for run_id in run_ids:
                with self.subTest(run_id=run_id):
                    before=self.conn.execute('SELECT to_jsonb(sync_runs) FROM sync_runs WHERE run_id=%s',(run_id,)).fetchone()[0]
                    result=sync._run_locked(self.conn,interrupted,run_id)
                    after=self.conn.execute('SELECT to_jsonb(sync_runs) FROM sync_runs WHERE run_id=%s',(run_id,)).fetchone()[0]
                    self.assertEqual(before,after)
                    self.assertEqual(result,{k:before[k] for k in ('run_id','status','records_fetched','records_inserted','records_updated','table_counts','error_message')})
            with self.assertRaisesRegex(RuntimeError,'Durable sync outcome unavailable'):
                sync._run_locked(self.conn,interrupted,999999)

    def test_incomplete_or_malformed_snapshot_never_commits_rows_or_advances_checkpoint(self):
            from fixtures import snapshot
            self.migrate()
            sync=self.sync()
            data=snapshot()
            data['complete']=False
            result=sync.run_sync(self.conn,lambda:data)
            self.assertEqual((result['status'],result['records_inserted']),('partial',0))
            for case in ['bad_id','bad_type','nan','conflict','orphan','naive']:
                with self.subTest(case=case):
                    data=snapshot()
                    if case=='bad_id': data['models'][0]['id']=' synthetic/alpha'
                    elif case=='bad_type': data['models'][0]['context_length']=True
                    elif case=='nan': data['models'][0]['pricing']['prompt']='NaN'
                    elif case=='conflict': data['models'].append(dict(data['models'][0],name='conflict'))
                    elif case=='orphan': data['endpoints'][0]['model_id']='synthetic/no-parent'
                    elif case=='naive': data['observed']=data['observed'].replace(tzinfo=None)
                    result=sync.run_sync(self.conn,lambda:data)
                    self.assertEqual(result['status'],'failed')
            self.assertEqual(self.conn.execute('SELECT count(*) FROM catalog_entries').fetchone()[0],0)
            self.assertEqual(self.conn.execute('SELECT count(*) FROM sync_state').fetchone()[0],0)
            self.assertEqual(self.conn.execute('SELECT count(*) FROM sync_runs').fetchone()[0],7)

    def test_process_kill_mid_transaction_recovers_unfinished_attempt_without_partial_rows(self):
            import subprocess,sys,time
            from fixtures import snapshot
            self.migrate()
            sync=self.sync()
            self.conn.execute("""CREATE FUNCTION pause_route() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN PERFORM pg_sleep(2); RETURN NEW; END $$""")
            self.conn.execute('CREATE TRIGGER pause_test BEFORE INSERT ON serving_endpoints FOR EACH ROW EXECUTE FUNCTION pause_route()')
            program="""import sys,os;sys.path.insert(0,os.getcwd()+'/tests');from test_m3 import module;from fixtures import snapshot;import psycopg;c=psycopg.connect(os.environ['M3_TEST_DSN'],autocommit=True);module('ingest/sync.py','child_sync').run_sync(c,snapshot)"""
            child=subprocess.Popen([sys.executable,'-I','-B','-c',program],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            def cleanup_child():
                if child.poll() is None: child.kill()
                child.communicate(timeout=5)
            self.addCleanup(cleanup_child)
            deadline=time.monotonic()+10
            while time.monotonic()<deadline:
                if self.conn.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event='PgSleep'").fetchone()[0]: break
                time.sleep(.05)
            else: self.fail('child never reached the intentionally paused real transaction')
            self.assertEqual(self.conn.execute('SELECT count(*) FROM catalog_entries').fetchone()[0],0)
            self.assertEqual(self.conn.execute('SELECT records_fetched FROM sync_runs').fetchone()[0],7,'fetched count must survive an abrupt process death')
            child.kill(); child.communicate(timeout=5)
            self.assertEqual(self.conn.execute('SELECT count(*) FROM serving_endpoints').fetchone()[0],0)
            self.conn.execute('DROP TRIGGER pause_test ON serving_endpoints')
            result=sync.run_sync(self.conn,snapshot)
            self.assertEqual(result['records_inserted'],12)
            rows=self.conn.execute('SELECT status,error_message,records_inserted FROM sync_runs ORDER BY run_id').fetchall()
            self.assertEqual(rows[0],('failed','interrupted_run_recovered',0))
            self.assertEqual(rows[1],('success',None,12))

    def test_concurrent_attempt_is_logged_failed_without_fetch_or_data_changes(self):
            from fixtures import snapshot
            self.migrate()
            sync=self.sync()
            with psycopg.connect(os.environ['M3_TEST_DSN'],autocommit=True) as other:
                other.execute('SELECT pg_advisory_lock(6153,3)')
                result=sync.run_sync(self.conn,lambda:self.fail('contended attempt must not fetch'))
                self.assertEqual((result['status'],result['error_message']),('failed','concurrent_run'))
            self.assertEqual(self.conn.execute('SELECT count(*) FROM catalog_entries').fetchone()[0],0)
            self.assertEqual(sync.run_sync(self.conn,snapshot)['status'],'success')

    def test_cli_fetches_paged_http_retries_429_and_503_and_replays_cleanly(self):
            from http_fixture import FixtureServer
            self.migrate()
            with FixtureServer(statuses=[429,503]) as fixture:
                args=['--local-fixture-url',fixture.url,'--page-size','2','--endpoint-models','2']
                first=self.cli('ingest/sync.py',*args)
                self.assertEqual(first.returncode,0,first.stdout+first.stderr)
                self.assertIn('records_inserted',first.stdout,'sync CLI must run, not be a no-op')
                self.assertEqual(json.loads(first.stdout)['records_inserted'],12)
                second=self.cli('ingest/sync.py',*args)
                self.assertEqual(second.returncode,0,second.stdout+second.stderr)
                self.assertEqual(json.loads(second.stdout)['records_updated'],0)
                self.assertEqual(json.loads(second.stdout)['records_inserted'],0)
                self.assertEqual(fixture.statuses,[])
                self.assertTrue(all(set(r['query'])=={'output_modalities','limit','offset'} for r in fixture.requests if r['path']=='/api/v1/models'))
            self.assertEqual(self.conn.execute('SELECT count(*) FROM sync_runs').fetchone()[0],2)

    def test_cli_bad_key_and_malformed_connection_never_emit_credentials(self):
            from http_fixture import FixtureServer
            self.migrate()
            with FixtureServer(unauthorized=True) as fixture:
                result=self.cli('ingest/sync.py','--local-fixture-url',fixture.url,
                                env={'OPENROUTER_API_KEY':'SYNTHETIC-KEY-MUST-NOT-LOG'})
                self.assertNotEqual(result.returncode,0)
                self.assertNotIn('SYNTHETIC-KEY-MUST-NOT-LOG',result.stdout+result.stderr)
            self.assertEqual(self.conn.execute('SELECT status,records_inserted FROM sync_runs').fetchone(),('failed',0))
            result=self.cli('ingest/sync.py',env={'DATABASE_URL':'postgresql://u:SYNTHETIC-PASSWORD@127.0.0.1:bad/m3'})
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn('SYNTHETIC-PASSWORD',result.stdout+result.stderr)
            self.assertNotIn('Traceback',result.stdout+result.stderr)

    def test_status_cli_and_existing_app_connectivity_use_real_app_reader(self):
            from fixtures import snapshot
            self.migrate()
            self.conn.execute((ROOT/'db/roles.sql').read_text())
            self.sync().run_sync(self.conn,snapshot)
            checked=self.cli('scripts/check_db.py','--app')
            self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
            self.assertIn('Database user: app_reader',checked.stdout)
            result=self.cli('scripts/status.py')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads(result.stdout)
            self.assertEqual(data['database_user'],'app_reader')
            self.assertEqual(data['last_7_days']['records_inserted'],12)
            self.assertIsNotNone(data['last_success_at'])
            self.assertIsNotNone(data['last_data_change_at'])
            rejected=self.cli('scripts/status.py',env={'APP_DATABASE_URL':os.environ['M3_TEST_DSN']})
            self.assertNotEqual(rejected.returncode,0)

    def test_roles_script_refuses_elevated_existing_role_or_public_write_instead_of_broad_mutation(self):
            self.migrate()
            roles=(ROOT/'db/roles.sql').read_text()
            self.conn.execute(roles)
            self.conn.execute('ALTER ROLE app_reader REPLICATION')
            try:
                with self.assertRaises(psycopg.errors.RaiseException): self.conn.execute(roles)
            finally:
                self.conn.execute('ROLLBACK');self.conn.execute('ALTER ROLE app_reader NOREPLICATION')
            self.conn.execute('GRANT INSERT ON catalog_entries TO PUBLIC')
            try:
                with self.assertRaises(psycopg.errors.RaiseException): self.conn.execute(roles)
            finally:
                self.conn.execute('ROLLBACK');self.conn.execute('REVOKE INSERT ON catalog_entries FROM PUBLIC')
            self.conn.execute(roles)

    def test_roles_remove_direct_and_refuse_public_column_write_or_reference_grants(self):
            self.migrate()
            roles=(ROOT/'db/roles.sql').read_text()
            self.conn.execute(roles)
            actions={
                'INSERT': "INSERT INTO providers(provider_name) VALUES ('SYNTHETIC column grant')",
                'UPDATE': 'UPDATE providers SET provider_name=provider_name',
                'REFERENCES': 'CREATE TABLE m3_column_probe.synthetic_reference (name text REFERENCES public.providers(provider_name))',
            }
            self.conn.execute('CREATE ROLE m3_unrelated_acl NOLOGIN')
            self.addCleanup(lambda:self.conn.execute('DROP ROLE m3_unrelated_acl'))
            self.conn.execute('CREATE SCHEMA m3_column_probe AUTHORIZATION app_reader')
            self.addCleanup(lambda:self.conn.execute('DROP SCHEMA m3_column_probe CASCADE'))
            self.conn.execute('GRANT SELECT(provider_name) ON providers TO m3_unrelated_acl')
            self.addCleanup(lambda:self.conn.execute('REVOKE SELECT(provider_name) ON providers FROM m3_unrelated_acl'))
            for grantee in ('app_reader','PUBLIC'):
                for privilege,action in actions.items():
                    with self.subTest(grantee=grantee,privilege=privilege):
                        grant=f'{privilege}(provider_name) ON providers'
                        self.conn.execute(f'GRANT {grant} TO {grantee}')
                        acl=self.conn.execute("SELECT attacl::text FROM pg_attribute WHERE attrelid='providers'::regclass AND attname='provider_name'").fetchone()
                        try:
                            # This is an executable privilege, not merely an ACL string.
                            with psycopg.connect(os.environ['M3_APP_DSN'],autocommit=True) as app:
                                app.execute(action)
                            self.conn.execute('DROP TABLE IF EXISTS m3_column_probe.synthetic_reference')
                            self.assertTrue(self.conn.execute("SELECT has_column_privilege('app_reader','providers','provider_name',%s)",(privilege,)).fetchone()[0])
                            if grantee=='PUBLIC':
                                try:
                                    with self.assertRaises(psycopg.errors.RaiseException): self.conn.execute(roles)
                                finally:
                                    self.conn.execute('ROLLBACK')
                                self.assertEqual(self.conn.execute("SELECT attacl::text FROM pg_attribute WHERE attrelid='providers'::regclass AND attname='provider_name'").fetchone(),acl,'reject without changing PUBLIC or unrelated ACLs')
                            else:
                                # PostgreSQL table REVOKE also removes direct column grants.
                                self.conn.execute(roles)
                                with psycopg.connect(os.environ['M3_APP_DSN'],autocommit=True) as app:
                                    with self.assertRaises(psycopg.errors.InsufficientPrivilege): app.execute(action)
                                self.assertTrue(self.conn.execute("SELECT has_column_privilege('m3_unrelated_acl','providers','provider_name','SELECT')").fetchone()[0])
                        finally:
                            self.conn.execute('ROLLBACK')
                            self.conn.execute('DROP TABLE IF EXISTS m3_column_probe.synthetic_reference')
                            self.conn.execute(f'REVOKE {grant} FROM {grantee}')
                            self.conn.execute('DELETE FROM providers')
                        self.conn.execute(roles)
                        with psycopg.connect(os.environ['M3_APP_DSN'],autocommit=True) as app:
                            self.assertEqual(app.execute('SELECT count(*) FROM providers').fetchone(),(0,))
                            with self.assertRaises(psycopg.errors.InsufficientPrivilege): app.execute(action)

    def test_roles_refuse_existing_database_schema_and_public_relation_ownership(self):
            from psycopg import sql
            self.migrate()
            roles=(ROOT/'db/roles.sql').read_text()
            self.conn.execute(roles)
            owner=self.conn.execute('SELECT current_user').fetchone()[0]
            database=self.conn.info.dbname
            self.conn.execute('CREATE VIEW public.m3_owned_view AS SELECT 1 AS value')
            self.conn.execute('CREATE SEQUENCE public.m3_owned_sequence')
            cases=[('DATABASE',database,sql.SQL('ALTER DATABASE {} CONNECTION LIMIT -1').format(sql.Identifier(database))),
                   ('SCHEMA','public',sql.SQL('DROP SCHEMA public CASCADE'))]
            cases += [('TABLE',t,sql.SQL('DROP TABLE public.{} CASCADE').format(sql.Identifier(t))) for t in TABLES+['sync_runs','sync_state']]
            cases += [('VIEW','m3_owned_view',sql.SQL('DROP VIEW public.m3_owned_view')),
                      ('SEQUENCE','m3_owned_sequence',sql.SQL('DROP SEQUENCE public.m3_owned_sequence'))]
            for kind,name,forbidden in cases:
                with self.subTest(kind=kind,name=name):
                    change=sql.SQL('ALTER {} {} OWNER TO {}').format(sql.SQL(kind),sql.Identifier(name),sql.Identifier('app_reader'))
                    restore=sql.SQL('ALTER {} {} OWNER TO {}').format(sql.SQL(kind),sql.Identifier(name),sql.Identifier(owner))
                    self.conn.execute(change)
                    try:
                        # Remove ordinary ACL privileges: ownership still authorizes DDL.
                        if kind=='SCHEMA': self.conn.execute('REVOKE ALL ON SCHEMA public FROM app_reader')
                        elif kind not in ('DATABASE',):
                            self.conn.execute(sql.SQL('REVOKE ALL ON {} {} FROM app_reader').format(sql.SQL('SEQUENCE' if kind=='SEQUENCE' else 'TABLE'),sql.Identifier(name)))
                        with self.assertRaisesRegex(RuntimeError,'rollback synthetic ownership proof'):
                            with self.conn.transaction():
                                self.conn.execute('SET LOCAL ROLE app_reader')
                                self.conn.execute(forbidden)
                                raise RuntimeError('rollback synthetic ownership proof')
                        try:
                            with self.assertRaises(psycopg.errors.RaiseException): self.conn.execute(roles)
                        finally:
                            self.conn.execute('ROLLBACK')
                        # Refusal is not a silent ownership reassignment.
                        self.assertTrue(self.conn.execute("SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=%s AND datdba='app_reader'::regrole) OR EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=%s AND nspowner='app_reader'::regrole) OR EXISTS(SELECT 1 FROM pg_class WHERE relnamespace='public'::regnamespace AND relname=%s AND relowner='app_reader'::regrole)",(name,name,name)).fetchone()[0])
                    finally:
                        self.conn.execute('ROLLBACK')
                        self.conn.execute(restore)
                        self.conn.execute(roles)
            with psycopg.connect(os.environ['M3_APP_DSN'],autocommit=True) as app:
                self.assertEqual(app.execute('SELECT count(*) FROM providers').fetchone(),(0,))
                for action in ('DROP TABLE providers CASCADE','ALTER TABLE providers ADD COLUMN not_allowed int','ALTER SCHEMA public RENAME TO not_allowed'):
                    with self.subTest(action=action),self.assertRaises(psycopg.errors.InsufficientPrivilege): app.execute(action)

    def test_run_schema_enforces_status_trigger_counts_and_reader_privileges(self):
            self.migrate()
            self.conn.execute((ROOT / 'db/roles.sql').read_text())
            with psycopg.connect(os.environ['M3_APP_DSN'], autocommit=True) as app:
                self.assertEqual(app.execute('SELECT current_user').fetchone()[0], 'app_reader')
                for t in TABLES + ['sync_runs']:
                    self.assertEqual(app.execute('SELECT count(*) FROM ' + t).fetchone(), (0,))
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        app.execute('DELETE FROM ' + t)
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        app.execute('INSERT INTO ' + t + ' DEFAULT VALUES')
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    app.execute('SELECT * FROM sync_state')
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    app.execute('CREATE TABLE public.not_allowed (x int)')
            for column, value in [('status', 'bogus'), ('trigger', 'push'), ('records_fetched', -1)]:
                with self.assertRaises(psycopg.errors.CheckViolation):
                    if column == 'status':
                        self.conn.execute("INSERT INTO sync_runs(status,trigger) VALUES (%s,'manual')", (value,))
                    elif column == 'trigger':
                        self.conn.execute("INSERT INTO sync_runs(status,trigger) VALUES ('failed',%s)", (value,))
                    else:
                        self.conn.execute("INSERT INTO sync_runs(status,trigger,records_fetched) VALUES ('failed','manual',%s)", (value,))
