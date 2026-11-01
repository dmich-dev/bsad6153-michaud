# Assignment 1.3 preparation and recording checklist

[Canvas assignment](https://newmanu.instructure.com/courses/14628/assignments/241963)
was refreshed October 29, 2026. Due Sunday, November 1, 2026 at 11:59 p.m. America/Chicago (CST).

## Prepared for review

- [x] Confirm existing project decision and API choice from README.
- [x] Check public catalog access and real pagination without credentials or inference.
- [x] Find enough available main records: all-modalities API reported 689; default list contained 456.
- [x] Save a small real model/endpoint sample.
- [x] Draft [data dictionary](data_dictionary.md), [API review sheet](api_review.md), and README proposal.
- [x] Preserve existing [baseline log](baseline_log.md) without adding observations.

## Before fetch-code implementation

- [x] DJ watches [Lecture 3](https://www.loom.com/share/8804dcb379a8408d8ae3c1300e182b78). DJ confirmed this on November 1.
- [ ] DJ checks authentication, pagination, and rate-limit explanations in the API review sheet against
  official documentation, and records corrections or verification.
- [ ] Resolve instructor approval for OpenRouter and the all-modalities collection scope.
- [ ] Review the proposed fetch implementation and proposed Models.dev backup.

## Technical work still to implement and verify

- [ ] `ingest/fetch.py`: pagination, paced requests, bounded backoff/retries, failure reporting, raw saves.
- [ ] At least 500 unique main records actually downloaded, with related endpoint records and valid joins.
- [ ] Clean-start and rerun evidence, plus tests for errors, missing fields, pagination, and 429 behavior.
- [ ] Exact run instructions in README; optional key name only in `.env.example` if used.
- [ ] Confirm endpoint identity rules and investigate conflicting output limits in the sample.
- [ ] Review the draft dictionary, source terms, and attribution before describing them as final.

## DJ's remaining evidence

- [ ] At least five genuine baseline entries. Use a timer for live decisions; do not invent timing for
  reconstructions. The assignment explicitly applies No AI to the entries themselves.
- [ ] Complete the five reflection prompts below the existing baseline log.
- [ ] Revise the proposal's workflow description using that log, and choose/confirm the backup source.
- [ ] Fill the PR template's Direct, Read, Verify, Decide sections with what actually happened.

## A 3–5 minute screencast outline

Use this as an outline, not a script to claim understanding or work that has not happened.

| Approximate time | What to show and explain in your own words |
|---|---|
| 0:00–0:35 | The daily model-choice problem; what catalog data can and cannot tell you. |
| 0:35–1:35 | Run the eventual documented command from a clean output folder. Show counts for models and related endpoints, then the saved JSON. |
| 1:35–2:40 | Show the exact pagination, delay, 429 backoff, and error-handling code. Explain the effect of `output_modalities=all`. |
| 2:40–3:35 | Open one real model and a linked endpoint. Explain the join, token-price units, and a null or conflicting field. |
| 3:35–4:30 | Show the data dictionary and completed review log; state real limitations and remaining questions. |

## Final review and submission

- [ ] Local changes reviewed by DJ; no secrets in files, screenshots, or Git history.
- [ ] `milestone-1` pull request targets `main`; completed PR template and review log included.
- [ ] Screencast recorded by DJ, uploaded, and linked.
- [ ] Resolve submission location: Canvas currently reports `submission_types=["none"]`, although the
  assignment text requests a PR URL and screencast. No online Canvas submission is currently offered.
- [ ] DJ authorizes final delivery; verify the resulting receipt/state. Nothing has been submitted by this preparation.
