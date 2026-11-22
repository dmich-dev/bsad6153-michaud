# Milestone 3 PR1: latest-M2 base plus Parts A-D

DRAFT / FOR REVIEW, November 14, 2026. **No publication, cloud activation or submission is authorized.** Begin with `../READINESS.md`, `../ACTIVATION_PLAN.md` and `../recording/RECORDING_CUE.md` rather than older milestone recording instructions.

## Exact base and retained hardening

The effective base is the latest verified published M2 draft PR #3 head `42ce2521bab78f68376f0ab66244bdc2f51f698e`, not an assumption that main contains M2. The canonical worktree is read-only. Inputs are copied and hash-checked under `../inputs/`; .env was never read or copied. Per-file reconciliation is recorded in `../reconciliation/`.

The final M2 loader, checker and business SQL are imported exactly, along with all missing declared M2 base files and regression tests. M3's password-free role hardening, post-commit durable audit and exact/distinct origin validation are retained. Narrow new fixes reject whitespace-only M3 route identities without normalizing valid identities and preserve the 720-elapsed-hour contract in golden Q04. Current manifests and fresh tests, not the older 67/60 counts, establish this revision.

## Parts A-D

- `db/milestone3.sql`: constrained sync_runs and private observation checkpoint. Apply only after explicit target approval, over the existing M2 schema; do not recreate its tables.
- `db/roles.sql`: SELECT on the four data tables and sync_runs only. No password; fail closed on existing elevated membership, database/schema/relation ownership and inherited PUBLIC write/CREATE or column privileges. It does not silently alter unrelated ACLs.
- `ingest/sync.py`: source fetch plus parameterized natural-key ON CONFLICT upserts; hash-difference WHERE skips identical payloads and leaves their last_updated_at unchanged. Parents precede children. Data, terminal success and checkpoint commit together; a post-commit interruption cannot rewrite durable success as failed.
- Creation time is not a change watermark. The inspected API has no documented modification cursor, so mode `full_snapshot_hash_diff` honestly downloads the catalog plus rolling ten-model text/tool endpoint subset and compares payload hashes. The saved checkpoint is a successful observation, not a fabricated delta cursor. Retain missing/unselected records as last-known, not asserted current availability.
- `scripts/status.py`: actual reader-only last successful check, last data change and seven-day counts. An unreachable database cannot guarantee its own failed-attempt row; nonzero CLI/CI is the fallback.
- `.github/workflows/sync.yml`: proposed daily 09:17 UTC cron, workflow_dispatch, secrets passed as environment references, contents:read, concurrency without cancellation, 15-minute job deadline and visible nonzero sync failure. Daily metadata collection bounds load; minute 17 avoids the start-of-hour peak. It is not a promise of finite worst-case freshness or exactly timed runs. No workflow exists remotely at the recorded preflight.

## Parts E-H and honest gaps

`db/quality_checks.sql`/`scripts/quality_report.py` produce dated read-only measurements; `docs/data_quality.md` is actual local synthetic evidence, with latest historical M2 quality preserved separately. `evals/golden_questions.csv` has 15 candidates, 12 working SQL references and three decline specifications. All sources are other until real running-list choices and provenance exist. The checker uses app_reader, a read-only repeatable-read transaction, bounded queries and immutable outputs. `--allow-candidate` is not acceptance.

`docs/sync_tests.md` retains real local rerun/change/rollback/key/outage/kill/recovery outcomes. `docs/data_dictionary.md` describes lineage/transforms/freshness/ownership. `docs/running_questions_2026-11-14.md` lets the student make current choices without falsifying M1 history. AI review and recording remain the student's genuine work.

## Verification and one-launch local practice

On djserver, `../.review-venv/` contains the pinned `requirements-sync.txt` dependencies. `../review/run_isolated.py` scrubs DB/libpq environment, disables dotenv, starts its own socket-only unprivileged PostgreSQL 17.11 and stops it afterward. Never point tests at Supabase or an application database. Current complete/A-D/CLI/gap receipts and source hashes are indexed in `../CURRENT_MANIFEST.json`.

One actual local rehearsal launch is documented in `../recording/RECORDING_CUE.md`; it waits at READY, runs real local CLIs after RUN/Enter, prints actual outputs and holds them until finished. It never uses live credentials or activates anything.

## Gates that local tests cannot close

Actual source/public-display approval; M1/M2-to-main integration and dispatch bootstrap decision; approved cloud migration/role/private secrets; actual Session-pooler app_reader proof and Data API-off verification; two real M3 PRs; a hosted manual smoke; three genuine successful schedule events spanning at least 48 actual hours; live golden baseline followed by at least two additional genuine scheduled syncs and a later check; live M3 quality; authentic student selection/predictions/review and own 4-6 minute recording. No secret or submission action is implicit in preparation.

The November 18, 2026 workflow guidance and November 22, 2026 11:59:59 PM America/Chicago deadline are from the supplied live prompt. Primary API/GitHub/Supabase checks are in `../review/PRIMARY-REFERENCES.md`; permissions and actual target state remain separately unverified.

## PR1 scope

This standalone copy excludes M3 E-H quality/golden scripts and tests. References to E-H above describe the full candidate only; do not add those files to this early PR. Exact differences are in the top-level PR1 overlay allowlist.
