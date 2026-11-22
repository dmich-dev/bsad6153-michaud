-- Actual read-only query used for the November 12 Supabase quality receipt.
-- This observes the pre-Milestone-3 snapshot, not automated synchronization.
SELECT pg_catalog.now() AS measured_at,
       pg_catalog.jsonb_build_object(
         'canonical_models', (SELECT count(*) FROM public.canonical_models),
         'catalog_entries', (SELECT count(*) FROM public.catalog_entries),
         'providers', (SELECT count(*) FROM public.providers),
         'serving_endpoints', (SELECT count(*) FROM public.serving_endpoints)
       ) AS row_counts,
       (SELECT count(*) FROM public.catalog_entries WHERE canonical_model_id IS NULL) AS null_canonical_parent,
       (SELECT count(*) FROM public.catalog_entries WHERE prompt_usd_per_token IS NULL) AS null_prompt_rates,
       (SELECT count(*) FROM public.catalog_entries WHERE completion_usd_per_token IS NULL) AS null_completion_rates,
       (SELECT count(*) FROM public.catalog_entries WHERE context_length IS NULL) AS null_context_lengths,
       (SELECT count(*) FROM public.catalog_entries WHERE prompt_usd_per_token < 0 OR completion_usd_per_token < 0) AS negative_usable_catalog_rates,
       (SELECT count(*) FROM (SELECT catalog_id FROM public.catalog_entries GROUP BY catalog_id HAVING count(*) > 1) d) AS duplicate_catalog_id_groups,
       (SELECT count(*) FROM (SELECT canonical_slug FROM public.canonical_models GROUP BY canonical_slug HAVING count(*) > 1) d) AS duplicate_canonical_slug_groups,
       (SELECT count(*) FROM public.catalog_entries c
        LEFT JOIN public.canonical_models m ON m.canonical_model_id = c.canonical_model_id
        WHERE c.canonical_model_id IS NOT NULL AND m.canonical_model_id IS NULL) AS orphan_catalog_parents,
       (SELECT count(*) FROM public.serving_endpoints e
        LEFT JOIN public.catalog_entries c ON c.catalog_entry_id = e.catalog_entry_id
        LEFT JOIN public.providers p ON p.provider_id = e.provider_id
        WHERE c.catalog_entry_id IS NULL OR p.provider_id IS NULL) AS orphan_endpoints,
       (SELECT count(DISTINCT catalog_entry_id) FROM public.serving_endpoints) AS catalog_entries_with_collected_endpoints;
