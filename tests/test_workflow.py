from pathlib import Path
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[1]
class WorkflowTests(unittest.TestCase):
    def test_workflow_schedule_manual_permissions_secrets_concurrency_and_visible_failure(self):
        path=ROOT/'.github/workflows/sync.yml'
        self.assertTrue(path.exists(),'scheduled sync workflow is missing')
        text=path.read_text();data=yaml.load(text,Loader=yaml.BaseLoader)
        self.assertEqual(set(data['on']),{'schedule','workflow_dispatch'})
        self.assertEqual(data['on']['schedule'],[{'cron':'17 9 * * *'}])
        self.assertEqual(data['permissions'],{'contents':'read'})
        self.assertEqual(data['concurrency']['cancel-in-progress'],'false')
        job=data['jobs']['sync']
        self.assertEqual(job['timeout-minutes'],'15')
        step=next(s for s in job['steps'] if s.get('id')=='sync')
        self.assertEqual(step['env']['DATABASE_URL'],'${{ secrets.DATABASE_URL }}')
        self.assertEqual(step['env']['OPENROUTER_API_KEY'],'${{ secrets.OPENROUTER_API_KEY }}')
        self.assertIn('github.event_name',step['env']['SYNC_TRIGGER'])
        self.assertIn('python -I -B ingest/sync.py --trigger "$SYNC_TRIGGER"',step['run'])
        self.assertNotIn('continue-on-error',text)
        self.assertNotIn('|| true',text)
        self.assertNotIn('--local-fixture-url',text)
        self.assertNotIn('postgresql://',text)
