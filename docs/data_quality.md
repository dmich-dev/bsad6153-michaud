# Part E: measured quality, November 14, 2026

DRAFT / FOR REVIEW. These fresh measurements are **local synthetic acceptance**, not live Supabase or scheduled-source observations. Actor: assistant. Actual database user: app_reader, PostgreSQL 17.11. Each SQL result below carries its own actual transaction measurement timestamp. Complete receipt: `../../evidence/preseal-full/cli-acceptance/quality-local.json`; SQL: `db/quality_checks.sql` (named `-- check:` blocks). No old M3 count is presented as a fresh run.

## aliases

SQL basis: `db/quality_checks.sql`, `-- check: aliases`.

| measured_at | shared_canonical_groups | catalog_ids_in_shared_groups |
|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | 1 | 2 |

## anomalies

SQL basis: `db/quality_checks.sql`, `-- check: anomalies`.

| measured_at | issue | rows |
|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | negative_catalog_rates | 0 |
| 2026-11-14 00:39:30.331616-06:00 | negative_endpoint_rates | 0 |
| 2026-11-14 00:39:30.331616-06:00 | negative_context | 0 |
| 2026-11-14 00:39:30.331616-06:00 | endpoint_output_exceeds_context | 0 |
| 2026-11-14 00:39:30.331616-06:00 | catalog_creation_after_observation | 0 |
| 2026-11-14 00:39:30.331616-06:00 | unknown_output_modality_labels | 0 |

## coverage

SQL basis: `db/quality_checks.sql`, `-- check: coverage`.

| measured_at | output_modalities | catalog_entries | entries_with_endpoints | coverage_percent |
|---|---|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | ['image'] | 1 | 0 | 0.00 |
| 2026-11-14 00:39:30.331616-06:00 | ['text'] | 3 | 2 | 66.67 |

## endpoint_nulls

SQL basis: `db/quality_checks.sql`, `-- check: endpoint_nulls`.

| measured_at | endpoints | null_context | null_prompt | null_completion | null_tier |
|---|---|---|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | 3 | 0 | 0 | 0 | 3 |

## freshness

SQL basis: `db/quality_checks.sql`, `-- check: freshness`.

| measured_at | oldest_stored_payload_observation | newest_stored_payload_observation | last_successful_check |
|---|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | 2026-11-14 00:39:25.044925-06:00 | 2026-11-14 00:39:29.454191-06:00 | 2026-11-14 00:39:29.466864-06:00 |

## important_nulls

SQL basis: `db/quality_checks.sql`, `-- check: important_nulls`.

| measured_at | field | total | null_count | null_percent |
|---|---|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | canonical_model_id | 4 | 0 | 0.00 |
| 2026-11-14 00:39:30.331616-06:00 | catalog_id | 4 | 0 | 0.00 |
| 2026-11-14 00:39:30.331616-06:00 | completion_usd_per_token | 4 | 1 | 25.00 |
| 2026-11-14 00:39:30.331616-06:00 | context_length | 4 | 1 | 25.00 |
| 2026-11-14 00:39:30.331616-06:00 | name | 4 | 1 | 25.00 |
| 2026-11-14 00:39:30.331616-06:00 | output_modalities | 4 | 0 | 0.00 |
| 2026-11-14 00:39:30.331616-06:00 | prompt_usd_per_token | 4 | 2 | 50.00 |
| 2026-11-14 00:39:30.331616-06:00 | supported_parameters | 4 | 0 | 0.00 |

## natural_duplicates

SQL basis: `db/quality_checks.sql`, `-- check: natural_duplicates`.

| measured_at | natural_key | duplicate_groups |
|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | canonical_slug | 0 |
| 2026-11-14 00:39:30.331616-06:00 | catalog_id | 0 |
| 2026-11-14 00:39:30.331616-06:00 | provider_name | 0 |
| 2026-11-14 00:39:30.331616-06:00 | endpoint_composite | 0 |

## orphans

SQL basis: `db/quality_checks.sql`, `-- check: orphans`.

| measured_at | relationship | orphans |
|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | catalog_canonical | 0 |
| 2026-11-14 00:39:30.331616-06:00 | endpoint_catalog | 0 |
| 2026-11-14 00:39:30.331616-06:00 | endpoint_provider | 0 |

## row_counts

SQL basis: `db/quality_checks.sql`, `-- check: row_counts`.

| measured_at | table_name | rows |
|---|---|---|
| 2026-11-14 00:39:30.331616-06:00 | canonical_models | 3 |
| 2026-11-14 00:39:30.331616-06:00 | catalog_entries | 4 |
| 2026-11-14 00:39:30.331616-06:00 | providers | 2 |
| 2026-11-14 00:39:30.331616-06:00 | serving_endpoints | 3 |
| 2026-11-14 00:39:30.331616-06:00 | sync_runs | 9 |

## same_label

SQL basis: `db/quality_checks.sql`, `-- check: same_label`.

| measured_at | same_name_different_id_groups |
|---|---|
| 2026-11-14 00:39:30.331616-06:00 | 0 |

## Decisions and fairness

Preserve exact natural identities, provider/route/tier distinctions, raw JSON and decimal prices. Negative unknown-price sentinels become NULL usable rates, never zero/free. Reject invalid shapes, non-finite or out-of-range numbers, NUL/unpaired-surrogate JSON, whitespace-only route identities, conflicting duplicates and missing fetched parents before the data writer. Healthy Unicode, literal backslash escapes and meaningful whitespace survive unchanged. Foreign keys and one transaction prevent orphaned/partial committed data.

Retain absent or no-longer-selected entries as last-known observations because no source deletion/modification history contract was established. A renamed route is a new natural identity. Do not infer that old retained routes remain available, or that a missing/unqueried route has no provider.

The dated **synthetic** coverage result above shows the test image group has no inspected endpoints while the test text group has partial coverage. It proves that the SQL detects a gap; it is not an OpenRouter fairness finding. The unchanged latest M2 quality report is preserved separately in `data_quality_m2_baseline.md`, including its genuine November 7 source observation and later student-input clarification. That historical dataset had 8 of 705 catalog IDs covered by collected endpoints (1.13%); its dated full group breakdown is in that preserved report. This is not remeasured cloud M3 evidence.

A chatbot could unfairly omit uninspected models/providers by treating absence from this recency/text/tool endpoint sample as no provider availability. Use the actual coverage denominator and date, disclose the selected sample, separate unknown from unavailable, and decline universal provider rankings. This is entity-representation bias, not measured human-demographic discrimination. Run the full suite against the approved live target as app_reader before claiming a live M3 quality report.

## Part H: lineage, freshness and ownership

Catalog metadata GET pages -> origin/pagination checks -> exact JSON/type/price validation -> canonical parents -> catalog entries. Selected details GETs -> fetched-parent validation -> providers -> serving endpoints. Parameterized upserts compare canonical raw-payload hashes. A durable attempt surrounds one atomic data/success/checkpoint transaction. Reader-only status, quality and golden scripts consume data and sync_runs, not owner-only sync_state. `data_dictionary.md` gives the field transformations.

The healthy catalog refresh target is daily plus source visibility lag, queue delay and runtime. Worst-case freshness is **unbounded** under unbounded failures/delays. Retained unselected endpoint rows also have no finite age bound even if the catalog checks succeed daily. Latest successful check and last changed-payload observation are different facts; show both.

November 14 change log: reconciled the latest published M2 preflight/privacy/runtime/timezone fixes, retained M3 role/audit/provenance hardening, and corrected M3 route preflight and golden Q04 elapsed-hour semantics with RED/GREEN evidence. Actual synthetic source changes and process-kill recovery were exercised; no hosted-source quirk or live price change is asserted. Proposed operational owner is a data-platform pipeline owner/on-call operator, with the app owner responsible for stale/coverage warnings. Verify Actions failure delivery after approved activation; no stale monitor is deployed.
