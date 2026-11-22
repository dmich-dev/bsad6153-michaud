"""Part E-H real reader evaluation and quality integration tests."""
import json
from pathlib import Path
import os
import psycopg
import m3_support
from m3_support import ROOT,TABLES,module

class M3EvaluationTests(m3_support.M3Case):
    def test_golden_candidate_all_reference_sql_runs_as_reader_and_persists_comparison(self):
            import tempfile
            from fixtures import snapshot
            self.migrate();self.conn.execute((ROOT/'db/roles.sql').read_text())
            data=snapshot();self.sync().run_sync(self.conn,lambda:data)
            self.assertTrue((ROOT/'evals/golden_questions.csv').exists(),'15-question candidate set is missing')
            self.assertTrue((ROOT/'evals/check_reference.py').exists(),'safe golden-reference checker is missing')
            with tempfile.TemporaryDirectory() as folder:
                baseline=Path(folder)/'first.json'; second=Path(folder)/'second.json'
                common=['--allow-candidate','--scope','local_synthetic']
                result=self.cli('evals/check_reference.py',*common,'--output',str(baseline))
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                first=json.loads(baseline.read_text())
                self.assertEqual(first['database_user'],'app_reader')
                self.assertEqual(len(first['answers']),12)
                self.assertEqual(first['decline_ids'],['Q13','Q14','Q15'])
                self.assertFalse(first['provenance']['acceptance_ready'])
                self.assertEqual(first['provenance']['baseline_count'],0)
                data['models'][0]['context_length']=512000
                self.sync().run_sync(self.conn,lambda:data)
                self.sync().run_sync(self.conn,lambda:data)
                result=self.cli('evals/check_reference.py',*common,'--output',str(second),'--baseline',str(baseline))
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                saved=json.loads(second.read_text())
                self.assertIn('Q01',saved['comparison']['changed_ids'])
                self.assertIn('Q07',saved['comparison']['changed_ids'])
                self.assertFalse(saved['scheduled_requirement_satisfied'])
                self.assertNotEqual(self.cli('evals/check_reference.py',*common,'--output',str(second)).returncode,0,'baseline evidence is immutable')
                self.assertNotEqual(self.cli('evals/check_reference.py','--scope','local_synthetic','--output',str(Path(folder)/'strict.json')).returncode,0,'missing authentic provenance is a real gate')
                self.assertNotEqual(self.cli('evals/check_reference.py',*common,'--output',str(Path(folder)/'owner.json'),env={'APP_DATABASE_URL':os.environ['M3_TEST_DSN']}).returncode,0)

    def test_quality_sql_executes_real_counts_nulls_duplicates_anomalies_orphans_and_coverage(self):
            import tempfile
            from fixtures import snapshot
            self.migrate();self.conn.execute((ROOT/'db/roles.sql').read_text())
            self.sync().run_sync(self.conn,snapshot)
            self.assertTrue((ROOT/'db/quality_checks.sql').exists(),'measured quality SQL is missing')
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'quality.json'
                result=self.cli('scripts/quality_report.py','--output',str(path),'--scope','local_synthetic')
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report=json.loads(path.read_text())
                self.assertEqual(report['database_user'],'app_reader')
                checks=report['checks']
                self.assertEqual(dict((r[1],r[2]) for r in checks['row_counts']['rows'])['catalog_entries'],4)
                self.assertTrue(all(r[2]==0 for r in checks['natural_duplicates']['rows']))
                self.assertTrue(all(r[2]==0 for r in checks['orphans']['rows']))
                self.assertEqual(checks['coverage']['rows'][0][2],1)
                self.assertEqual(checks['coverage']['rows'][0][3],0)

    def test_reader_checker_rejects_mutation_multistatements_empty_and_oversized_results(self):
            from fixtures import snapshot
            self.migrate();self.conn.execute((ROOT/'db/roles.sql').read_text())
            self.sync().run_sync(self.conn,snapshot)
            checker=module('evals/check_reference.py','golden_safety')
            with psycopg.connect(os.environ['M3_APP_DSN'],autocommit=True) as reader:
                for query in ['SELECT 1; DELETE FROM catalog_entries','SELECT * FROM catalog_entries WHERE false','SELECT generate_series(1,1001)']:
                    with self.subTest(query=query),self.assertRaises(ValueError):
                        checker.run_references(reader,[dict(id='Q01',category='lookup',reference_sql=query)])
                with self.assertRaises(psycopg.Error) as error:
                    checker.run_references(reader,[dict(id='Q01',category='lookup',reference_sql='WITH wipe AS (DELETE FROM catalog_entries RETURNING catalog_id) SELECT * FROM wipe')])
                self.assertIn(error.exception.sqlstate,('42501','25006'))
            self.assertEqual(self.conn.execute('SELECT count(*) FROM catalog_entries').fetchone()[0],4)

    def test_credential_facing_new_clis_suppress_malformed_dsn_without_fallback(self):
            import tempfile
            self.migrate()
            with tempfile.TemporaryDirectory() as directory:
                for script,args in [('scripts/status.py',[]),('scripts/quality_report.py',['--scope','local_synthetic','--output',str(Path(directory)/'q.json')]),('evals/check_reference.py',['--scope','local_synthetic','--allow-candidate','--output',str(Path(directory)/'g.json')])]:
                    with self.subTest(script=script):
                        result=self.cli(script,*args,env={'APP_DATABASE_URL':'invalid DSN SYNTHETIC-SECRET-MUST-NOT-LOG'})
                        self.assertNotEqual(result.returncode,0)
                        self.assertNotIn('SYNTHETIC-SECRET-MUST-NOT-LOG',result.stdout+result.stderr)
                        self.assertNotIn('Traceback',result.stdout+result.stderr)
