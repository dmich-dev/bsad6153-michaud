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
RUNNING_LIST='docs/running_questions_2026-11-14.md'
# Pin the decision rows from the published November 22 worksheet, not surrounding prose.
DECISION_ROWS_SHA256='82ebe66fb8d3e20da96ae9593bcbfaeffcb913aafc90ed42085590aa8ab25aa9'
M2_COMMIT='42ce2521bab78f68376f0ab66244bdc2f51f698e'
M2_NOTES='docs/milestone2_questions.md'
M2_NOTES_SHA256='5201bd7c83dbebf5a541b378e20bd57263c1df48268047d0d40a1b5177951554'
M2_SQL='db/queries.sql'
M2_SQL_SHA256='35e55438b3583085524ac9c3c1a742615ab8fae43c33f03e41b5b8963b405cc1'


def checked_source(root, name, expected_hash):
    path=Path(name)
    if (str(path)!=name or path.is_absolute() or '..' in path.parts or not path.parts
        or path.parts[0] not in ('docs','db')):
        raise ValueError('Origin must be an allowlisted project document')
    target=Path(root)/path
    if any(p.is_symlink() for p in [target,*target.parents] if p!=Path(root).parent):
        raise ValueError('Origin symlinks are not allowed')
    content=target.read_bytes()
    if hashlib.sha256(content).hexdigest()!=expected_hash:
        raise ValueError('Origin source changed')
    return content.decode('utf-8')


def check_part_f_origin(row, origin, ledger, root):
    qid=row['id']
    if origin.get('student_historical_evidence') is not False:
        raise ValueError('Part F reuse/selection is not historical student authorship')
    worksheet=checked_source(root,RUNNING_LIST,ledger.get('running_list_sha256'))
    decisions=[line for line in worksheet.splitlines() if re.match(r'^\| Q[0-9]+ \|',line)]
    if hashlib.sha256('\n'.join(decisions).encode()).hexdigest()!=DECISION_ROWS_SHA256:
        raise ValueError('Published running-list decisions have changed')
    prefix=f"| {qid} | {row['question']} | "
    if origin['origin_kind']=='student_selected_proposal':
        expected=prefix+'Kept by the student on November 22. |'
        if (origin.get('origin_file')!=RUNNING_LIST or origin.get('origin_excerpt')!=expected
            or origin.get('original_question')!=row['question'] or expected not in decisions):
            raise ValueError('Question does not match a selected running-list row')
        return
    number=int(qid[1:])
    if (qid not in ('Q01','Q02','Q03','Q04','Q05') or ledger.get('m2_published_commit')!=M2_COMMIT
        or prefix+f'Reuses M2 business query {number}. |' not in decisions
        or origin.get('origin_file')!=M2_NOTES or origin.get('origin_sha256')!=M2_NOTES_SHA256
        or origin['origin_excerpt'].split(' | ')[:2]!=[f'| Q{number}',origin['original_question']]
        or origin.get('query_origin')!=f'{M2_SQL} Q{number}' or origin.get('query_origin_sha256')!=M2_SQL_SHA256):
        raise ValueError('Question does not match its published M2 origin')
    # This is the pinned five-query M2 file, not a general SQL parser. Keep all
    # SELECT bytes, including whitespace inside literals; only omit its terminator.
    sql=checked_source(root,M2_SQL,M2_SQL_SHA256)
    block=re.search(rf'^-- Q{number}:[^\n]*\n(?:--[^\n]*\n)*(SELECT\b[^;]+);$',sql,re.MULTILINE)
    if not block or row['reference_sql']!=block[1]:
        raise ValueError('Reference SQL differs from its numbered published M2 SELECT')


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
    ledger=json.loads(Path(provenance_path).read_text())
    provenance=ledger['questions']
    baseline_identities=set()
    baseline_count=0
    for row in rows:
        if (not re.fullmatch(r'Q[0-9]{2,}',row['id']) or row['category'] not in CATEGORIES
            or row['source'] not in ('baseline','other') or not row['question'].strip()
            or not row['correct_behavior'].strip() or row['id'] not in provenance):
            raise ValueError('Invalid question metadata')
        if (row['category']=='should_decline') != (not row['reference_sql'].strip()):
            raise ValueError('Decline SQL must be empty; other questions need SQL')
        origin=provenance[row['id']]
        original=origin.get('original_question','')
        if origin.get('origin_file'):
            content=checked_source(root,origin['origin_file'],origin.get('origin_sha256'))
            excerpt=origin.get('origin_excerpt','')
            if origin.get('origin_kind')=='published_m2_query' and excerpt not in content.splitlines():
                raise ValueError('Published M2 note must be a whole source row')
            if not excerpt or not original or excerpt not in content or original not in excerpt:
                raise ValueError('Exact original question/excerpt is not supported')
        if origin.get('origin_kind') in ('published_m2_query','student_selected_proposal'):
            check_part_f_origin(row,origin,ledger,root)
        elif row['source']=='baseline':
            if (not origin.get('origin_file') or origin.get('student_historical_evidence') is not True
                or origin['origin_file'] in (RUNNING_LIST,M2_NOTES,M2_SQL)
                or origin.get('origin_kind') not in ('student_baseline','student_running_list','confirmed_business_query')):
                raise ValueError('A proposal cannot be relabeled as historical evidence')
            if row['question']!=original:
                raise ValueError('Baseline question must exactly match its original question')
        if row['source']=='baseline':
            identities={original,row['question']}
            if baseline_identities & identities:
                raise ValueError('Baseline original or current question is reused')
            baseline_identities.update(identities)
            baseline_count+=1
    declines=sum(r['category']=='should_decline' for r in rows)
    if declines<3: raise ValueError('Need at least three decline questions')
    return rows,dict(question_count=len(rows),decline_count=declines,baseline_count=baseline_count,
                     acceptance_ready=baseline_count>=8,gate=None if baseline_count>=8 else 'Fewer than eight distinct Part F origins verified')


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
            print('Reference check gated: fewer than eight distinct Part F origins verified. Use --allow-candidate only for explicitly labeled technical review.')
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
