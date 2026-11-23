# Part E: data quality and coverage

## Live quality measurement

**Measured November 22, 2026 at 9:10 p.m. Central (2026-11-23 03:10:02.968784 UTC)**, after manual sync run 2. All ten named SELECTs in [`db/quality_checks.sql`](../db/quality_checks.sql) ran on live Supabase in an **owner read-only transaction**. The dated results below come from `live-quality-owner-read-only.json`, not from the synthetic fixture or the later standalone reader login. `sync_state` is owner-only and was not counted by the five-table row-count query.

**What the coverage gap means.** On November 22 (Central), **0 of 61 image-only catalog entries (0.00%)** had a collected route, versus **17 of 478 text-only entries (3.56%)**. The collection step selects recent text/tool-capable models for route lookups. A chatbot comparing providers should say “no route collected for this entry,” not “this model has no provider.” The denominator is catalog entries in each exact output-modality array, not endpoints or all available providers. The same model can have aliases; those catalog IDs are not independent architectures.

**What was cleaned, rejected or retained.** Unknown typed prices stay NULL, never “free”; negative sentinel values are preserved in the raw pricing data, not exposed as usable rates. A null rate alone does not identify its cause. Exact source IDs and aliases are retained so requestable variants survive; conflicting duplicate identities and missing fetched parents are rejected rather than silently repaired. Foreign keys protect stored relationships. Old or unselected rows remain last-known observations, not certified availability. These rules explain why zero natural-key duplicates can coexist with 106 shared identity groups (November 22, Central).

### Stored rows

SQL: `row_counts` · Measured 2026-11-22 (Central).

| table name | rows |
| --- | --- |
| canonical_models | 667 |
| catalog_entries | 773 |
| providers | 15 |
| serving_endpoints | 47 |
| sync_runs | 2 |

### Catalog null rates

SQL: `important_nulls` · Measured 2026-11-22 (Central).

| field | total | null count | null percent |
| --- | --- | --- | --- |
| canonical_model_id | 773 | 0 | 0.00 |
| catalog_id | 773 | 0 | 0.00 |
| completion_usd_per_token | 773 | 8 | 1.03 |
| context_length | 773 | 0 | 0.00 |
| name | 773 | 0 | 0.00 |
| output_modalities | 773 | 0 | 0.00 |
| prompt_usd_per_token | 773 | 8 | 1.03 |
| supported_parameters | 773 | 0 | 0.00 |

### Duplicate natural-key groups

SQL: `natural_duplicates` · Measured 2026-11-22 (Central).

| natural key | duplicate groups |
| --- | --- |
| canonical_slug | 0 |
| catalog_id | 0 |
| provider_name | 0 |
| endpoint_composite | 0 |

### Catalog aliases

SQL: `aliases` · Measured 2026-11-22 (Central).

| shared canonical groups | catalog ids in shared groups |
| --- | --- |
| 106 | 212 |

### Same display name across distinct catalog IDs

SQL: `same_label` · Measured 2026-11-22 (Central).

| same name different id groups |
| --- |
| 0 |

### Range and consistency checks

SQL: `anomalies` · Measured 2026-11-22 (Central).

| issue | rows |
| --- | --- |
| negative_catalog_rates | 0 |
| negative_endpoint_rates | 0 |
| negative_context | 0 |
| endpoint_output_exceeds_context | 0 |
| catalog_creation_after_observation | 0 |
| unknown_output_modality_labels | 0 |

### Missing parents

SQL: `orphans` · Measured 2026-11-22 (Central).

| relationship | orphans |
| --- | --- |
| catalog_canonical | 0 |
| endpoint_catalog | 0 |
| endpoint_provider | 0 |

### Entries with at least one collected route

SQL: `coverage` · Measured 2026-11-22 (Central).

| output modalities | catalog entries | entries with endpoints | coverage percent |
| --- | --- | --- | --- |
| `["decisions"]` | 48 | 0 | 0.00 |
| `["embeddings"]` | 47 | 0 | 0.00 |
| `["image"]` | 61 | 0 | 0.00 |
| `["image", "text"]` | 10 | 0 | 0.00 |
| `["rerank"]` | 13 | 0 | 0.00 |
| `["speech"]` | 42 | 0 | 0.00 |
| `["text"]` | 478 | 17 | 3.56 |
| `["text", "audio"]` | 4 | 0 | 0.00 |
| `["text", "image"]` | 3 | 0 | 0.00 |
| `["text", "video"]` | 2 | 0 | 0.00 |
| `["transcription"]` | 31 | 0 | 0.00 |
| `["video"]` | 34 | 0 | 0.00 |

### Endpoint nulls

SQL: `endpoint_nulls` · Measured 2026-11-22 (Central).

| endpoints | null context | null prompt | null completion | null tier |
| --- | --- | --- | --- | --- |
| 47 | 0 | 0 | 0 | 32 |

### Age of the stored payloads versus last successful check

SQL: `freshness` · Measured 2026-11-22 (Central).

| oldest stored payload observation | newest stored payload observation | last successful check |
| --- | --- | --- |
| 2026-11-07 19:37:26.086181+00:00 | 2026-11-23 03:06:13.181774+00:00 | 2026-11-23 03:08:05.886537+00:00 |

**Freshness and ownership.** On November 22 (Central), a successful check coexisted with retained payloads last observed November 7. A daily target is not a maximum age: an unselected route or a pipeline that keeps failing can remain stale indefinitely. The proposed pipeline owner would investigate a missed refresh; the app owner would show the last successful check, payload observation time and coverage limits. This run does not demonstrate scheduled alert delivery. See [lineage and field meanings](data_dictionary.md#lineage).

<details>
<summary>Actual SQL for all ten live measurements</summary>

```sql
-- check: row_counts
SELECT now() AS measured_at, 'canonical_models' AS table_name,count(*) AS rows FROM canonical_models
UNION ALL SELECT now(),'catalog_entries',count(*) FROM catalog_entries
UNION ALL SELECT now(),'providers',count(*) FROM providers
UNION ALL SELECT now(),'serving_endpoints',count(*) FROM serving_endpoints
UNION ALL SELECT now(),'sync_runs',count(*) FROM sync_runs;

-- check: important_nulls
SELECT now() AS measured_at,v.field,count(*) AS total,
       count(*) FILTER (WHERE v.missing) AS null_count,
       round(100.0*count(*) FILTER (WHERE v.missing)/nullif(count(*),0),2) AS null_percent
FROM catalog_entries c CROSS JOIN LATERAL (VALUES
 ('catalog_id',c.catalog_id IS NULL),('canonical_model_id',c.canonical_model_id IS NULL),
 ('name',c.name IS NULL),('context_length',c.context_length IS NULL),
 ('prompt_usd_per_token',c.prompt_usd_per_token IS NULL),('completion_usd_per_token',c.completion_usd_per_token IS NULL),
 ('output_modalities',c.output_modalities IS NULL),('supported_parameters',c.supported_parameters IS NULL)
) v(field,missing) GROUP BY v.field ORDER BY v.field;

-- check: natural_duplicates
SELECT now() AS measured_at,'canonical_slug' AS natural_key,count(*) AS duplicate_groups
FROM (SELECT canonical_slug FROM canonical_models GROUP BY canonical_slug HAVING count(*)>1) d
UNION ALL SELECT now(),'catalog_id',count(*) FROM (SELECT catalog_id FROM catalog_entries GROUP BY catalog_id HAVING count(*)>1) d
UNION ALL SELECT now(),'provider_name',count(*) FROM (SELECT provider_name FROM providers GROUP BY provider_name HAVING count(*)>1) d
UNION ALL SELECT now(),'endpoint_composite',count(*) FROM (SELECT catalog_entry_id,provider_id,tag,name,service_tier FROM serving_endpoints GROUP BY catalog_entry_id,provider_id,tag,name,service_tier HAVING count(*)>1) d;

-- check: aliases
SELECT now() AS measured_at,count(*) AS shared_canonical_groups,coalesce(sum(entries),0) AS catalog_ids_in_shared_groups
FROM (SELECT canonical_model_id,count(*) AS entries FROM catalog_entries WHERE canonical_model_id IS NOT NULL GROUP BY canonical_model_id HAVING count(*)>1) g;

-- check: same_label
SELECT now() AS measured_at,count(*) AS same_name_different_id_groups
FROM (SELECT name FROM catalog_entries WHERE name IS NOT NULL GROUP BY name HAVING count(DISTINCT catalog_id)>1) g;

-- check: anomalies
SELECT now() AS measured_at,'negative_catalog_rates' AS issue,count(*) AS rows FROM catalog_entries WHERE prompt_usd_per_token<0 OR completion_usd_per_token<0
UNION ALL SELECT now(),'negative_endpoint_rates',count(*) FROM serving_endpoints WHERE prompt_usd_per_token<0 OR completion_usd_per_token<0
UNION ALL SELECT now(),'negative_context',count(*) FROM catalog_entries WHERE context_length<0
UNION ALL SELECT now(),'endpoint_output_exceeds_context',count(*) FROM serving_endpoints WHERE max_completion_tokens>context_length
UNION ALL SELECT now(),'catalog_creation_after_observation',count(*) FROM catalog_entries WHERE catalog_created_at>source_observed_at
UNION ALL SELECT now(),'unknown_output_modality_labels',count(*) FROM catalog_entries c CROSS JOIN LATERAL unnest(c.output_modalities) m WHERE m NOT IN ('text','image','embeddings','audio','video','rerank','decisions','speech','transcription');

-- check: orphans
SELECT now() AS measured_at,'catalog_canonical' AS relationship,count(*) AS orphans FROM catalog_entries c LEFT JOIN canonical_models m USING(canonical_model_id) WHERE c.canonical_model_id IS NOT NULL AND m.canonical_model_id IS NULL
UNION ALL SELECT now(),'endpoint_catalog',count(*) FROM serving_endpoints e LEFT JOIN catalog_entries c USING(catalog_entry_id) WHERE c.catalog_entry_id IS NULL
UNION ALL SELECT now(),'endpoint_provider',count(*) FROM serving_endpoints e LEFT JOIN providers p USING(provider_id) WHERE p.provider_id IS NULL;

-- check: coverage
SELECT now() AS measured_at,c.output_modalities,count(*) AS catalog_entries,
       count(*) FILTER (WHERE EXISTS(SELECT 1 FROM serving_endpoints e WHERE e.catalog_entry_id=c.catalog_entry_id)) AS entries_with_endpoints,
       round(100.0*count(*) FILTER (WHERE EXISTS(SELECT 1 FROM serving_endpoints e WHERE e.catalog_entry_id=c.catalog_entry_id))/count(*),2) AS coverage_percent
FROM catalog_entries c GROUP BY c.output_modalities ORDER BY c.output_modalities;

-- check: endpoint_nulls
SELECT now() AS measured_at,count(*) AS endpoints,
       count(*) FILTER (WHERE context_length IS NULL) AS null_context,
       count(*) FILTER (WHERE prompt_usd_per_token IS NULL) AS null_prompt,
       count(*) FILTER (WHERE completion_usd_per_token IS NULL) AS null_completion,
       count(*) FILTER (WHERE service_tier IS NULL) AS null_tier
FROM serving_endpoints;

-- check: freshness
SELECT now() AS measured_at,
       (SELECT min(source_observed_at) FROM catalog_entries) AS oldest_stored_payload_observation,
       (SELECT max(source_observed_at) FROM catalog_entries) AS newest_stored_payload_observation,
       (SELECT max(finished_at) FROM sync_runs WHERE status='success') AS last_successful_check;
```

</details>

## Historical local measurements — November 14, 2026

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

A chatbot could unfairly omit uninspected models/providers by treating absence from this recency/text/tool endpoint sample as no provider availability. Use the actual coverage denominator and date, disclose the selected sample, separate unknown from unavailable, and decline universal provider rankings. This is entity-representation bias, not measured human-demographic discrimination. The November 22 live measurements above used an owner read-only transaction. Do not describe them as a standalone `app_reader` quality run.

## Part H: lineage, freshness and ownership

Catalog metadata GET pages -> origin/pagination checks -> exact JSON/type/price validation -> canonical parents -> catalog entries. Selected details GETs -> fetched-parent validation -> providers -> serving endpoints. Parameterized upserts compare canonical raw-payload hashes. A durable attempt surrounds one atomic data/success/checkpoint transaction. Reader-only status, quality and golden scripts consume data and sync_runs, not owner-only sync_state. `data_dictionary.md` gives the field transformations.

The healthy catalog refresh target is daily plus source visibility lag, queue delay and runtime. Worst-case freshness is **unbounded** under unbounded failures/delays. Retained unselected endpoint rows also have no finite age bound even if the catalog checks succeed daily. Latest successful check and last changed-payload observation are different facts; show both.

November 14 change log: reconciled the latest published M2 preflight/privacy/runtime/timezone fixes, retained M3 role/audit/provenance hardening, and corrected M3 route preflight and golden Q04 elapsed-hour semantics with RED/GREEN evidence. Actual synthetic source changes and process-kill recovery were exercised; no hosted-source quirk or live price change is asserted. Proposed operational owner is a data-platform pipeline owner/on-call operator, with the app owner responsible for stale/coverage warnings. Verify Actions failure delivery after approved activation; no stale monitor is deployed.
