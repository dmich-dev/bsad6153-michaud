-- DRAFT / FOR REVIEW. ALL questions below are PROPOSED, confirmation pending.
-- baseline_log.md contains no recorded wished-I-knew questions. These derive from
-- its cost/context/tool/HERMES criteria, not invented student events or surprises.
-- Metadata is not a coding benchmark or proof of HERMES interoperability.

-- Q1: PROPOSED - Which text/tool entries have >=128k advertised context and the
-- lowest base-token estimate for an illustrative 1M input + 250k output workload?
-- Workload and threshold are assistant examples, NOT measured student consumption.
-- Volumes are illustrative totals across requests, not one prompt proven to fit.
-- Other units, conditional pricing, routing, retries and subscriptions are excluded.
-- Student surprise, reported November 12, 2026 after viewing the real results:
-- "Honeslty the amount of free models i didn't even know existed to be honest is probably the biggest one."
-- The number of previously unknown free options was the student's stated surprise;
-- no numeric prior expectation or quality judgment was supplied or inferred.
-- In this dated result, 13 of the 20 returned catalog entries had zero base-token
-- rates. This is not the total free-model count or proof of unrestricted access.
SELECT c.catalog_id, m.canonical_slug,
       c.prompt_usd_per_token * 1000000 AS prompt_usd_per_million,
       c.completion_usd_per_token * 1000000 AS completion_usd_per_million,
       c.prompt_usd_per_token * 1000000 + c.completion_usd_per_token * 250000 AS example_base_usd,
       c.context_length
FROM catalog_entries c
LEFT JOIN canonical_models m USING (canonical_model_id)
WHERE 'text' = ANY(c.output_modalities)
  AND 'tools' = ANY(c.supported_parameters)
  AND c.context_length >= 128000
  AND c.prompt_usd_per_token IS NOT NULL
  AND c.completion_usd_per_token IS NOT NULL
ORDER BY example_base_usd, c.catalog_id
LIMIT 20;

-- Q2: PROPOSED - For the collected text/tool catalog entries, which providers and
-- distinct routes advertise which base prices and limits? This is a selected
-- recency-biased subset, NOT evidence that uncollected entries have no providers.
SELECT c.catalog_id, p.provider_name, e.tag, e.service_tier,
       e.prompt_usd_per_token * 1000000 AS endpoint_prompt_usd_per_million,
       e.completion_usd_per_token * 1000000 AS endpoint_completion_usd_per_million,
       e.context_length, e.max_completion_tokens, e.name AS endpoint_name
FROM serving_endpoints e
JOIN catalog_entries c USING (catalog_entry_id)
JOIN providers p USING (provider_id)
WHERE 'text' = ANY(c.output_modalities)
  AND 'tools' = ANY(c.supported_parameters)
  AND 'tools' = ANY(e.supported_parameters)
ORDER BY c.catalog_id, endpoint_prompt_usd_per_million NULLS LAST,
         p.provider_name, e.tag, e.service_tier NULLS FIRST,
         e.name NULLS FIRST, e.serving_endpoint_id;

-- Q3: PROPOSED - Which canonical identities appear under multiple catalog IDs,
-- so a shortlist count should not be confused with a distinct-architecture count?
-- A canonical_slug is a source identity, not proof of a distinct architecture.
-- The student's genuine surprise is recorded above Q1; Q3 is not preselected.
-- See data_quality.md for assistant measurements, not personal reactions.
SELECT m.canonical_slug, count(*) AS catalog_id_count,
       array_agg(c.catalog_id ORDER BY c.catalog_id) AS catalog_ids
FROM canonical_models m
JOIN catalog_entries c USING (canonical_model_id)
GROUP BY m.canonical_model_id, m.canonical_slug
HAVING count(*) > 1
ORDER BY catalog_id_count DESC, m.canonical_slug;

-- Q4: PROPOSED - Which text/tool entries were added to the catalog in the 720
-- elapsed hours (30 x 24 hours) ending at the latest stored observation?
-- Both start and end are inclusive. NOT model release dates or price changes.
-- Use hours, not calendar days: timestamptz day arithmetic follows the session
-- timezone across DST, while 720 elapsed hours has a session-independent boundary.
-- The saved-observation anchor, not current_date, keeps this dated draft
-- reproducible after November 2026 without changing source IDs or timestamps.
SELECT c.catalog_id, c.catalog_created_at, c.context_length,
       c.prompt_usd_per_token * 1000000 AS prompt_usd_per_million,
       c.source_observed_at
FROM catalog_entries c
WHERE c.catalog_created_at >= (SELECT max(source_observed_at) FROM catalog_entries) - interval '720 hours'
  AND c.catalog_created_at <= (SELECT max(source_observed_at) FROM catalog_entries)
  AND 'text' = ANY(c.output_modalities)
  AND 'tools' = ANY(c.supported_parameters)
ORDER BY c.catalog_created_at DESC, c.catalog_id;

-- Q5: PROPOSED - Which output-modality groups are represented in the catalog but
-- underrepresented in the endpoint sample used for provider comparisons?
-- Coverage/fairness check is about metadata representation, NOT human fairness.
-- EXISTS counts each catalog entry once, regardless of how many endpoints it has.
-- Array combinations are source-ordered groups, not mutually exclusive abilities.
SELECT c.output_modalities, count(*) AS catalog_entries,
       count(*) FILTER (WHERE EXISTS (
           SELECT 1 FROM serving_endpoints e WHERE e.catalog_entry_id=c.catalog_entry_id
       )) AS entries_with_collected_endpoints,
       round(100.0 * count(*) FILTER (WHERE EXISTS (
           SELECT 1 FROM serving_endpoints e WHERE e.catalog_entry_id=c.catalog_entry_id
       )) / count(*), 2) AS endpoint_coverage_percent
FROM catalog_entries c
GROUP BY c.output_modalities
ORDER BY catalog_entries DESC, c.output_modalities;
