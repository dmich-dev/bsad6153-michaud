# DRAFT / FOR REVIEW — Milestone 2 design before SQL

Prepared by Hermes on November 7, 2026, after reading the README, untouched baseline, dictionary, importer, real linked sample and all 21 existing tests. This is a design proposal, not a student approval or rejection.

## Proposed entities and order

1. **Canonical model identity:** one returned nonempty `canonical_slug`, not a claim about unique architectures. Store natural slug UNIQUE plus generated primary key and audit timestamps. Missing canonical values remain unknown on the catalog row rather than invented canonical records.
2. **Catalog entry:** one exact `model.id`, including aliases and variants, linked optionally to a canonical identity. Store typed context/output limits, catalog-added time, exact numeric base token rates, text arrays for modalities/parameters, original JSON, observed time and payload hash. Keep original pricing JSON to preserve non-token units and conditional overrides.
3. **Serving provider:** one exact returned provider name, not an inferred model-author prefix. No source universal provider ID exists in the inspected sample; exact name is a provisional natural identifier.
4. **Serving endpoint:** one provisional composite of catalog ID, provider, tag, name and service tier, with generated PK and NULLS NOT DISTINCT uniqueness so nullable tiers cannot cause rerun duplicates. FK to catalog entry and provider. Preserve independent context, output limit, pricing and original JSON.

Parents load before children in a single transaction. Source validation happens before writes. Use bound psycopg placeholders and Jsonb adapters; never interpolate source values into SQL. Replaying the same complete fetch output is insert-only `ON CONFLICT DO NOTHING`: rows and audit timestamps remain unchanged. Changed payloads for existing keys are deliberately not updated in this milestone; freshness/upsert/deletion tracking is next-milestone work.

## Trade-off to discuss with DJ

Do not collapse catalog aliases into canonical rows: distinct request IDs can have different capabilities/prices and endpoints join to catalog IDs. Keep canonical identity separate but do not duplicate uncertain canonical attributes onto it. Provider name and endpoint composite identities are observed provisional keys, not universally stable API IDs. Do not silently merge null/empty routing values. Reject conflicting duplicate input identities rather than choosing a winner.

## Validation and evidence plan

Use vertical RED→GREEN cycles: relational schema first; exact transformation/parent-first loading; idempotent replay and null-tier uniqueness; full transactional rollback; optional/invalid values and literal identifiers; safe CLI errors; real query execution and coverage measurements. Keep complete red/green command output and exit codes outside Git in the working packet evidence folder. Existing tests must stay unchanged and pass.

Use actual anonymous metadata GETs through existing `fetch.collect(Client(key=None))`, preserving raw pages, endpoint responses and summary. The current run actually returned 705 catalog IDs, 616 canonical slugs and 19 endpoints; these are not the historical November 1 counts. Load the full real run in disposable PostgreSQL, never SQLite. Docker access is denied; do not elevate. Download official Debian PostgreSQL packages and extract under scratch, run a fresh unprivileged loopback-only cluster with finite connection/memory limits, and stop it after verification.

## Honest rubric boundaries

The baseline has no actual logged wished-I-knew questions. Proposed SQL questions derive only from recorded cost/context/tool/HERMES criteria. Student confirmation now cannot establish historical baseline provenance: use authentic existing evidence or obtain instructor permission for a clearly dated alternative. No student surprise, schema rejection, acceptance, new baseline event, Supabase project, public PR, recording or submission may be invented. A screencast outline is not a recording. Local PostgreSQL is not Supabase evidence. Do not handle a real owner password.
