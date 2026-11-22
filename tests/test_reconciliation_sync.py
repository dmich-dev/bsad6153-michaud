"""Reconciliation regressions, previously reproduced RED/GREEN in this packet."""
from unittest.mock import patch
from m3_support import M3Case, TABLES
from fixtures import snapshot

class SyncPreflightTests(M3Case):
    def test_whitespace_only_route_identity_rejected_before_data_transaction(self):
        self.migrate()
        sync=self.sync()
        for tag,name in [(' ',None),(None,'\t'),('\u00a0','\u2003')]:
            with self.subTest(tag=tag,name=name):
                data=snapshot();data['endpoints'][0].update(tag=tag,name=name)
                with patch.object(sync,'_apply',side_effect=AssertionError('invalid identity reached data writer')) as apply:
                    result=sync.run_sync(self.conn,lambda:data)
                self.assertEqual(result['status'],'failed');apply.assert_not_called()
                self.assertEqual(result['error_message'],'source_or_validation_error')
        self.assertEqual([self.conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in TABLES],[0,0,0,0])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM sync_state').fetchone()[0],0)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sync_runs WHERE status='failed'").fetchone()[0],3)

    def test_usable_route_identity_is_preserved_without_trimming(self):
        self.migrate();sync=self.sync();data=snapshot()
        data['endpoints'][0].update(tag=' ',name=' Exact café route ')
        result=sync.run_sync(self.conn,lambda:data)
        self.assertEqual(result['status'],'success')
        row=self.conn.execute('SELECT tag,name,raw_payload FROM serving_endpoints WHERE name=%s',(' Exact café route ',)).fetchone()
        self.assertEqual(row[:2],(' ',' Exact café route '));self.assertEqual(row[2],data['endpoints'][0])
