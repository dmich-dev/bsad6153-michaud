# Part G: actual local failure and reference checks

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

All 15 current CSV sources remain other, and strict checking correctly refuses the unverified eight-origin requirement. `--allow-candidate` labels technical review only. `running_questions_2026-11-14.md` is a current selection worksheet, not a backdated M1 log. The real required live baseline and later comparison after at least two **additional genuine scheduled syncs** remain missing. Local manual calls, trigger strings and simulated times do not close that gate.
