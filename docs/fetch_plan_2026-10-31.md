# Fetch implementation plan for review

Status: proposed October 31; implemented and assistant-verified November 1 after DJ asked the assistant
to perform the documentation check. DJ's personal check/review is not marked complete. Read the
resulting script before student execution. Current results: [verification report](run_verification_2026-11-01.json).

November 1: DJ explicitly confirmed retaining OpenRouter after clarifying that the project uses catalog
metadata. The plan makes no paid inference calls. Lecture 3 is confirmed watched; the documentation
check remains pending as DJ's own work. The assistant's later check and implementation are recorded honestly.

## Collection and outputs

Implemented in `ingest/fetch.py` with Python 3.12's standard library, so retrieval needs no additional packages.

1. Collect the broad model catalog in explicit pages. Retain each original JSON response under a new, timestamped directory inside ignored `data/raw/`.
2. Validate each model's ID, retain optional fields without inventing defaults, and deduplicate IDs. Report invalid rows and conflicting duplicates. Require at least 500 unique main records; fewer is an incomplete milestone, not a reason to repeat records. Report canonical-identity counts separately from catalog-ID counts so aliases are visible.
3. For a bounded set of up to ten text/tool-capable models, collect related serving endpoints. Include the saved comparison model if still available. Resolve returned details links only under the intended API host and route. Require nonempty related data and verify every accepted endpoint's parent joins to a collected model.
4. Save a machine-readable run summary: start/end timestamps, source requests, page/record counts, rejected records, retries, failures, relationship checks, and completeness. Redact credentials. A timestamped run directory prevents a later partial run from silently overwriting earlier evidence.
5. Keep one small linked real example under `data/sample/`. Preserve provenance and distinguish it from the complete raw run.

## Failure behavior

- Pace all attempts, including retries. Apply the bounded 429 policy in the API review sheet. If the allowed wait budget is exceeded, report that the run stopped instead of shortening the server's requested wait.
- Retry timeouts and transient server failures within a fixed attempt budget. Use explicit connection/read timeouts.
- Stop on authentication failures. Treat malformed JSON or response structure as a reported failure, not an empty successful page.
- Reject malformed required identifiers; preserve and flag missing optional values. An exhausted page failure means catalog coverage is incomplete. Endpoint failures remain visible and prevent a blanket success claim.
- Detect repeated pagination, a maximum-page boundary, missing progress, and invalid destinations. Check redirects before forwarding credentials. Do not send credentials to an unexpected host.
- Exit unsuccessfully if the minimum count, related-resource coverage, joins, or full-run checks fail. Save diagnostic evidence even for unsuccessful runs.

## Verification to run after DJ reads the code

| Check | Evidence needed |
|---|---|
| Paging | A local test server supplies multiple pages and a final boundary; accepted IDs and request sequence match |
| 429 | Local responses exercise `Retry-After`, fallback backoff, and retry exhaustion; no artificial real-service throttling |
| Other failures | Local timeout, 5xx, invalid JSON, missing required IDs, missing optional fields, and failed endpoint cases are reported accurately |
| Safety | Repeated/off-host pagination and redirects are rejected before credential forwarding |
| Honest completion | Duplicate IDs cannot inflate counts; fewer than 500, broken joins, and partial coverage do not pass |
| Clean start and rerun | Two independent real runs produce raw responses and truthful summaries, with at least 500 unique models and valid related records each |
| Documentation | README commands match actual usage; dictionary examples match saved data; unresolved source conflicts are labeled |

All 16 offline tests passed. Two separate real runs each retrieved 687 catalog IDs and 15 related
endpoints. Offline retry/error tests and live retrieval evidence are distinguished in the report.

## Human evidence and delivery

DJ supplies genuine baseline observations and reflections, verifies the proposal against them, fills the review log truthfully, and records the 3–5 minute screencast. Assistant-generated preparations must retain disclosure.

Remote main was checked on November 1 and the working copy now contains its Git history, with a local
`milestone-1` branch based on `3fc374c`. Verify history/file contents and refresh remote state before
creating the PR into `main`. A limited four-signature history scan passed, not an exhaustive secret audit.
Verify live Canvas instructions and delivery location before submission. User review and final delivery
remain separate steps.

Basis: the October 30 snapshot of [Assignment 1.3](https://newmanu.instructure.com/courses/14628/assignments/241963), the existing [milestone checklist](milestone1_checklist.md), and [the API check](api_check_2026-10-31.md). Implementation choices above are assistant proposals, not additional instructor requirements.
