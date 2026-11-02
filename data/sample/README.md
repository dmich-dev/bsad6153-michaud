Put one small sample of your raw API data here (a few records) so others can see its shape.
Large raw downloads go in data/raw/, which Git ignores.

This committed GPT-4.1 file is a historical schema example. The live recording page now defaults
to the most recently added entry with collected provider data and labels its dates. Its current
run and model-menu checks are in [latest verification](../../docs/latest_selection_verification_2026-11-01.json).

`openrouter_sample.json` contains one model and three related serving endpoints observed on
November 1, 2026. Its record objects are copied from the complete assistant-executed ingestion;
the surrounding source URLs, date, and counts are provenance metadata.

The verified full run has 687 distinct catalog IDs, 604 canonical identities, and 15 related endpoint
records. An independent rerun produced the same ID set and counts. This committed file is deliberately
small; full original response pages and summaries stay under ignored `data/raw/`.

The earlier October 29 sample remains in Git history and in the preserved handoff. It must not be
confused with the November 1 run. [Run verification](../../docs/run_verification_2026-11-01.json)
records hashes of the current full-run responses.

See the [data dictionary](../../docs/data_dictionary.md) and [API review sheet](../../docs/api_review.md).
