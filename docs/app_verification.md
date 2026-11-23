# Part B: what the public app actually displayed

**November 23, 2026, 16:54:25 UTC.** The local Streamlit entrypoint ran headlessly against the course Supabase database with its standalone `app_reader` credential. The UI figures below were read from Streamlit's rendered dataframe elements, not copied from the app's query functions. A second PostgreSQL connection ran the reference SQL below against Supabase. This is assistant-run technical evidence; it is not a Render deployment, a Supabase dashboard screenshot, or DJ's personal verification.

## Reproduce the selection

Start with **Minimum advertised context = 128,000**. The default shortlist displayed 20 entries (the display limit). Checking **Only entries with a sampled route that advertises tools** gave 17 entries. Choose **`tencent/hy4-flash`**. One sampled route appeared: provider `Tencent`, tag `tencent/fp8`, name `Tencent | tencent/hy4-flash-20261116`, tier **Not listed**. The fields below belong to that selection, not all possible providers.

| Figure | UI text | Direct Supabase SQL | Result |
|---|---:|---:|---|
| Catalogue: advertised context, tokens | 1,048,576 | 1048576 | Match |
| Catalogue: example base cost, USD | 0.070125 | 0.0701250000 | Match |
| Route: advertised context, tokens | 1,048,576 | 1048576 | Match |
| Route: maximum output, tokens | 65,536 | 65536 | Match |
| Route: input USD / 1M tokens | 0.035 | 0.035000000 | Match |
| Route: output USD / 1M tokens | 0.1405 | 0.1405000000 | Match |

No numerical mismatch was observed. The comparisons used exact decimals after removing thousands separators; trailing decimal zeros do not change the value. Matching catalogue and route contexts for this model do not make those fields interchangeable. The workload is **1M input + 250k output across requests**, not a claim that one request fits or that this is a final bill.

### Independent queries

These versions select a unique model or route directly, without using the app's ranking, cache or calculation helper. The cost is regrouped as `250000 * (4 * input_rate + output_rate)`. The verification runner bound model and route identifiers as values; the equivalent literals below make the read-only checks easy to repeat. Each lookup returned exactly one row.

```sql
SELECT context_length,
       (4 * prompt_usd_per_token + completion_usd_per_token) * 250000 AS example_usd
FROM public.catalog_entries
WHERE catalog_id = 'tencent/hy4-flash';

SELECT e.context_length, e.max_completion_tokens,
       e.prompt_usd_per_token * 1000000 AS input_usd_per_million,
       e.completion_usd_per_token * 1000000 AS output_usd_per_million
FROM public.serving_endpoints AS e
WHERE e.catalog_entry_id = (SELECT catalog_entry_id FROM public.catalog_entries
                            WHERE catalog_id = 'tencent/hy4-flash')
  AND e.provider_id = (SELECT provider_id FROM public.providers WHERE provider_name = 'Tencent')
  AND e.tag = 'tencent/fp8' AND e.name = 'Tencent | tencent/hy4-flash-20261116'
  AND e.service_tier IS NULL;
```

The banner displayed **“Last successful check: 2026-11-23 05:12:20 UTC (11h 42m ago).”** A separate query returned `2026-11-23 05:12:20.960142+00`. The banner formats seconds and elapsed whole minutes. This is the last successful check, not the age of every listing.

```sql
SELECT finished_at FROM public.sync_runs
WHERE status = 'success' ORDER BY finished_at DESC LIMIT 1;
```

## Read-only proof: a role denial, not just a transaction refusal

At **16:51:43 UTC** the separate standalone reader logged in through the verified-TLS Session pooler. No administrator or `SET ROLE` was used. In the normal query connection, identity was `session_user = current_user = app_reader`, `transaction_isolation = repeatable read`, `transaction_read_only = on`. Each app data query enforces the read-only mode and checks both identities before selecting data.

For the permission check only, a separate transaction explicitly reported `transaction_read_only = off` under the same reader. `SELECT count(*) FROM public.catalog_entries` returned **773**; `has_table_privilege(current_user, 'public.catalog_entries', 'DELETE')` returned **false**. The harness checked there were no user-defined statement-level DELETE triggers and then attempted the prior milestone's zero-row probe:

```sql
DELETE FROM public.catalog_entries WHERE false;
-- SQLSTATE 42501: permission denied for table catalog_entries
```

The probe could not match a row, and the transaction was rolled back unconditionally, including on unexpected success. A fresh read-only connection counted **773** rows afterward. `42501` shows a missing table privilege, not merely a read-only transaction error. The public app contains no DELETE. This proves the credential used in the local verification; repeat the identity/denial check through the actual deployed credential after Render exists.

## Limits of this verification

A separate Chromium run at **16:57 UTC** opened the real Streamlit server on loopback in a fresh headless browser profile. It displayed the freshness banner, accepted the sampled-route filter and model selection, and showed `Tencent` and `65,536` in the route grid. The browser raised no page exceptions. The selected-route screenshot also visibly shows the catalogue cost `0.070125` and the two route prices. The server was stopped after capture; this was not a public visit.

Streamlit AppTest exercised the default view, a changed shortlist filter and an actual model selection against live data. Separate synthetic checks exercised missing configuration, rejected identities/URLs, an unavailable database and recovery, no successful sync, stale/future times, empty results, bound model identifiers and unknown versus zero prices. These cases did not change Supabase data. The comparison is dated: later successful syncs can legitimately change the shortlist or prices, and each result can be cached for up to five minutes. DJ's own source checks and deployment verification are still open.
