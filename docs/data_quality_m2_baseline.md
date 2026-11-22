# DRAFT / FOR REVIEW — Actual metadata quality and coverage

Hermes assistant measurements, November 7, 2026. These are objective data checks, **not student user-test events, personal reactions, comparative model benchmarks, or claims of human-group fairness**. The student must verify any documentation used in coursework against the saved source.

## Evidence and scope

The existing Milestone 1 importer ran anonymously with `Client(key=None)` against public OpenRouter metadata GETs. The complete run ended **2026-11-07T19:37:26.086181+00:00**, used 8 catalog pages and 10 selected endpoint lookups, and recorded no issues, no retries and no paid inference calls. The two actual empty provider responses (`openrouter/auto`, `openrouter/auto-code`) are preserved as empty, not invented offerings.

Durable evidence is outside Git at:

`/home/hermes-worker/PersonalOps/10 Projects/School/AI Implementations/Working drafts/2026-11-07/3.2 Database draft/evidence/`

- `public-source/`: original catalog/endpoint HTTP bodies plus importer aggregates and summary; public model/provider metadata only.
- `public-source-sha256.json`: exact-file SHA-256 provenance.
- `quality-measurements.json` and `actual-queries-quality.log`: executed Python/SQL measurements, including the full modality table below.
- `sql-results.json`: actual results of all five proposed SQL queries, using a read-only PostgreSQL transaction.
- `actual-postgres-load.json`: first/second actual load counts and row-content hashes.

These are this run's counts. Historical November 1 sample counts in existing documents are not relabeled as current.

## Main counts, identity and missingness

The actual PostgreSQL load contains **705 catalog entries, 616 canonical identities, 9 serving providers and 19 endpoints**. Those endpoints cover only **8 catalog IDs**. Both runs stored the same counts, complete row contents and audit values.

Identity checks measured **528** IDs differing from their canonical slug, **89** canonical groups with multiple IDs, and at most **2** IDs per group in this snapshot. The difference of catalog IDs and canonical identities is **89**, measured by the analysis script. Distinct catalog count is not a distinct-architecture count; aliases must not inflate a purported market-size or quality claim.

Missing-or-null checks over all **705** catalog rows:

| Field | Missing/null |
|---|---:|
| id, canonical_slug, name, created, context_length | 0 each |
| pricing.prompt, pricing.completion | 0 each |
| input_modalities, output_modalities, supported_parameters | 0 each |
| top_provider.max_completion_tokens | 6 |
| per_request_limits | 705 |

Populated does not mean valid or comparable. **90** context lengths are explicitly zero; **8** prompt and **8** completion rates are negative source values and become unknown typed prices, not credits. All **19** collected endpoint records lack usable `latency_last_30m`; no speed ranking is supported. **15** endpoints have null service tiers, so ordinary nullable composite uniqueness would be insufficient for replay protection.

The current selected endpoints have **0** output-limit disagreements with their joined catalog summary. This does not resolve the historical GPT-4.1/Azure disagreement in the preserved sample: that entry is outside this recent endpoint sample. Absence from the sample is not evidence that the earlier issue disappeared.

## Genuine fairness/coverage check: metadata representation

**Question tested:** Does the endpoint sample represent the catalog groups to which a provider comparison might be generalized? Denominator is catalog entries in each exact, source-ordered output-modality group; numerator is entries with at least one collected endpoint. SQL uses EXISTS so a model with many providers is counted once. These groups are metadata buckets, not people or protected classes; arrays in a different order would form a different bucket.

| Output modalities | Catalog entries | With endpoints | Coverage % |
|---|---:|---:|---:|
| text | 441 | 8 | 1.81 |
| image | 53 | 0 | 0.00 |
| embeddings | 45 | 0 | 0.00 |
| speech | 38 | 0 | 0.00 |
| decisions | 36 | 0 | 0.00 |
| video | 31 | 0 | 0.00 |
| transcription | 30 | 0 | 0.00 |
| rerank | 12 | 0 | 0.00 |
| image + text | 10 | 0 | 0.00 |
| text + audio | 4 | 0 | 0.00 |
| text + image | 3 | 0 | 0.00 |
| text + video | 2 | 0 | 0.00 |

Overall collected-endpoint coverage is **1.13%** (8 of 705). Among **398** advertised text/tool entries, **8** have collected endpoints (**2.01%**). The fetcher intentionally selects the newest text/tool entries, not a random or stratified sample: **8 of 89** catalog entries added in the last 30 days have endpoints here, compared with **0 of 616** older/unknown entries. That is a measured sampling-coverage imbalance, not a claim of unfair treatment by a model.

Endpoint-row counts by provider are OpenAI **6**, Azure **6**, and Liquid, GMICloud, Tencent, Stealth, Z.AI, Particle AI and Amazon Bedrock **1 each**. Two catalog entries (`openai/gpt-6.1-terra-pro`, `openai/gpt-6.1-terra`) have **6** and **7** rows respectively. Counting endpoint rows as independent model evidence would overweight entries with more routes.

**Consequence and proposed mitigation:** provider comparisons must be labeled as a recency-biased collected subset. Do not infer that missing rows mean unavailable or that text-only coverage describes the whole catalog. For a future milestone, collect endpoint details for the student's actual candidate set (or a justified stratified sample), distinguish unqueried, queried-empty and failed responses, and report coverage by group. This proposal is not a claim that additional data were fetched or that the student accepted it.

## Price/unit pitfalls

The source has **112 zero prompt-rate fields** and **249 zero completion-rate fields**. A zero component is not a free total request or a free personal subscription. The eight negative prompt IDs are recorded exactly in `quality-measurements.json`; raw `-1` values are preserved while typed usable rates are NULL.

Prices are exact decimal strings in USD per **token** for prompt/completion. SQL multiplies by 1,000,000 only to display per-million token rates. Q1 uses an explicitly illustrative 1M-input/250k-output workload; it is not measured student spend. Full `pricing` JSON remains necessary: actual extra-field occurrence counts include `web_search` **190**, `input_cache_read` **339**, `input_cache_write` **102**, `overrides` **84**, `image_output` **63**, `image` **45**, `image_token` **45**, `audio` **37**, `input_cache_write_1h` **34**, `internal_reasoning` **30**, `input_audio_cache` **27**, and `audio_output` **2**. Their units and conditions must not be silently collapsed into a token sum.

Endpoint and catalog prices/limits are stored independently. Tier, region, caching, multimodal units and overrides can change totals. Do not treat an advertised `tools` parameter as verified HERMES compatibility, coding quality or reliability.

## Freshness and query interpretation

All five proposed queries executed on actual PostgreSQL. Result-row counts were Q1 **20** (limited shortlist), Q2 **19** (collected routes), Q3 **89** (shared-canonical groups), Q4 **32** (text/tool additions within the observation-relative 30-day window), Q5 **12** (modality groups). The quality query counts **383** text/tool rows with >=128k context before requiring known prices or applying Q1's limit. Detailed results, not just these counts, are preserved.

Q1's first row is `cohere/north-mini-code:free` with base-token estimate 0 and context 256000 in the saved run. This does not prove no other charge or superior coding performance. Q3's 89 alias groups and Q5's coverage imbalance are assistant-observed findings the student may investigate; **at initial preparation this report had no student surprise**. Superseding November 12 input is now documented in [the student review notes](milestone2_student_review_notes.md): the student was surprised by the number of previously unknown free options in Q1. Its returned-twenty limit and zero-base-rate caveats still apply.

The schema is insert-only for this milestone. Replaying an existing identity does not refresh its changed payload or last_updated_at. Source creation timestamps cannot detect price changes, and future sync must distinguish missing-after-failure from true removal. Display the observation date, not a claim of perpetual currency.

## Boundaries

This dataset describes model/provider metadata, not people. Human demographic fairness, actual task success, time saved, access through subscriptions/university accounts, and HERMES end-to-end compatibility cannot be evaluated from these fields. No private prompts, account activity, owner credentials or employer-confidential records were added. Instructor source approval and public-display permission remain unresolved; a grade or praise of the website is not explicit OpenRouter approval.
