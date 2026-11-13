"""Opt-in real PostgreSQL Q4 regressions; all inserted records are synthetic.

Reuse the existing schema/query helpers, not the original TestCase inheritance,
so discovery never runs the original database tests a second time.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from typing import Any
import unittest

import test_database as base_tests


OBSERVED_AT = datetime.fromisoformat('2026-11-07T19:37:26Z')
TIMEZONES = ('UTC', 'America/Chicago', 'Asia/Kolkata')


@unittest.skipUnless(base_tests.psycopg and os.environ.get('MILESTONE2_TEST_DSN'),
                     'explicit disposable PostgreSQL required')
class QueryTimezoneTests(unittest.TestCase):
    conn: Any
    schema: str
    setUp = base_tests.PostgreSQLTests.setUp
    tearDown = base_tests.PostgreSQLTests.tearDown
    query = base_tests.PostgreSQLTests.query

    def insert_candidate(self, catalog_id, created_at, observed_at=OBSERVED_AT,
                         output_modalities=('text',), supported_parameters=('tools',)):
        payload = json.dumps({'id': catalog_id, 'synthetic': True}, sort_keys=True)
        self.conn.execute(
            """INSERT INTO catalog_entries
                   (catalog_id, catalog_created_at, source_observed_at,
                    output_modalities, supported_parameters, raw_payload, payload_sha256)
               VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)""",
            (catalog_id, created_at, observed_at, list(output_modalities),
             list(supported_parameters), payload,
             hashlib.sha256(payload.encode('utf-8')).hexdigest()))

    def q4_rows(self, zone):
        self.conn.execute("SELECT set_config('TimeZone', %s, false)", (zone,))
        return self.conn.execute(self.query(4)).fetchall()

    def test_q4_excludes_candidate_older_than_720_elapsed_hours_across_fall_back(self):
        self.insert_candidate('synthetic/fall-back-repro',
                              datetime.fromisoformat('2026-10-08T19:07:26Z'))
        counts = {zone: len(self.q4_rows(zone)) for zone in TIMEZONES}
        print('Q4 saved-observation DST reproduction: ' + json.dumps(counts, sort_keys=True),
              flush=True)
        self.assertEqual(counts, dict.fromkeys(TIMEZONES, 0),
                         'a 720-hour window must not gain an hour at Chicago fall-back')

    def test_q4_window_is_closed_at_exact_instants_with_microsecond_outside_excluded(self):
        # Exercise both Chicago clock changes, not only a fixed-offset zone.
        observations = (OBSERVED_AT, datetime.fromisoformat('2026-03-14T19:37:26Z'))
        for observed_at in observations:
            with self.subTest(observed_at=observed_at):
                self.conn.execute('DELETE FROM catalog_entries')
                start = observed_at - timedelta(hours=720)
                tick = timedelta(microseconds=1)
                candidates = [
                    ('synthetic/before-start', start - tick),
                    ('synthetic/start', start),
                    ('synthetic/inside-start', start + tick),
                    ('synthetic/inside-end', observed_at - tick),
                    ('synthetic/end', observed_at),
                    ('synthetic/after-end', observed_at + tick),
                    ('synthetic/unknown-created', None),
                ]
                for catalog_id, created_at in reversed(candidates):
                    self.insert_candidate(catalog_id, created_at, observed_at)
                stored = self.conn.execute(
                    """SELECT catalog_id, catalog_created_at AT TIME ZONE 'UTC',
                              source_observed_at AT TIME ZONE 'UTC', raw_payload, payload_sha256
                       FROM catalog_entries ORDER BY catalog_id""").fetchall()
                expected = [
                    ('synthetic/end', observed_at),
                    ('synthetic/inside-end', observed_at - tick),
                    ('synthetic/inside-start', start + tick),
                    ('synthetic/start', start),
                ]
                for zone in TIMEZONES:
                    with self.subTest(zone=zone):
                        rows = self.q4_rows(zone)
                        self.assertEqual([(r[0], r[1].astimezone(timezone.utc)) for r in rows],
                                         expected)
                        self.assertEqual([r[4].astimezone(timezone.utc) for r in rows],
                                         [observed_at] * len(expected))
                self.assertEqual(self.conn.execute(
                    """SELECT catalog_id, catalog_created_at AT TIME ZONE 'UTC',
                              source_observed_at AT TIME ZONE 'UTC', raw_payload, payload_sha256
                       FROM catalog_entries ORDER BY catalog_id""").fetchall(), stored,
                    'querying in other timezones must not rewrite source IDs, dates or raw data')

    def test_q4_orders_newest_first_then_exact_catalog_id_for_tied_instants(self):
        older = OBSERVED_AT - timedelta(hours=12)
        candidates = [
            ('synthetic/z-older', older),
            ('synthetic/z-newest', OBSERVED_AT),
            ('synthetic/a-older', older),
            ('synthetic/a-newest', OBSERVED_AT),
        ]
        for catalog_id, created_at in candidates:
            self.insert_candidate(catalog_id, created_at)
        expected = ['synthetic/a-newest', 'synthetic/z-newest',
                    'synthetic/a-older', 'synthetic/z-older']
        for repeat in range(3):
            for zone in TIMEZONES:
                with self.subTest(repeat=repeat, zone=zone):
                    self.assertEqual([r[0] for r in self.q4_rows(zone)], expected)

    def test_q4_uses_latest_saved_observation_including_non_text_tool_entries(self):
        earlier = OBSERVED_AT - timedelta(days=10)
        self.insert_candidate('synthetic/eligible', OBSERVED_AT - timedelta(days=15), earlier)
        self.insert_candidate('synthetic/too-old', OBSERVED_AT - timedelta(days=35), earlier)
        self.insert_candidate('synthetic/non-text-anchor', OBSERVED_AT - timedelta(days=1),
                              output_modalities=('image',))
        self.insert_candidate('synthetic/no-tools', OBSERVED_AT - timedelta(days=2),
                              supported_parameters=())
        for zone in TIMEZONES:
            with self.subTest(zone=zone):
                self.assertEqual([r[0] for r in self.q4_rows(zone)], ['synthetic/eligible'])

    def test_q4_saved_window_ignores_a_changing_real_session_current_date(self):
        created_at = OBSERVED_AT - timedelta(hours=1)
        self.insert_candidate('synthetic/current-date-independent', created_at)
        dates = {}
        # These real fixed-offset zones are 26 hours apart: CURRENT_DATE differs
        # at any wall-clock execution time without mocking or changing system time.
        for zone in ('Pacific/Kiritimati', 'Etc/GMT+12'):
            with self.subTest(zone=zone):
                rows = self.q4_rows(zone)
                dates[zone] = self.conn.execute('SELECT current_date').fetchone()[0]
                normalized = [(r[0], r[1].astimezone(timezone.utc),
                               r[4].astimezone(timezone.utc)) for r in rows]
                self.assertEqual(normalized,
                                 [('synthetic/current-date-independent', created_at, OBSERVED_AT)])
        self.assertGreater(len(set(dates.values())), 1,
                           'the test must observe different real CURRENT_DATE values')
        print('Q4 unchanged while real session current_date changes: ' +
              json.dumps({zone: day.isoformat() for zone, day in dates.items()}, sort_keys=True),
              flush=True)


if __name__ == '__main__':
    unittest.main()
