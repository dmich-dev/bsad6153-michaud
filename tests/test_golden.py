"""Provenance fixtures are synthetic and do not create student evidence."""
import copy
import csv
import hashlib
import shutil
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
            for row in rows: row['source']='other'
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
            for row in rows: row['source']='other'
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
            for row in rows[8:]:
                row['source']='other'
                ledger['questions'][row['id']]=dict(origin_kind='new_assistant_candidate',original_question=row['question'],student_historical_evidence=False)
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

    def test_part_f_rejects_spoofed_reuse_selection_and_stale_hashes(self):
        checker=module('evals/check_reference.py','golden_spoofed_reuse')
        cases=('another_select','unrelated_select','different_literal','reused_query_origin',
               'wrong_m2_note','unrelated_current_wording','unselected_proposal','false_history',
               'm2_sql_hash','m2_note_hash','running_list_hash','other_file_hash',
               'duplicate_current_question','historical_path_alias','false_m2_original','other_query_hash')
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                for name in ('docs/running_questions_2026-11-14.md','docs/milestone2_questions.md','db/queries.sql'):
                    target=root/name; target.parent.mkdir(exist_ok=True)
                    shutil.copyfile(ROOT/name,target)
                with (ROOT/'evals/golden_questions.csv').open(newline='') as file:
                    rows={r['id']:r for r in csv.DictReader(file)}
                ledger=json.loads((ROOT/'evals/question_provenance.json').read_text())
                origins=ledger['questions']
                if case=='another_select': rows['Q02']['reference_sql']=rows['Q01']['reference_sql']
                elif case=='unrelated_select': rows['Q02']['reference_sql']='SELECT 1'
                elif case=='different_literal': rows['Q04']['reference_sql']=rows['Q04']['reference_sql'].replace('720 hours','720  hours')
                elif case=='reused_query_origin':
                    origins['Q02']['query_origin']=origins['Q01']['query_origin']
                    rows['Q02']['reference_sql']=rows['Q01']['reference_sql']
                elif case=='wrong_m2_note':
                    for key in ('original_question','origin_excerpt'): origins['Q02'][key]=origins['Q01'][key]
                elif case=='unrelated_current_wording': rows['Q04']['question']=rows['Q09']['question']
                elif case=='unselected_proposal':
                    rows['Q07']['source']='baseline'
                    origins['Q07']=dict(origins['Q06'],original_question=rows['Q07']['question'],
                        origin_excerpt=next(x for x in (root/origins['Q06']['origin_file']).read_text().splitlines() if x.startswith('| Q07 |')))
                elif case=='duplicate_current_question':
                    rows['Q07'].update(source='baseline',question=rows['Q01']['question'])
                    text=rows['Q07']['question'];name='docs/copied.md';(root/name).write_text(text)
                    origins['Q07']=dict(origin_kind='student_running_list',original_question=text,
                        origin_excerpt=text,origin_file=name,origin_sha256=hashlib.sha256(text.encode()).hexdigest(),
                        student_historical_evidence=True)
                elif case=='historical_path_alias':
                    origins['Q08'].update(origin_kind='student_running_list',student_historical_evidence=True,
                        origin_file='docs/./running_questions_2026-11-14.md')
                elif case=='false_m2_original':
                    origins['Q01']['original_question']+=' | Recorded cost effectiveness; project context/tool comparison'
                elif case=='false_history': origins['Q08']['student_historical_evidence']=True
                elif case=='m2_sql_hash': (root/'db/queries.sql').write_text('SELECT 1;')
                elif case=='m2_note_hash': (root/'docs/milestone2_questions.md').write_text('stale notes')
                elif case=='running_list_hash': ledger['running_list_sha256']='0'*64
                elif case=='other_query_hash':
                    rows['Q01']['source']='other';origins['Q01']['query_origin_sha256']='0'*64
                elif case=='other_file_hash':
                    rows['Q06']['source']='other';origins['Q06']['origin_sha256']='0'*64
                csv_path=root/'questions.csv';ledger_path=root/'ledger.json'
                with csv_path.open('w',newline='') as file:
                    writer=csv.DictWriter(file,fieldnames=checker.COLUMNS);writer.writeheader();writer.writerows(rows.values())
                ledger_path.write_text(json.dumps(ledger))
                with self.assertRaises(ValueError): checker.load_questions(csv_path,ledger_path,root=root)

    def test_real_set_counts_five_published_queries_and_three_selected_proposals(self):
        checker=module('evals/check_reference.py','golden_part_f')
        rows,summary=checker.load_questions(ROOT/'evals/golden_questions.csv',ROOT/'evals/question_provenance.json')
        ledger=json.loads((ROOT/'evals/question_provenance.json').read_text())['questions']
        reused={'Q01','Q02','Q03','Q04','Q05'}
        selected={'Q06','Q08','Q10'}
        self.assertEqual({row['id'] for row in rows if row['source']=='baseline'},reused|selected)
        for ids,kind in ((reused,'published_m2_query'),(selected,'student_selected_proposal')):
            for qid in ids:
                self.assertEqual(ledger[qid]['origin_kind'],kind)
                self.assertIs(ledger[qid]['student_historical_evidence'],False)
        self.assertEqual((summary['question_count'],summary['baseline_count'],summary['decline_count']),(15,8,3))
        self.assertTrue(summary['acceptance_ready'])
