# ingest/

Code that moves data from your API into your database. You build it with your AI agent, one piece per week:

| Week | File | What it does |
|---|---|---|
| 1 | `fetch.py` | Calls your API: authentication, pagination, rate limits, retries. Saves raw JSON to `data/raw/`. |
| 2 | `load.py` | Turns the raw JSON into rows in your tables, using parameterized queries. Running it twice must not create duplicates. |
| 3 | `sync.py` | Combines fetch and load into one incremental, idempotent sync that GitHub Actions runs on a schedule and records in `sync_runs`. |

Only the sync connects as the database owner (`DATABASE_URL`). Everything else uses a limited role.

## Current milestone: metadata retrieval

`fetch.py` now retrieves OpenRouter's all-modalities catalog and related serving endpoints using
Python 3.12's standard library. It makes metadata GET requests only and does not connect to a database.

From the repository directory:

```console
python ingest/fetch.py
python -m unittest discover -s tests -v
```

An optional `OPENROUTER_API_KEY` is read locally; the verified runs used no key. Each run creates a
timestamped directory under ignored `data/raw/`. It retains original response pages, normalized
`models.json` and `endpoints.json`, and `summary.json` with counts, retries, issues, and completeness.
`--output-dir data/raw/my-new-run` selects a new or empty directory; nonempty destinations are refused.

The [README](../README.md#how-to-run-this-project) includes this desktop's PowerShell command.
See [run evidence](../docs/run_verification_2026-11-01.json) and [review packet](../docs/REVIEW_READY.md).
