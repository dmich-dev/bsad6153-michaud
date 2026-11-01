# OpenRouter API review before implementation

Prepared by Codex on October 29, 2026 for [Assignment 1.3](https://newmanu.instructure.com/courses/14628/assignments/241963).

**Historical October 29 preflight:** counts, proposed dependencies, and implementation status below
refer to that date. The November 1 implementation uses Python's standard library and has passed 16
offline tests and two complete live runs. See [current technical review](REVIEW_READY.md) and
[AI review log](ai_review_log.md). DJ's personal review is still not marked complete.

This is an assistant research sheet. DJ's documentation check and decisions are still pending.
At the time of this preflight, no reusable fetch script had been written or run.

## Three claims for DJ to check

| Topic | Explanation to check | Official documentation and observed evidence |
|---|---|---|
| Authentication | The reference shows bearer-token authentication. Public catalog and model-endpoint GET requests returned HTTP 200 without a key in this preflight. That observation does not mean private endpoints or inference are anonymous. | [Authentication](https://openrouter.ai/docs/api_reference/authentication); [models reference](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties). No credentials were used for the OpenRouter checks. |
| Pagination | Use `offset` and `limit`; follow the returned `links.next` until it is null. Keep `output_modalities=all` on every page. Omitting pagination returns the full default list. | [Models reference, query parameters](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties). The two-record all-modalities page reported 689 total records and a next-page URL with offset 2. The default request reported 456 records and no next page. These are live counts, not guarantees. |
| Rate limits | A public-catalog requests-per-minute quota was not established from the documentation reviewed. Free inference limits must not be presented as catalog limits. Make sequential requests with a delay; for 429, honor `Retry-After` when supplied and otherwise use bounded exponential backoff. | [Limits, handling 429 errors](https://openrouter.ai/docs/api_reference/limits). The preflight did not deliberately cause a 429. Backoff has not been implemented or tested. |

DJ should open the linked references, check each explanation, and record corrections or how the explanation was verified.

- [ ] Authentication explanation checked by DJ.
- [ ] Pagination explanation checked by DJ.
- [ ] Rate-limit explanation checked by DJ.

**DJ's corrections or verification notes:** Pending.

## Proposed implementation after that check

Use the existing Python 3.12 environment and `requests` dependency. Keep the implementation in
`ingest/fetch.py`, with meaningful integration tests using a local HTTP server.

1. Fetch the full all-modalities model catalog in pages of 100. Follow only pagination URLs under the
   expected OpenRouter API origin and path; stop on repeated URLs or a page limit.
2. Deduplicate by model ID. Report the unique count and fail the milestone count check below 500.
   Do not repeat records or add daily duplicates to inflate that count.
3. Fetch related serving endpoints for a bounded set of text/tool-capable models, including GPT-4.1
   for comparison with the saved sample. Join endpoint `model_id` to catalog `id`.
4. Space requests, bound retries, and handle timeouts, 429, 5xx, invalid JSON, and missing required fields.
   A partial run must report incomplete coverage rather than claim success.
5. Save original response pages and a run summary under ignored `data/raw/`. Retain one small linked
   example under `data/sample/`. Read an optional `OPENROUTER_API_KEY` from `.env` if needed; never log it.
6. Run the script from a clean output folder, rerun it, and report counts and relationship checks.

The raw catalog includes image, audio, and other models. The later coding-model shortlist should filter
for suitable text output and tool support. Ingesting the wider catalog is not evidence that all models
are appropriate for coding. Confirm this scope with the instructor when requesting API approval.

## AI review evidence

| Stage | Current evidence |
|---|---|
| Direct | DJ asked Codex to handle some of Assignment 1.3. The repository already selected OpenRouter for daily coding/agent model choice. |
| Read | DJ's review is pending. No statement that DJ has read the generated files is implied. |
| Verify | Codex observed anonymous HTTP 200 responses for the catalog and one model's endpoints, optional pagination, and a 689-record all-modalities total. Only a small preflight sample is prepared for Git; the 500-record ingestion run is not complete. |
| Decide | Pending DJ's documentation check, source approval, and review of the proposed implementation. |

## Remaining source questions

- The assignment requires instructor approval for APIs outside its menu. OpenRouter is outside that menu;
  no approval was found in the material inspected.
- Review [OpenRouter's terms](https://openrouter.ai/terms) before public display in Week 4. This research
  has not established a blanket right to redistribute the entire catalog.
- Proposed backup: [Models.dev API](https://github.com/anomalyco/models.dev#api), published at
  `https://models.dev/api.json`. This is a different schema and data source, not an automatic substitute
  for OpenRouter prices. Its [MIT-licensed repository](https://github.com/anomalyco/models.dev) and attribution
  requirements should be checked before adopting it. Backup retrieval has not been tested.
