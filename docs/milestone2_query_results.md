# Assistant-run query results: November 8, 2026

Public metadata observed: `2026-11-07T19:37:26.086181+00:00`. Actual read-only execution on disposable PostgreSQL 17.11: `2026-11-08T17:23:03.071973+00:00`. Not current API pricing, live Supabase proof or a student reaction.

Complete results, not only these previews, are in [milestone2_query_results.json](milestone2_query_results.json). Q2 includes `endpoint_name`, which older receipts omitted.

## Q1: 20 returned rows

| catalog_id | canonical_slug | prompt_usd_per_million | completion_usd_per_million | example_base_usd | context_length |
| --- | --- | --- | --- | --- | --- |
| cohere/north-mini-code:free | cohere/north-mini-code-20260617 | 0 | 0 | 0 | 256000 |
| dots-studio/dots-3-note-preview:free | dots-studio/dots-3-note-preview-20260813 | 0 | 0 | 0 | 512000 |
| google/gemma-4-26b-a4b-it:free | google/gemma-4-26b-a4b-it-20260403 | 0 | 0 | 0 | 262144 |

First three rows only. Use the JSON file for the complete result.

## Q2: 19 returned rows

| catalog_id | provider_name | tag | service_tier | endpoint_prompt_usd_per_million | endpoint_completion_usd_per_million | context_length | max_completion_tokens | endpoint_name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| liquid/lfm-3-1.7b | Liquid | liquid/fp8 | NULL | 0.08000000 | 0.2000000 | 262144 | 8192 | Liquid \| liquid/lfm-3-1.7b-20261106 |
| openai/gpt-6.1-terra | OpenAI | openai/flex | flex | 0.5000000 | 2.5000000 | 1050000 | 128000 | OpenAI \| openai/gpt-6.1-terra-20261026 |
| openai/gpt-6.1-terra | Azure | azure | NULL | 1.000000 | 5.000000 | 1050000 | 128000 | Azure \| openai/gpt-6.1-terra-20261026 |

First three rows only. Use the JSON file for the complete result.

## Q3: 89 returned rows

| canonical_slug | catalog_id_count | catalog_ids |
| --- | --- | --- |
| anthropic/claude-4.1-opus-20250805 | 2 | ["anthropic/claude-opus-4.1", "anthropic/claude-opus-4.1:batch"] |
| anthropic/claude-4.5-haiku-20251001 | 2 | ["anthropic/claude-haiku-4.5", "anthropic/claude-haiku-4.5:batch"] |
| anthropic/claude-4.5-opus-20251124 | 2 | ["anthropic/claude-opus-4.5", "anthropic/claude-opus-4.5:batch"] |

First three rows only. Use the JSON file for the complete result.

## Q4: 32 returned rows

| catalog_id | catalog_created_at | context_length | prompt_usd_per_million | source_observed_at |
| --- | --- | --- | --- | --- |
| liquid/lfm-3-1.7b | 2026-11-06T23:57:57+00:00 | 262144 | 0.08000000 | 2026-11-07T19:37:26.086181+00:00 |
| liquid/lfm-3-1.7b:free | 2026-11-06T23:57:57+00:00 | 262144 | 0 | 2026-11-07T19:37:26.086181+00:00 |
| openrouter/auto | 2026-11-05T13:38:09+00:00 | 2000000 | NULL | 2026-11-07T19:37:26.086181+00:00 |

First three rows only. Use the JSON file for the complete result.

## Q5: 12 returned rows

| output_modalities | catalog_entries | entries_with_collected_endpoints | endpoint_coverage_percent |
| --- | --- | --- | --- |
| ["text"] | 441 | 8 | 1.81 |
| ["image"] | 53 | 0 | 0.00 |
| ["embeddings"] | 45 | 0 | 0.00 |

First three rows only. Use the JSON file for the complete result.
