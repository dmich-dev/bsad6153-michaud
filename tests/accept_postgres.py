"""Disposable PostgreSQL 17 acceptance; never opens a caller-supplied database.

Run as an unprivileged user: python -I -B tests/accept_postgres.py --pg-bin /path/to/bin
An installation with initdb, pg_ctl and its matching libraries is required.
"""
import argparse
import os
from pathlib import Path

import subprocess
import sys
import tempfile
import unittest

import psycopg
from psycopg import errors

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'ingest'), str(ROOT/'tests')]
from fixtures import snapshot
import sync


def connection(user):
    return psycopg.connect(host=str(SOCKET), port=55438, dbname='postgres', user=user,
                           autocommit=True, connect_timeout=3, passfile=str(SOCKET/'no-passfile'))


class WriterAcceptance(unittest.TestCase):
    def test_writer_and_reader(self):
        # Exercise the provisioning path as a database owner with CREATEROLE,
        # not as a PostgreSQL superuser. The initial fixture admin only bootstraps it.
        with connection('fixture_admin') as admin:
            admin.execute('CREATE ROLE fixture_owner LOGIN CREATEROLE NOSUPERUSER')
            admin.execute('ALTER DATABASE postgres OWNER TO fixture_owner')
        with connection('fixture_owner') as owner:
            for path in ('schema', 'milestone3', 'roles'):
                owner.execute((ROOT/'db'/f'{path}.sql').read_text())
            writer_sql = ROOT/'db/sync_writer.sql'
            self.assertTrue(writer_sql.is_file(), 'dedicated writer provisioning is missing')
            # Refuse inherited privilege; rollback rather than changing PUBLIC grants.
            owner.execute('GRANT CREATE ON SCHEMA public TO PUBLIC')
            with self.assertRaises(errors.RaiseException):
                owner.execute(writer_sql.read_text())
            owner.execute('ROLLBACK')
            self.assertIsNone(owner.execute("SELECT to_regrole('catalog_sync_writer')").fetchone()[0])
            owner.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
            owner.execute('REVOKE CONNECT ON DATABASE postgres FROM PUBLIC')
            owner.execute(writer_sql.read_text())
            self.assertTrue(owner.execute("SELECT has_database_privilege('catalog_sync_writer',current_database(),'CONNECT')").fetchone()[0])
            owner.execute('GRANT CONNECT ON DATABASE postgres TO app_reader')
            with self.assertRaises(errors.DuplicateObject):
                owner.execute(writer_sql.read_text())
            owner.execute('ROLLBACK')
            owner.execute('CREATE ROLE acl_recipient NOLOGIN; CREATE TABLE unrelated_fixture (n int)')
            with connection('catalog_sync_writer') as writer, connection('app_reader') as reader:
                self.assertEqual(writer.execute('SELECT current_user,session_user').fetchone(), ('catalog_sync_writer',)*2)
                writer.execute('SET search_path = pg_catalog, public, pg_temp')
                data = snapshot()
                first = sync.run_sync(writer, lambda: data)
                self.assertEqual((first['status'], first['records_inserted'], first['records_updated']), ('success',12,0))
                same = sync.run_sync(writer, lambda: data)
                self.assertEqual((same['status'], same['records_fetched'], same['records_inserted'], same['records_updated']), ('success',7,0,0))
                data['models'][0]['context_length'] += 1

                data['endpoints'][0]['context_length'] += 1
                changed = sync.run_sync(writer, lambda: data)
                self.assertEqual((changed['status'], changed['records_updated']), ('success',2))
                failed = sync.run_sync(writer, lambda: dict(data, complete=False))
                self.assertEqual((failed['status'],failed['records_inserted'],failed['records_updated']), ('partial',0,0))
                self.assertEqual(owner.execute('SELECT last_success_run_id FROM sync_state').fetchone(), (changed['run_id'],))
                self.assertEqual(reader.execute('SELECT status,trigger FROM sync_runs ORDER BY run_id').fetchall(), [('success','manual')]*3+[('partial','manual')])
                self.assertEqual(reader.execute('SELECT count(*) FROM catalog_entries').fetchone(), (4,))
                flags=owner.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolinherit,rolreplication,rolbypassrls FROM pg_roles WHERE rolname='catalog_sync_writer'").fetchone()
                self.assertEqual(flags,(False,)*6)
                self.assertEqual(owner.execute("SELECT count(*) FROM pg_auth_members WHERE member='catalog_sync_writer'::regrole").fetchone(), (0,))
                for connection_, statements in [(writer, [
                    'CREATE SCHEMA forbidden', 'CREATE TABLE public.forbidden(n int)',
                    'ALTER TABLE public.providers ADD COLUMN bad int', 'DROP TABLE public.sync_state',
                    'UPDATE providers SET provider_name=provider_name', 'UPDATE sync_runs SET trigger=trigger',
                    'UPDATE catalog_entries SET first_seen_at=first_seen_at', 'DELETE FROM catalog_entries',
                    'TRUNCATE sync_runs CASCADE', 'INSERT INTO unrelated_fixture VALUES (1)',
                    'CREATE ROLE forbidden_role', 'GRANT app_reader TO catalog_sync_writer', 'SET ROLE fixture_admin',
                ]), (reader, ['SET ROLE catalog_sync_writer','SELECT * FROM sync_state',
                              'DELETE FROM providers','INSERT INTO sync_runs(status,trigger) VALUES (\'partial\',\'manual\')'])]:
                    for statement in statements:
                        with self.subTest(statement=statement), self.assertRaises(errors.InsufficientPrivilege):
                            connection_.execute(statement)
                # PostgreSQL may WARN (rather than error) on an ineffective GRANT.
                try:
                    writer.execute('GRANT SELECT ON catalog_entries TO acl_recipient')
                except errors.InsufficientPrivilege:
                    pass
                self.assertFalse(owner.execute("SELECT has_table_privilege('acl_recipient','catalog_entries','SELECT')").fetchone()[0])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pg-bin', type=Path, required=True)
    args=parser.parse_args()
    if os.geteuid()==0:
        parser.error('run as an unprivileged local OS user')
    if any(k.startswith('PG') for k in os.environ):
        parser.error('remove ambient libpq settings before running this disposable test')
    with tempfile.TemporaryDirectory(prefix='m3pg-') as temp:
        global SOCKET
        root=Path(temp).resolve(); SOCKET=root/'s'; SOCKET.mkdir(mode=0o700)
        data=root/'data'
        env={'PATH':os.defpath,'HOME':str(root),'TMPDIR':str(root),'LANG':'C',
             **({'LD_LIBRARY_PATH':os.environ['LD_LIBRARY_PATH']} if 'LD_LIBRARY_PATH' in os.environ else {})}
        def pg(name,*args_):
            subprocess.run([str(args.pg_bin.resolve()/name),*map(str,args_)],env=env,check=True,
                           stdout=subprocess.DEVNULL)
        pg('initdb','-D',data,'-U','fixture_admin','--auth-local=trust','--auth-host=reject','--no-locale','--encoding=UTF8')
        # Paths come from tempfile; pass them to postgres as settings, not shell text.
        with (data/'postgresql.conf').open('a') as config:
            config.write("\nlisten_addresses=''\nport=55438\nunix_socket_directories='"+str(SOCKET).replace("'","''")+"'\n")
        pg('pg_ctl','-D',data,'-l',root/'pg.log','-w','start')
        try:
            result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WriterAcceptance))
        finally:
            pg('pg_ctl','-D',data,'-m','fast','-w','stop')
        return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
