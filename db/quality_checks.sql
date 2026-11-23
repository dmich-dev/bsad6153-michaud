-- DRAFT / FOR REVIEW. Each result includes its actual measurement timestamp.
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
