"""Provenance fixtures are synthetic and do not create student evidence."""
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from test_m3 import ROOT,module

class ProvenanceTests(unittest.TestCase):
    def test_baseline_cannot_reuse_one_original_identity_across_rows_or_files(self):
        checker=module('evals/check_reference.py','golden_distinct_origins')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'docs').mkdir()
            with (ROOT/'evals/golden_questions.csv').open(newline='') as file: rows=list(csv.DictReader(file))
            original='SYNTHETIC original question: how many fixture providers exist?'
            for name in ('first.md','copied.md'):
                (root/'docs'/name).write_text('SYNTHETIC TEST ONLY, NOT STUDENT HISTORY\n'+original)
            csv_path=root/'questions.csv';ledger_path=root/'origins.json'
            for duplicate_files in (False,True):
                with self.subTest(duplicate_files=duplicate_files):
                    ledger={'questions':{r['id']:dict(origin_kind='new_assistant_candidate',student_historical_evidence=False) for r in rows}}
                    for index,row in enumerate(rows[:8]):
                        row.update(source='baseline',question=original)
                        name='copied.md' if duplicate_files and index%2 else 'first.md'
                        source=root/'docs'/name
                        ledger['questions'][row['id']]=dict(origin_kind='student_running_list',origin_file='docs/'+name,
                            origin_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),origin_excerpt=original,
                            original_question=original,student_historical_evidence=True,fixture_notice='SYNTHETIC TEST ONLY')
                    with csv_path.open('w',newline='') as file:
                        writer=csv.DictWriter(file,fieldnames=checker.COLUMNS);writer.writeheader();writer.writerows(rows)
                    ledger_path.write_text(json.dumps(ledger))
                    with self.assertRaises(ValueError): checker.load_questions(csv_path,ledger_path,root=root)

    def test_baseline_question_rejects_unrelated_or_stale_current_text(self):
        checker=module('evals/check_reference.py','golden_exact_binding')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'docs').mkdir()
            with (ROOT/'evals/golden_questions.csv').open(newline='') as file: rows=list(csv.DictReader(file))
            source=root/'docs/synthetic_history.md'
            source.write_text('SYNTHETIC TEST ONLY, NOT STUDENT HISTORY\n'+'\n'.join(r['question'] for r in rows[:8]))
            ledger={'questions':{r['id']:dict(origin_kind='new_assistant_candidate',student_historical_evidence=False) for r in rows}}
            for row in rows[:8]:
                row['source']='baseline'
                ledger['questions'][row['id']]=dict(origin_kind='student_running_list',origin_file='docs/synthetic_history.md',
                    origin_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),origin_excerpt=row['question'],
                    original_question=row['question'],student_historical_evidence=True,fixture_notice='SYNTHETIC TEST ONLY')
            csv_path=root/'questions.csv';ledger_path=root/'origins.json'
            ledger_path.write_text(json.dumps(ledger))
            for mutation in ('unrelated','stale'):
                with self.subTest(mutation=mutation):
                    changed=copy.deepcopy(rows)
                    for row in changed[:8]:
                        row['question']='Unrelated SYNTHETIC question '+row['id'] if mutation=='unrelated' else row['question']+' (changed after mapping)'
                    with csv_path.open('w',newline='') as file:
                        writer=csv.DictWriter(file,fieldnames=checker.COLUMNS);writer.writeheader();writer.writerows(changed)
                    with self.assertRaises(ValueError): checker.load_questions(csv_path,ledger_path,root=root)
            with csv_path.open('w',newline='') as file:
                writer=csv.DictWriter(file,fieldnames=checker.COLUMNS);writer.writeheader();writer.writerows(rows)
            _,healthy=checker.load_questions(csv_path,ledger_path,root=root)
            self.assertEqual(healthy['baseline_count'],8)
            self.assertTrue(healthy['acceptance_ready'])

    def test_verified_synthetic_origins_are_validated_without_relabeling_real_candidates(self):
        checker=module('evals/check_reference.py','golden_provenance')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'docs').mkdir()
            with (ROOT/'evals/golden_questions.csv').open(newline='') as file: rows=list(csv.DictReader(file))
            ledger=json.loads((ROOT/'evals/question_provenance.json').read_text())
            excerpt='SYNTHETIC TEST FIXTURE ONLY, NOT STUDENT HISTORY\n'+'\n'.join(r['question'] for r in rows[:8])
            source=root/'docs/synthetic_questions.md';source.write_text(excerpt)
            for row in rows[:8]:
                row['source']='baseline'
                ledger['questions'][row['id']]=dict(origin_kind='student_running_list',origin_file='docs/synthetic_questions.md',
                    origin_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),origin_excerpt=row['question'],
                    original_question=row['question'],student_historical_evidence=True,
                    fixture_notice='SYNTHETIC TEST ONLY')
            # Other rows are new candidates and have no inherited-source files.
            for row in rows[8:]: ledger['questions'][row['id']]=dict(origin_kind='new_assistant_candidate',original_question=row['question'],student_historical_evidence=False)
            csv_path=root/'questions.csv';ledger_path=root/'origins.json'
            with csv_path.open('w',newline='') as file:
                writer=csv.DictWriter(file,fieldnames=checker.COLUMNS);writer.writeheader();writer.writerows(rows)
            ledger_path.write_text(json.dumps(ledger))
            _,result=checker.load_questions(csv_path,ledger_path,root=root)
            self.assertEqual(result['baseline_count'],8)
            self.assertTrue(result['acceptance_ready'])
            broken=copy.deepcopy(ledger);broken['questions']['Q01']['student_historical_evidence']=False
            ledger_path.write_text(json.dumps(broken))
            with self.assertRaises(ValueError): checker.load_questions(csv_path,ledger_path,root=root)
            ledger_path.write_text(json.dumps(ledger));source.write_text('changed synthetic source')
            with self.assertRaises(ValueError): checker.load_questions(csv_path,ledger_path,root=root)
        _,real=checker.load_questions(ROOT/'evals/golden_questions.csv',ROOT/'evals/question_provenance.json')
        self.assertEqual(real['baseline_count'],0)
        self.assertFalse(real['acceptance_ready'])
