Put one small sample of your raw API data here (a few records) so others can see its shape.
Large raw downloads go in data/raw/, which Git ignores.

`openrouter_sample.json` contains one model and three related serving endpoints observed on
October 29, 2026. The record objects are copied unchanged from public API preflight responses;
the surrounding source URLs, date, and counts are sample metadata.

This is a shape/relationship example, not evidence of a completed 500-record ingestion run.
The all-modalities total of 689 came from a two-record paginated response. Full preflight
responses are local under ignored `data/raw/preflight-2026-10-29/`.

See the [data dictionary](../../docs/data_dictionary.md) and [API review sheet](../../docs/api_review.md).
