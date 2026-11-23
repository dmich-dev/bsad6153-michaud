# Part G: sync failures and reference checks

## Live manual sync and recovery

On November 22, 2026 (Central), the sync fetched OpenRouter metadata and wrote to the live Supabase catalog. These IDs are from the live `sync_runs` table, **not** the identically numbered local fixture runs below. Sources: `manual-sync-intent.json`, `manual-sync-retry-intent.json`, `manual-sync-retry-readback.json`, and the dated live sync summary. The run 1 fetched count is from the November 22 live recording deck’s run-history table; the retry receipt confirms its recovery and zero committed writes.

| Live run | Trigger / outcome | Fetched | Inserted | Updated | What the database recorded |
|---|---|---:|---:|---:|---|
| 1 | manual / failed | 767 | 0 | 0 | The time limit interrupted the attempt. At restart, the sync marked it `interrupted_run_recovered`; no catalog writes committed. |
| 2 | manual / success | 767 | 153 | 352 | 2026-11-23 **03:05:53.650137–03:08:05.886537 UTC**. The CLI exited 0; the checkpoint pointed to run 2. |

Fetched records are source records; inserts and updates are committed rows across four normalized tables. After run 2, the database held 667 canonical models, 773 catalog entries, 15 providers and 47 endpoints. The [dated quality checks](data_quality.md#live-quality-measurement) found zero duplicate natural-key groups and zero orphans in all three relationships. This is live recovery evidence, not a live zero-change replay or proof of a particular upstream price change.

At 03:14:22 UTC, the status SQL in [`scripts/status.py`](../scripts/status.py) ran in an **owner read-only transaction** (`recording-live-read-only.json`). It returned 2 attempts, 1 success, 153 inserts and 352 updates over seven days. Last successful check and last data change both read `2026-11-23 03:08:05.886537+00:00`; `stale` was false **at measurement**. This was not the status CLI logging in as the reader.

## Live reference baseline

The 03:14 UTC owner check returned 12 nonempty SQL results, but it was not the reader baseline. The 03:50 UTC [reader permission proof](schema.md#access-roles) also did **not** establish a baseline: its checker exited 1 with `reference_checker: null`. The separate `live-app-reader-reference-baseline.json`, recorded **2026-11-23 03:52:01 UTC** (November 22, 9:52 p.m. Central), identifies `app_reader` and `live_supabase`. Its 12 SQL answers were nonempty; Q13–Q15 were three should-decline specifications, not executed queries.

| Reference | Q01 | Q02 | Q03 | Q04 | Q05 | Q06 | Q07 | Q08 | Q09 | Q10 | Q11 | Q12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Result rows | 20 | 47 | 106 | 42 | 12 | 1 | 10 | 1 | 1 | 1 | 10 | 15 |

Q09 returned **773 catalog IDs and 667 canonical identities**. The checker bound its answers to the CSV and provenance file together (set SHA-256: `ea3ca7f42c5a23ba18a0791cc27fdbacf53d9ce60e371efc20079ef06915319c`). That November 22 receipt reported 15 questions and **0 verified baseline/running-list origins** for the earlier set. Running the SQL does not establish where a question came from.

At **04:00:25 UTC** the same-evening candidate-mode checker ran again as `app_reader` and exited 0: 12 SQL successes, 3 declines specified, no changed answer IDs (`checker-command-take.json`). This comparison had **not** followed two additional scheduled syncs. These receipts remain evidence for the earlier set. The [Part F source correction](../evals/README.md) changes the set hash without changing any question or SQL. The earlier answers are not used for comparisons against the corrected set.

### Corrected-set baseline: strict mode, hosted reader

At **10:50 p.m. CST on November 22** (04:50:02 UTC on November 23), `evals/check_reference.py --scope live_supabase --output baseline.json` ran without `--allow-candidate`. The standalone `app_reader` returned 12 nonempty SQL answers; Q13–Q15 require declines. The checker accepted all eight Part F sources (five published M2 queries and three November 22 choices). The [immutable baseline with all answers](evidence/m3-golden-baseline-2026-11-23T045002Z.json) identifies the corrected set as `9e2fd3d3a327391e0f652b55324cb82ecc3171fed4b5b61f94dd46638ce4c77a` (SHA-256). Q09 returned 773 catalog IDs and 667 canonical identities. This is the baseline to compare **after two subsequent scheduled updates**, not that later comparison.

The integrated source at commit `105d24c8194360d25302010597dadbb1c9ac8274` also passed 121 tests (zero skipped) and 14 CLI acceptance checks on disposable PostgreSQL. Those are local regression checks, not hosted syncs.

### Live workflow on the default branch

On November 22, 2026 (Central), the [production workflow](https://github.com/dmich-dev/bsad6153-michaud/blob/133d6e21e82fb1addf75eeffd9aa718ceca951b4/.github/workflows/sync.yml) was deployed to `main` without merging the older milestone branches. It reads anonymous OpenRouter metadata and uses a dedicated `catalog_sync_writer` through a main-only GitHub environment. The database owner password is not used by GitHub. The workflow is configured to run daily at **09:17 UTC** and also accepts an explicit manual dispatch. The daily interval limits source requests; an upstream outage or a delayed job can leave the data older than 24 hours.

The first [hosted manual run, 45115971859](https://github.com/dmich-dev/bsad6153-michaud/actions/runs/45115971859), succeeded on its first attempt. GitHub started it at **05:09:08 UTC on November 23**. The matching Supabase `sync_runs` row was **3**, `manual`, `success`, **771 fetched, 0 inserted, 12 updated**. Its database transaction finished at 05:12:20 UTC (11:12 p.m. Central on November 22). This is a different run from both the earlier locally started manual success and the push-triggered fixture. The [matched GitHub and database receipt](evidence/m3-first-hosted-manual-dispatch.json) records the timestamps and deployed commit.

This hosted dispatch verifies that the production job can fetch and commit changes, but does **not** count toward the three successful `schedule` events spanning 48 hours. The corrected-set baseline above also still needs a follow-up after two genuine scheduled updates.

## Historical local failure and reference checks — November 14, 2026

DRAFT / FOR REVIEW. Fresh assistant-run local PostgreSQL and synthetic loopback HTTP. No student prediction, live-source change or hosted scheduled event is claimed. Commands/output/run rows: `../../evidence/preseal-full/cli-acceptance/acceptance.json`. The preseal execution finished at `2026-11-14T06:39:30.358904+00:00`. This is a genuine current execution, not the older M3v2 receipt. Frozen final suites are separately indexed in the top-level READINESS and manifest.

## Predictions before actual CLI invocations

The following expectations were recorded by the assistant in the acceptance script before each CLI call. They are **not** student predictions. Fill `../../recording/PREDICTIONS.md` with the student's actual pre-run reasoning for later student runs.

| Test | Expected status | Expected fetched | Expected inserted | Expected updated | Actual run_id | Actual status | Actual inserted | Actual updated |
|---|---|---|---|---|---|---|---|---|
| first_full_snapshot_with_429_and_503 | success | 7 | 12 | 0 | 1 | success | 12 | 0 |
| immediate_rerun | success | 7 | 0 | 0 | 2 | success | 0 | 0 |
| simulated_source_change | success | 7 | 0 | 2 | 3 | success | 0 | 2 |
| unchanged_after_change | success | 7 | 0 | 0 | 4 | success | 0 | 0 |
| synthetic_invalid_api_key | failed | 0 | 0 | 0 | 5 | failed | 0 | 0 |
| bounded_three_attempt_outage | failed | 0 | 0 | 0 | 6 | failed | 0 | 0 |
| late_trigger_failure | failed | 7 | 0 | 0 | 7 | failed | 0 | 0 |
| recovery_after_process_kill | success | 7 | 0 | 1 | 9 | success | 0 | 1 |

## Exact resulting run rows

| run_id | started_at | finished_at | status | records_fetched | records_inserted | records_updated | error_message | trigger | table_counts |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11-14 00:39:24.932730-06:00 | 2026-11-14 00:39:25.056980-06:00 | success | 7 | 12 | 0 | None | manual | {'canonical_models': {'inserted': 3, 'updated': 0}, 'catalog_entries': {'inserted': 4, 'updated': 0}, 'providers': {'inserted': 2, 'updated': 0}, 'serving_endpoints': {'inserted': 3, 'updated': 0}} |
| 2 | 2026-11-14 00:39:25.336714-06:00 | 2026-11-14 00:39:25.436590-06:00 | success | 7 | 0 | 0 | None | manual | {'canonical_models': {'inserted': 0, 'updated': 0}, 'catalog_entries': {'inserted': 0, 'updated': 0}, 'providers': {'inserted': 0, 'updated': 0}, 'serving_endpoints': {'inserted': 0, 'updated': 0}} |
| 3 | 2026-11-14 00:39:25.583946-06:00 | 2026-11-14 00:39:25.709724-06:00 | success | 7 | 0 | 2 | None | manual | {'canonical_models': {'inserted': 0, 'updated': 0}, 'catalog_entries': {'inserted': 0, 'updated': 1}, 'providers': {'inserted': 0, 'updated': 0}, 'serving_endpoints': {'inserted': 0, 'updated': 1}} |
| 4 | 2026-11-14 00:39:25.849887-06:00 | 2026-11-14 00:39:25.945263-06:00 | success | 7 | 0 | 0 | None | manual | {'canonical_models': {'inserted': 0, 'updated': 0}, 'catalog_entries': {'inserted': 0, 'updated': 0}, 'providers': {'inserted': 0, 'updated': 0}, 'serving_endpoints': {'inserted': 0, 'updated': 0}} |
| 5 | 2026-11-14 00:39:26.228278-06:00 | 2026-11-14 00:39:26.389576-06:00 | failed | 0 | 0 | 0 | incomplete_source_snapshot | manual | {} |
| 6 | 2026-11-14 00:39:26.581284-06:00 | 2026-11-14 00:39:26.615221-06:00 | failed | 0 | 0 | 0 | incomplete_source_snapshot | manual | {} |
| 7 | 2026-11-14 00:39:26.759341-06:00 | 2026-11-14 00:39:26.828432-06:00 | failed | 7 | 0 | 0 | database_error | manual | {} |
| 8 | 2026-11-14 00:39:26.970284-06:00 | 2026-11-14 00:39:29.407119-06:00 | failed | 7 | 0 | 0 | interrupted_run_recovered | manual | {} |
| 9 | 2026-11-14 00:39:29.352304-06:00 | 2026-11-14 00:39:29.466864-06:00 | success | 7 | 0 | 1 | None | manual | {'canonical_models': {'inserted': 0, 'updated': 0}, 'catalog_entries': {'inserted': 0, 'updated': 1}, 'providers': {'inserted': 0, 'updated': 0}, 'serving_endpoints': {'inserted': 0, 'updated': 0}} |

## What the checks demonstrate

- Immediate rerun commits zero inserts and zero updates. Controlled catalog context plus endpoint price changes update only those two records; unchanged audits stay equal.
- A late PostgreSQL trigger failure rolls the entire data transaction back. Complete data-row fingerprints before/after match; no partial catalog/provider/endpoint writes remain. This trigger exists only in the disposable fixture, never Supabase.
- The invalid key is a synthetic loopback 401. Its credential text never appears in output. A temporary outage exhausts exactly three configured attempts; the fast fixture supplies Retry-After zero. The separate gap probes exercise the real HTTP 429/503 path and the production exponential fallback function.
- A real sync CLI process is SIGKILLed while a real PostgreSQL transaction is paused. The observer sees seven fetched and zero committed rows. The next successful sync marks the unfinished attempt failed with interrupted_run_recovered and commits the pending change without duplicates. Exact process exit and recovery row are in the receipt. No fresh SIGTERM test is claimed here.
- If the database cannot be reached or its audit write fails, a log row cannot be guaranteed. The CLI/CI nonzero outcome is the fallback evidence; do not invent a missing run row.
- M3v2's hardened real-postcommit interruption/driver-error and ownership/PUBLIC-column/provenance regressions remain in the suite and are rerun on this candidate. New reconciliation regression tests cover M3 whitespace-only route rejection and the golden Q04 timezone boundaries.

## Golden checks

All 12 reference SQL queries ran as actual app_reader; three should-decline specifications have intentionally empty SQL. Initial/later outputs are immutable files in the receipt directory. The actual local changed IDs were `Q01, Q02, Q04, Q07, Q10`; unchanged IDs were `Q03, Q05, Q06, Q08, Q09, Q11, Q12`.

Q01/Q07 reflect the controlled context update and Q02 the controlled endpoint rate. Q04 includes changed stored observation metadata; Q10 includes latest successful check time/counters. Those latter answer changes do not prove new source facts or newly added catalog records. No record count growth is invented.

On November 14, all 15 CSV sources were `other`, and strict checking refused the unverified eight-origin requirement. `--allow-candidate` labeled that run as technical review only. The worksheet was not a backdated M1 log. As of November 14, the live baseline and the later comparison after at least two **additional genuine scheduled syncs** were missing. See the separate November 22 live baseline above; the scheduled comparison is still outstanding. Local manual calls, trigger strings and simulated times do not close that gate.
