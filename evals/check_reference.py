"""DRAFT: execute reviewed reference SQL as app_reader and freeze exact answers.

This is not a chatbot evaluator or a general SQL sandbox. Declines are specifications.
"""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re

import psycopg
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
COLUMNS=['id','question','category','reference_sql','correct_behavior','source']
CATEGORIES={'lookup','aggregate','trend','compare','should_decline'}


def json_default(value):
    if isinstance(value,Decimal): return str(value)
    if isinstance(value,datetime): return value.isoformat()
    raise TypeError('Unsupported reference answer type')


def load_questions(csv_path,provenance_path,*,root=ROOT):
    with Path(csv_path).open(newline='',encoding='utf-8') as file:
        reader=csv.DictReader(file)
        if reader.fieldnames!=COLUMNS: raise ValueError('Invalid golden CSV columns')
        rows=list(reader)
    if len(rows)<15 or len({r['id'] for r in rows})!=len(rows):
        raise ValueError('Need at least 15 uniquely identified questions')
    provenance=json.loads(Path(provenance_path).read_text())['questions']
    baseline_originals=set()
    for row in rows:
        if (not re.fullmatch(r'Q[0-9]{2,}',row['id']) or row['category'] not in CATEGORIES
            or row['source'] not in ('baseline','other') or not row['question'].strip()
            or not row['correct_behavior'].strip() or row['id'] not in provenance):
            raise ValueError('Invalid question metadata')
        if (row['category']=='should_decline') != (not row['reference_sql'].strip()):
            raise ValueError('Decline SQL must be empty; other questions need SQL')
        origin=provenance[row['id']]
        if origin.get('origin_file'):
            path=Path(origin['origin_file'])
            if path.is_absolute() or '..' in path.parts or path.parts[0] not in ('docs','db'):
                raise ValueError('Origin must be an allowlisted project document')
            target=Path(root)/path
            if any(p.is_symlink() for p in [target,*target.parents] if p!=Path(root).parent):
                raise ValueError('Origin symlinks are not allowed')
            content=target.read_bytes()
            if hashlib.sha256(content).hexdigest()!=origin.get('origin_sha256'):
                raise ValueError('Origin source changed')
            excerpt=origin.get('origin_excerpt','')
            original=origin.get('original_question','')
            if not excerpt or not original or excerpt not in content.decode('utf-8') or original not in excerpt:
                raise ValueError('Exact original question/excerpt is not supported')
        if row['source']=='baseline':
            if (not origin.get('origin_file') or origin.get('student_historical_evidence') is not True
                or origin.get('origin_kind') not in ('student_baseline','student_running_list','confirmed_business_query')):
                raise ValueError('A proposal cannot be relabeled as historical evidence')
            if row['question']!=original:
                raise ValueError('Baseline question must exactly match its original question')
            if original in baseline_originals:
                raise ValueError('Baseline original question is reused')
            baseline_originals.add(original)
    baseline_count=len(baseline_originals)
    declines=sum(r['category']=='should_decline' for r in rows)
    if declines<3: raise ValueError('Need at least three decline questions')
    return rows,dict(question_count=len(rows),decline_count=declines,baseline_count=baseline_count,
                     acceptance_ready=baseline_count>=8,gate=None if baseline_count>=8 else 'Eight authentic baseline/running-list origins remain unverified')


def run_references(conn,rows):
    answers={}
    with conn.transaction():
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        user=conn.execute('SELECT current_user').fetchone()[0]
        if user!='app_reader': raise ValueError('app_reader is required')
        conn.execute("SET LOCAL statement_timeout='10s'; SET LOCAL lock_timeout='3s'")
        for row in rows:
            if row['category']=='should_decline': continue
            query=row['reference_sql'].strip().removesuffix(';').strip()
            if ';' in query or not re.match(r'^(SELECT|WITH)\b',query,re.I):
                raise ValueError('Only one reviewed read query is allowed')
            cursor=conn.execute(query,prepare=True)
            values=cursor.fetchmany(1001)
            if not values or len(values)>1000:
                raise ValueError('Reference query empty or exceeds bounded result size')
            answers[row['id']]=dict(columns=[c.name for c in cursor.description],rows=values)
    return user,json.loads(json.dumps(answers,default=json_default,sort_keys=True))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',type=Path,default=ROOT/'evals/golden_questions.csv')
    parser.add_argument('--provenance',type=Path,default=ROOT/'evals/question_provenance.json')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--scope',required=True,choices=['local_synthetic','live_supabase'])
    parser.add_argument('--allow-candidate',action='store_true')
    args=parser.parse_args(argv)
    try:
        rows,provenance=load_questions(args.csv,args.provenance)
        if not provenance['acceptance_ready'] and not args.allow_candidate:
            print('Reference check gated: eight verified historical origins are missing. Use --allow-candidate only for explicitly labeled technical review.')
            return 2
        load_dotenv(ROOT/'.env',override=False)
        url=os.environ.get('APP_DATABASE_URL')
        if not url: raise ValueError()
        with psycopg.connect(url,autocommit=True,connect_timeout=10) as conn:
            user,answers=run_references(conn,rows)
        identity=hashlib.sha256(args.csv.read_bytes()+b'\0'+args.provenance.read_bytes()).hexdigest()
        result=dict(executed_at=datetime.now(timezone.utc).isoformat(),evidence_scope=args.scope,
                    database_user=user,set_sha256=identity,provenance=provenance,answers=answers,
                    decline_ids=[r['id'] for r in rows if r['category']=='should_decline'],
                    scheduled_requirement_satisfied=False,
                    schedule_gate='Requires independent GitHub schedule-event evidence and a later check after two more genuine scheduled syncs')
        if args.baseline:
            before=json.loads(args.baseline.read_text())
            if before['set_sha256']!=identity or before['evidence_scope']!=args.scope or set(before['answers'])!=set(answers):
                raise ValueError('Baseline set or scope mismatch')
            changed=sorted(k for k,v in answers.items() if before['answers'][k]!=v)
            result['comparison']=dict(baseline_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
                                      changed_ids=changed,unchanged_ids=sorted(set(answers)-set(changed)))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        # Freeze evidence: rerunning never overwrites an earlier baseline.
        with args.output.open('x',encoding='utf-8') as file:
            json.dump(result,file,default=json_default,indent=2,sort_keys=True);file.write('\n')
        print(json.dumps(dict(reference_queries_succeeded=len(answers),declines_specified=len(result['decline_ids']),
                              provenance=provenance,comparison=result.get('comparison'),evidence_scope=args.scope),sort_keys=True))
        return 0
    except Exception:
        print('Reference check failed: review CSV/provenance, immutable output path, baseline identity and private app_reader configuration. No raw database error is printed.')
        return 1


if __name__=='__main__':
    raise SystemExit(main())
