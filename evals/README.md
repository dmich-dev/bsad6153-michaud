# evals/

How you prove your system gives correct answers.

| Week | File | What it does |
|---|---|---|
| 3 | `golden_questions.csv` | 15+ questions with columns `id, question, category, reference_sql, correct_behavior, source` |
| 3 | `check_reference.py` | Runs every reference query as `app_reader` and confirms each one succeeds |
| 5 | `run_evals.py` | Asks your chatbot every golden question; records answer, tool calls, tokens, cost, time, and the reference result |
| 5&ndash;7 | `results/weekN.csv` | One results file per evaluation run, graded by you |

Reference answers are SQL, not fixed values, because your data keeps syncing.

## Which questions count as `baseline` in Part F?

| IDs | Source | What the checker verifies |
|---|---|---|
| Q01–Q05 | The five published M2 business queries, reused as Part F permits | Each question matches its numbered mapping on the [running list](../docs/running_questions_2026-11-14.md), its M2 source note, and its exact numbered `SELECT` in [`db/queries.sql`](../db/queries.sql) (without the final semicolon). |
| Q06, Q08, Q10 | Assistant proposals the student kept on November 22, 2026 | ID and wording match a selected row on that list. Selection is not authorship. |
| Q07, Q09, Q11–Q15 | Other proposals | These seven are `other`; Q13–Q15 specify declines and have no SQL. |

The [ledger](question_provenance.json) preserves the distinct origins. None of the eight is asserted to be an entry in the historical M1 log. The corrected set can run in strict mode without `--allow-candidate`. The earlier [live checker receipts](../docs/sync_tests.md#live-reference-baseline) are for a different set hash; they cannot serve as the baseline for a corrected-set comparison.
