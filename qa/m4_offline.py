"""Synthetic only. No local dotenv or real database. Database configuration is removed for this suite."""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import psycopg
import streamlit as st
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent.parent / 'app'
sys.path.insert(0, str(APP))
import catalogue as c

ROLE = 'app_reader.' + 'a' * 20
HOST = 'example.pooler.supabase.com'
SYN = f'postgresql://{ROLE}:synthetic@{HOST}:5432/postgres'


def setUpModule():
    scrubbed = {k: v for k, v in os.environ.items() if k not in {'APP_DATABASE_URL', 'DATABASE_URL'} and not k.startswith('PG')}
    clean = patch.dict(os.environ, scrubbed, clear=True)
    clean.start()
    unittest.addModuleCleanup(clean.stop)


def view():
    return AppTest.from_file(str(APP/'streamlit_app.py'), default_timeout=15).run()


class Isolated(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()
        self.addCleanup(st.cache_data.clear)


class Page(Isolated):
    def test_unconfigured_is_public_friendly_and_independent_of_admin(self):
        with patch.dict(os.environ, {'DATABASE_URL':'synthetic-invalid-admin-value'}, clear=True):
            page = view()
        self.assertFalse(page.exception)
        self.assertEqual(page.title[0].value, 'Model catalogue')
        self.assertTrue(any('unavailable' in w.value.lower() for w in page.warning))
        self.assertFalse(page.text_input)
        text = ' '.join(e.value for e in [*page.markdown, *page.warning, *page.caption])
        for private in ('synthetic-invalid-admin-value', 'APP_DATABASE_URL', 'Traceback'):
            self.assertNotIn(private, text)
        for public in ('OpenRouter', 'student project', 'minute'):
            self.assertIn(public, text)


class Freshness(Isolated):
    def test_cached_timestamp_crosses_24_hours_on_a_later_render(self):
        import time
        checked = datetime.now(timezone.utc) - timedelta(hours=24) + timedelta(seconds=3)
        deadline = checked + timedelta(hours=24)
        with patch.object(c, 'latest_sync', return_value=checked) as source, patch.object(c, 'shortlist', return_value=[]):
            page = view()
            self.assertTrue(page.success, 'before the boundary the banner must be fresh')
            time.sleep(max(0, (deadline - datetime.now(timezone.utc)).total_seconds()) + 0.1)
            page.run()
            self.assertTrue(any('Over 24 hours' in w.value for w in page.warning))
            self.assertEqual(source.call_count, 1, 'do not re-query to change the warning')

    def test_banner_uses_last_success_and_utc_with_uncached_age(self):
        now = datetime.now(timezone.utc)
        for checked, kind, needle in [(None,'warning','no successful sync'), (now-timedelta(hours=25),'warning','over 24 hours'),
                                      (now-timedelta(hours=3),'success','3h'), (now+timedelta(hours=2),'warning','future')]:
            st.cache_data.clear()
            with self.subTest(checked=checked), patch.object(c, 'latest_sync', return_value=checked) as source:
                page = view(); self.assertFalse(page.exception)
                banner = getattr(page,kind)
                self.assertTrue(any(needle in x.value.lower() for x in banner))
                if checked and checked <= now:
                    self.assertIn(checked.strftime('%Y-%m-%d %H:%M'), banner[0].value)
                    self.assertIn('UTC',banner[0].value)
                page.run(); self.assertEqual(source.call_count,1)


class Shortlist(Isolated):
    def test_filter_changes_bound_sql_and_empty_result_message(self):
        calls=[]
        def rows(sql, params=()):
            calls.append((sql,params))
            if 'sync_runs' in sql: return [(datetime.now(timezone.utc),)]
            if params==(128000,False): return [('sample/tool',180000,Decimal('0.000004'),Decimal('0.11'),Decimal('0.027504'))]
            return []
        with patch.object(c,'_select', side_effect=rows):
            page=view(); self.assertFalse(page.exception); self.assertTrue(page.dataframe)
            self.assertEqual(page.dataframe[0].value.iloc[0].tolist(),['sample/tool','180,000','0.000004','0.11','0.027504'])
            page.selectbox(key='minimum').select(1000000).run()
            self.assertFalse(page.exception); self.assertFalse(page.dataframe)
            self.assertTrue(any('no entries' in x.value.lower() for x in page.info))
            self.assertTrue(any(p==(1000000,False) and q.count('%s')==2 for q,p in calls))
            page.checkbox(key='sampled').check().run(); self.assertTrue(any(p==(1000000,True) for q,p in calls))


class Routes(Isolated):
    def test_selected_model_and_unknown_zero_and_absent_are_distinct(self):
        chosen="sample/owner's-tool"; calls=[]
        def rows(sql, params=()):
            calls.append((sql,params))
            if 'sync_runs' in sql: return [(datetime.now(timezone.utc),)]
            if params==(128000,False): return [(x,200000,Decimal(0),Decimal(0),Decimal(0)) for x in ('sample/first',chosen)]
            if params==(chosen,): return [('Example Provider',None,'Route B',None,200000,None,Decimal('0.00'),None)]
            return []
        with patch.object(c,'_select',side_effect=rows):
            page=view(); self.assertFalse(page.exception); self.assertTrue(any('no matching route' in x.value.lower() for x in page.info))
            page.selectbox(key='model').select(chosen).run(); self.assertFalse(page.exception)
            self.assertEqual(page.dataframe[1].value.iloc[0].tolist(),['Example Provider','Not listed','Route B','Not listed','200,000','Not listed','0','Not listed'])
            self.assertTrue(any(p==(chosen,) and '%s' in q and chosen not in q for q,p in calls))

    def test_driver_exception_never_reaches_page_and_retry_works(self):
        with patch.dict(os.environ, {'APP_DATABASE_URL':SYN},clear=True), patch('psycopg.connect',side_effect=psycopg.OperationalError('private-synthetic-error-marker')):
            page=view()
        self.assertFalse(page.exception); self.assertTrue(any('unavailable' in m.value for m in page.warning))
        self.assertNotIn('private-synthetic-error-marker',str(page._tree))
        with patch.object(c,'_select',side_effect=lambda sql,params: [(None,)] if 'sync_runs' in sql else []):
            page.run(); self.assertFalse(page.exception); self.assertTrue(any('No successful sync' in m.value for m in page.warning))


class Reader(unittest.TestCase):
    def test_reader_rejects_unsafe_connection_before_network(self):
        bad=['', 'postgresql://[synthetic', SYN.replace(ROLE,'postgres'), SYN.replace(HOST,'unrelated.invalid'),
             SYN+'?options=-crole%3Downer', SYN.replace('/postgres','/other'), SYN.replace(':5432/',':6543/'), SYN.replace(':synthetic@','@')]
        for value in bad:
            with self.subTest(value=value), patch.dict(os.environ,{'APP_DATABASE_URL':value},clear=True), patch('psycopg.connect') as connect:
                with self.assertRaises(c.CatalogueUnavailable) as fail: c.latest_sync()
                connect.assert_not_called(); self.assertNotIn('synthetic',str(fail.exception))

    def test_explicit_zero_port_is_not_a_missing_port(self):
        with patch.dict(os.environ,{'APP_DATABASE_URL':SYN.replace(':5432/',':0/')},clear=True), patch('psycopg.connect') as connect:
            with self.assertRaises(c.CatalogueUnavailable): c.latest_sync()
            connect.assert_not_called()

    def test_verified_transport_identity_and_transaction_precede_read(self):
        for ssl,role in [(False,'app_reader'),(True,'other'),(True,'app_reader')]:
            with self.subTest(ssl=ssl,role=role), patch.dict(os.environ,{'APP_DATABASE_URL':SYN+'?sslmode=disable'},clear=True), patch('psycopg.connect') as connect:
                conn=connect.return_value.__enter__.return_value; conn.pgconn.ssl_in_use=ssl
                def execute(sql,params=()):
                    cursor=Mock(); cursor.fetchone.return_value=('app_reader',role,'on'); cursor.fetchall.return_value=[(None,)]; return cursor
                conn.execute.side_effect=execute
                if ssl and role=='app_reader': self.assertIsNone(c.latest_sync())
                else:
                    with self.assertRaises(c.CatalogueUnavailable): c.latest_sync()
                args=connect.call_args.kwargs
                self.assertEqual(args['sslmode'],'verify-full'); self.assertEqual(Path(args['sslrootcert']),APP.parent/'db/supabase-root-2021.crt')
                self.assertEqual(args['gssencmode'],'disable')
                calls=[x.args[0].lower() for x in conn.execute.call_args_list]
                if ssl: self.assertIn('read only',calls[0])
                self.assertEqual(any('public.sync_runs' in sql for sql in calls), ssl and role=='app_reader')


if __name__=='__main__':
    unittest.main(verbosity=2)
