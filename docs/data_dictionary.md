# Milestone 3 data dictionary

DRAFT / FOR REVIEW. Assistant-prepared November 12, 2026. Historical Milestone 2 definitions remain in `schema.md`; this document describes the isolated M3 extension. That November 12 draft did not claim a cloud schema change or student acceptance. The [change log](#change-log) records the later live migration and manual sync.

## Data entities

| Table | One row means | Natural identity | Mutation behavior |
|---|---|---|---|
| canonical_models | Exact source canonical identity, not a verified model architecture | canonical_slug | New identities insert; identity-only parents have no non-key payload to update |
| catalog_entries | Exact catalog/request ID, including aliases or variants | catalog_id | Hash-different raw metadata updates typed columns and last_updated_at |
| providers | Exact returned serving-provider name, not the model author prefix | provider_name | New exact names insert; a renamed provider is a new identity |
| serving_endpoints | A collected last-known provider offering for one catalog entry | catalog_entry_id, provider_id, tag, name, service_tier | Composite conflict uses NULLS NOT DISTINCT; changed metadata updates in place |

The four original table definitions are unchanged. A missing optional value remains SQL NULL. No identifier is trimmed, repaired or substituted. Zero is distinct from unknown. Prices are parsed from exact decimal strings; negative sentinels remain in raw JSON/pricing but become NULL usable rates. Non-finite rates, integer booleans, bad ranges, malformed arrays and conflicting/orphan identities are rejected. Catalog Unix `created` is an addition/creation label, not a source modification cursor. A raw JSONB record is a parsed payload, not the original HTTP byte stream.

## sync_runs

| Column | Meaning |
|---|---|
| run_id | Generated bigint attempt ID |
| started_at | Database clock when the durable attempt row is created |
| finished_at | Terminal completion/recovery time; NULL while unfinished |
| status | CHECK-constrained success, partial or failed |
| records_fetched | Catalog plus endpoint records collected; durably saved before applying data |
| records_inserted, records_updated | Committed changes across all four normalized data tables, never attempted writes rolled back |
| error_message | Fixed safe category only; no exception text, URL, header, API key or source string |
| trigger | CHECK-constrained manual or schedule; a label is not independent evidence of a hosted schedule event |
| table_counts | Per-table inserted/updated counts for a committed success |

An unfinished attempt initially uses `partial` with `attempt_in_progress`; it is not a successful run. A completed incomplete retrieval is partial only if some records were fetched, with zero committed changes. A retrieval that obtains nothing is failed. On process death, the next exclusive sync marks older unfinished rows failed with `interrupted_run_recovered`. That `finished_at` is recovery time, not an invented time of death. Failed connections, missing schema or a destroyed connection can prevent a row from being written at all; the CLI/CI failure is the necessary fallback.

## sync_state

Owner-only checkpoint keyed by source. `last_success_run_id` references the terminal success row, `observed_at` is a completed retrieval observation, `snapshot_sha256` covers sorted catalog/endpoint payloads, and `mode` is constrained to `full_snapshot_hash_diff`. It is updated only in the same transaction as successful data changes. It is not exposed to `app_reader` and does not pretend to be an API delta cursor. The inspected OpenRouter references do not document a change-since cursor for these resources (OpenRouter, n.d.-a, n.d.-b).

## Lineage

```text
OpenRouter all-modalities catalog pages
  -> inherited origin-locked GET, bounded HTTP retry and pagination checks
  -> exact catalog IDs, complete total/boundary checks, metadata validation
  -> canonical_slug parents -> canonical_models
  -> Decimal prices, UTC creation time, arrays, raw JSON and hash -> catalog_entries
Recent eligible text/tool details links, selected from that catalog
  -> origin-locked endpoint GETs -> validate fetched model_id parent
  -> exact provider_name parents -> providers
  -> provisional composite offering key, Decimal prices, raw JSON and hash -> serving_endpoints
Each attempt -> durable sync_runs row
Validated full snapshot -> one transaction for all four tables, terminal success and sync_state
app_reader -> SELECT on four data tables and sync_runs -> status, quality and golden checks
```

`source_observed_at` is the successful fetch finish time for the payload that was inserted or last changed. It is deliberately unchanged on an identical replay, as is `last_updated_at`. `first_seen_at` is database insertion time, not source creation. The latest successful `sync_runs.finished_at` is the check freshness signal. OpenRouter pages and endpoint requests are not an atomic upstream snapshot, so even a complete, consistent-count fetch is not proof that every source record existed simultaneously at one instant.

No row-level price history, task outcomes, private account information, verified HERMES interoperability or provider-completeness claim is introduced. Missing/newly unselected routes are retained as last-known records; absent is not deleted and not globally unavailable. A renamed composite endpoint can create a new row while the older row remains. Keep these limitations visible in chatbot answers.

## Freshness guarantee

Daily cron is a refresh target, not an unconditional guarantee. In a successful, bounded-delay scenario, catalog age is approximately the 24-hour cadence plus upstream visibility lag, fetch/runtime and queue delay. Worst-case age is unbounded when source access, the database or the scheduler can fail indefinitely. Retained endpoint rows outside the newest-ten sample can also age indefinitely during otherwise healthy catalog runs. Warn from last successful check time and the specific payload observation, not from a freshly generated report timestamp. GitHub can delay or drop scheduled jobs and only schedules default-branch workflows (GitHub, n.d.).

## Ownership

Proposed company ownership, not an assignment of real staff: a data-platform/pipeline owner maintains credentials, source contracts, migrations and retry policy; an on-call data-platform operator receives job-failure and stale-check alerts; the application owner surfaces stale/limited-coverage warnings. Check successful catalog observation daily and investigate when it exceeds the target plus a reviewed tolerance. GitHub notification recipients/settings must be verified after activation. A separate stale-data monitor is still an operational follow-up, not a shipped service in this draft.

## Change log

November 12, 2026, assistant observations: the isolated extension now has changed-only upserts and durable attempt accounting rather than the frozen insert-only M2 loader. Synthetic tests demonstrated catalog context changes, provider-rate changes and safe process-death recovery. These are controlled local examples, not changes observed in live scheduled OpenRouter data. Actual hosted-run quirks remain unknown until approval and real collection.

November 22, 2026 (Central), live manual sync. `pre-migration.json` and `migration-verified.json` show the migration left all four preexisting catalog tables unchanged. The subsequent manual sync did change them (`manual-sync-retry-readback.json`):

| Stored entity | Before migration | After manual run 2 |
|---|---:|---:|
| `canonical_models` | 616 | 667 |
| `catalog_entries` | 705 | 773 |
| `providers` | 9 | 15 |
| `serving_endpoints` | 19 | 47 |

Run 2 logged 767 fetched source records, 153 inserted normalized rows and 352 updated normalized rows; the checkpoint named run 2. These are not counts of newly released models. The [quality report](data_quality.md#live-quality-measurement) illustrates the distinction between *check time* and *payload age*: after the November 22 refresh, the oldest stored catalog payload observation was still November 7. The failure of run 1 and recovery by run 2 are documented in [sync tests](sync_tests.md#live-manual-sync-and-recovery). Nothing in this change log attributes a field-level change to a particular provider or to a scheduled event.

## References

GitHub (n.d.) and OpenRouter (n.d.-a, n.d.-b), official references checked November 12, 2026. Full source metadata is in `../../evidence/pre-fix/primary-source-checks.json` and the repository README References section.
