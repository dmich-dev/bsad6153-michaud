# Milestone 1 technical review

Prepared November 1, 2026. **The technical draft is ready for DJ's review. The assignments are not yet ready to turn in.**

**Student recording received:** [Loom screencast, about 4:35](https://www.loom.com/share/4e4644a86a7e44a189dd7626a3d36de1).
The [review note](screencast_review_2026-11-01.md) records topic coverage, two technical clarifications,
existing public link access, and the remaining playback/final-review checks.

**Latest selection correction:** the demo no longer pins GPT-4.1. It selects the most recently added
catalog entry with collected provider data, shows catalog-added and retrieval dates separately, and
offers a model menu. All 21 tests passed; a fresh browser-triggered run returned 687 catalog IDs,
604 canonical identities, and 73 related endpoints. Two actual empty provider lists were saved and
reported as unavailable. See [current verification](latest_selection_verification_2026-11-01.json).

**Recording setup is prepared:** use the [recording guide](recording_guide.md), or double-click
**Prepare Recording.cmd** beside the project folder. A single local browser window contains a fresh-run
button, readable actual code, a real raw record, the dictionary, and a four-minute outline. Its browser
button was verified with another complete assistant-run collection; see [recording verification](recording_verification_2026-11-01.json).

## What now works

The [importer](../ingest/fetch.py) retrieves OpenRouter catalog metadata and related serving endpoints.
The original two verification runs, before the example-selection correction, each produced:

| Evidence | Result |
|---|---|
| Catalog pages | 7 |
| Distinct catalog IDs | 687 |
| Distinct canonical model identities | 604 |
| Related serving endpoints | 15 |
| Model endpoint lookups completed | 10 of 10 |
| HTTP requests per run | 17, all successful |
| Run issues | None |
| Offline tests | 16 passed |
| Paid inference/model-generation calls | 0 |

The two model-ID sets match. Counts and source contents can change later. Retry behavior was tested
with a local HTTP server and injected failures; a real provider rate limit was not deliberately triggered.
Full raw responses remain outside Git under `data/raw/`. [Machine-readable verification](run_verification_2026-11-01.json)
records response hashes. The [small linked sample](../data/sample/openrouter_sample.json) is safe to review in the repository.

## Read these pieces

1. [Project proposal](../README.md#project-proposal-week-1): check that the decision and proposed agent
   match what you actually want, and that the workflow description accurately acknowledges the incomplete baseline.
2. [Data dictionary](data_dictionary.md): review field meanings, price units, aliases, missing values,
   relationships, source conflict, and the unresolved public-display question.
3. [Code](../ingest/fetch.py): `load_key` reads the optional local key; `checked_url` limits destinations;
   `get_json` spaces requests; `retry_delay` honors retry hints or uses bounded backoff; `collect` follows
   pages, deduplicates, validates joins, and reports completeness.
4. [AI review log](ai_review_log.md): assistant checks and student review are distinct. DJ asked the
   assistant to do the documentation check while busy. No statement that DJ personally performed that
   pre-code check, read the code, ran tests, or recorded a video has been filled in.

## Running it yourself

Read the code first. From the repository folder, `python ingest/fetch.py` writes a fresh timestamped run.
The [README](../README.md#how-to-run-this-project) includes the exact PowerShell command for this
desktop's installed Python if `python` is unavailable. Tests: `python -m unittest discover -s tests -v`.
An existing nonempty output directory is refused, preserving earlier evidence.

For the 3–5 minute screencast: show your own clean run, point to paging/waiting/429 handling and explain
them in your own words, then show one model and its related endpoint. Use the outline in the
[milestone checklist](milestone1_checklist.md). This packet is an outline, not a fabricated student recording.

## Before turn-in

- DJ reviews and records his own understanding/corrections, including documentation and code review.
- Confirm instructor approval for the non-menu API and broad catalog scope; no approval was found in
  the inspected Canvas comments, which does not rule out approval elsewhere.
- Complete at least five genuine baseline entries and the reflections. Only one reconstructed entry
  is currently saved. Live times must be measured; no personal data was invented or adjusted.
- Verify the proposal against that baseline and review the supplied screencast's clarifications and playback.
- Review [draft milestone PR #2](https://github.com/dmich-dev/bsad6153-michaud/pull/2) and complete
  the review log using actual student actions. The milestone branch is pushed for review; the PR remains
  a draft and nothing has been turned in on Canvas. Student statements remain unmarked. Canvas reports
  submission type `none` for 1.3, so its delivery location still needs resolving.
- For 1.4, DJ writes his own 400–500-word brief and two substantive replies. The
  [source index](case_source_index.md) and [worksheet](case_brief_plan_2026-10-31.md) are research/planning aids only.

Live Canvas boundaries: 1.3 due November 1 at 11:59:59 p.m. CST; 1.4 discussion locks at the same instant.
