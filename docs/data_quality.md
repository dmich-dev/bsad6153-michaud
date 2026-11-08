# Data quality and coverage

**Snapshot:** 2026-11-07T19:37:26.086181+00:00. These are dated observations, not a claim about today's complete catalog.

**AI assistance:** Hermes assisted with collection, validation, and preparation of this report. These are assistant-run metadata checks, not student user-test events, coding benchmarks, or measured agent outcomes.

## Source and verification scope

The existing [metadata importer](../ingest/fetch.py) collected the public [OpenRouter model catalog](https://openrouter.ai/api/v1/models) and selected provider-endpoint metadata using anonymous GET requests. The endpoint selection intentionally favors the newest text/tool-capable catalog entries; it is not a random or stratified sample.

The saved snapshot was checked with Python and loaded into disposable local PostgreSQL using a review-build loader. This report does not claim a completed Supabase deployment or that unpublished database code is already present on this branch. It publishes aggregate findings, not the raw API responses or private working files.

The original measurement receipt and raw-source provenance are retained with the project's working evidence. Measurement-receipt SHA-256: `44c51b9cd801736d8a2fcc78be694eec27f7f10421aa661b663754b7dc9668b2`. A new importer run would be a different snapshot and should not be expected to reproduce these historical counts exactly.

## Counts and identity

| Measure | Observed count |
|---|---:|
| Catalog entries | 705 |
| Canonical identities | 616 |
| Providers in the endpoint sample | 9 |
| Collected endpoint rows | 19 |
| Catalog entries with collected endpoints | 8 |

There are 89 canonical groups with multiple catalog IDs, and 528 IDs differ from their canonical slug. Counting catalog aliases as separate architectures would overstate what the metadata establishes. Even canonical identity is not a measured coding-quality result.

## Fairness/coverage check: metadata representation

**Question tested:** Does the endpoint sample represent the catalog groups to which a provider comparison might be generalized?

The denominator is catalog entries in each exact, source-ordered output-modality group. The numerator is entries with at least one collected endpoint; an entry with several provider routes is counted once. Array order is retained, so differently ordered modality arrays are different metadata buckets. These groups are not people or protected classes.

| Output modalities | Catalog entries | With collected endpoints | Coverage % |
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

Overall endpoint coverage is **1.13% (8 of 705 catalog entries)**. Among 398 advertised text/tool entries, 8 have collected endpoints (2.01%). The table shows that this endpoint sample does not support generalizing provider comparisons across the whole catalog.

This is a measured **sampling-coverage imbalance**, not evidence that a model treats human groups unfairly. The check also did not test an agent's recommendations.

## Missingness and interpretation risks

- The metadata has 90 explicitly zero context lengths. A populated field is not automatically a useful capability limit.
- There are 8 negative prompt-rate fields and 8 negative completion-rate fields. The review loader preserves the raw values but treats usable typed prices as unknown, not as credits.
- There are 112 zero prompt-rate fields and 249 zero completion-rate fields. One zero component does not establish that an entire request is free.
- Advertised tool support does not establish actual coding quality, end-to-end agent compatibility, reliability, or access through a personal subscription.
- Catalog creation dates describe additions to the source, not necessarily product release dates or the time a price last changed.

## Agent consequence and proposed safeguards

An agent that mistakes missing endpoint rows for unavailable models could produce a misleading shortlist and exclude candidates merely because they were not collected. Counting endpoint rows as independent model evidence could also favor entries with more provider routes.

Before generalizing a provider comparison:

1. Display the snapshot date and coverage limits.
2. Keep unqueried entries, queried-empty responses, and failed requests distinct. Treat unqueried candidates as unknown, not unavailable.
3. Collect endpoint details for the actual candidate set, or use a justified stratified sample and report coverage by group.
4. Restrict conclusions to the collected subset until the required coverage exists.
5. Evaluate coding or agent-task success separately. This metadata report does not supply those performance or human-fairness measurements.

These are proposed safeguards, not claims that broader sampling, a live agent evaluation, or a deployment has already occurred.
