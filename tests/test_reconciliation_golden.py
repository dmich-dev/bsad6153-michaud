"""Golden Q04 DST/elapsed-hour regression, previously reproduced RED/GREEN."""
import csv
from datetime import datetime,timedelta
import os,unittest
import test_database as base
import test_query_timezones as tztests
@unittest.skipUnless(base.psycopg and os.environ.get('MILESTONE2_TEST_DSN'),'explicit disposable PostgreSQL required')
class GoldenTimezoneTests(unittest.TestCase):
    setUp=base.PostgreSQLTests.setUp
    tearDown=base.PostgreSQLTests.tearDown
    insert_candidate=tztests.QueryTimezoneTests.insert_candidate
    def test_reference_q04_has_closed_720_hour_boundaries_in_all_timezones(self):
        with (base.ROOT/'evals/golden_questions.csv').open(newline='',encoding='utf-8') as file:
            query=next(r['reference_sql'] for r in csv.DictReader(file) if r['id']=='Q04')
        for observed in [datetime.fromisoformat('2026-11-07T19:37:26Z'),datetime.fromisoformat('2026-03-14T19:37:26Z')]:
            self.conn.execute('DELETE FROM catalog_entries')
            start=observed-timedelta(hours=720);tick=timedelta(microseconds=1)
            for label,instant in [('before',start-tick),('start',start),('inside',start+tick),('end',observed),('after',observed+tick)]:
                self.insert_candidate('synthetic/'+label,instant,observed)
            for zone in tztests.TIMEZONES:
                with self.subTest(observed=observed,zone=zone):
                    self.conn.execute("SELECT set_config('TimeZone',%s,false)",(zone,))
                    rows=self.conn.execute(query).fetchall()
                    self.assertEqual([r[0] for r in rows],['synthetic/end','synthetic/inside','synthetic/start'])
