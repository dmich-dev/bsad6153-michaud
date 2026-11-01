# Assignment 1.3 preparation and recording checklist

[Canvas assignment](https://newmanu.instructure.com/courses/14628/assignments/241963)
was refreshed live November 1, 2026. Due that night at 11:59:59 p.m. America/Chicago (CST).

The technical draft and two assistant-executed runs are ready for review. See [review packet](REVIEW_READY.md).

## Prepared for review

- [x] Confirm existing project decision and API choice from README.
- [x] Check public catalog access and real pagination without credentials or inference.
- [x] Find enough available main records: the November 1 full runs retrieved 687 catalog IDs and 604 canonical identities. Earlier 689/456 counts are historical.
- [x] Save a small real model/endpoint sample.
- [x] Draft [data dictionary](data_dictionary.md), [API review sheet](api_review.md), and README proposal.
- [x] Preserve existing [baseline log](baseline_log.md) without adding observations.

## Human review and source scope

- [x] DJ watches [Lecture 3](https://www.loom.com/share/8804dcb379a8408d8ae3c1300e182b78). DJ confirmed this on November 1.
- [ ] DJ checks authentication, pagination, and rate-limit explanations in the API review sheet against
  official documentation, and records corrections or verification.
- [ ] Resolve instructor approval for OpenRouter and the all-modalities collection scope.
- [ ] Review the implemented fetch code and proposed Models.dev backup.
- [x] Assistant completed the documentation check after DJ asked it to do so while he was busy. This
  does not check off DJ's personal documentation review above.

## Technical work verified by the assistant

- [x] `ingest/fetch.py`: pagination, paced requests, bounded backoff/retries, failure reporting, raw saves.
- [x] Two initial runs each retrieved 687 distinct catalog IDs, 604 canonical identities, and 15 valid related endpoints.
- [x] Fixed the demo's old-model pin: a fresh newest-selection run returned 73 related endpoints; 21 tests passed. [Current verification](latest_selection_verification_2026-11-01.json).
- [x] Clean-start and rerun evidence; 16 offline tests passed. See [run verification](run_verification_2026-11-01.json).
- [x] Exact run instructions in README; optional key name only in `.env.example`.
- [x] Assistant checked the composite endpoint key and documented the unresolved output-limit source conflict; DJ still reviews their meaning in the dictionary.
- [ ] Review the draft dictionary, source terms, and attribution before describing them as final.

## DJ's remaining evidence

- [ ] At least five genuine baseline entries. Use a timer for live decisions; do not invent timing for
  reconstructions. The assignment explicitly applies No AI to the entries themselves.
- [x] Assistant drafted all five reflection responses from actual context with AI assistance disclosed; DJ reviews the wording and the fifth answer's honest evidence limitation.
- [x] Assistant updated the proposal workflow from DJ's actual stated criteria and recovered usage evidence; Models.dev remains the proposed backup for final review.
- [x] Assistant filled the PR's Direct, Read, Verify, Decide sections using actual instructions, dry-run feedback, and student screencast evidence; unverified personal attestations remain unchecked.
- [ ] DJ reviews and corrects those factual notes before final approval.

## A 3–5 minute screencast outline

Use this as an outline, not a script to claim understanding or work that has not happened.
The [recording workspace and guide](recording_guide.md) put the required material in one browser window.

| Approximate time | What to show and explain in your own words |
|---|---|
| 0:00–0:35 | The daily model-choice problem; what catalog data can and cannot tell you. |
| 0:35–1:35 | Use the recording workspace's fresh-run button or run the documented command. Show actual model/endpoint counts, then the saved JSON. |
| 1:35–2:40 | Show the exact pagination, delay, 429 backoff, and error-handling code. Explain the effect of `output_modalities=all`. |
| 2:40–3:35 | Open one real model and a linked endpoint. Explain the join, token-price units, and a null or conflicting field. |
| 3:35–4:30 | Show the data dictionary and completed review log; state real limitations and remaining questions. |

## Final review and submission

- [ ] Local changes reviewed by DJ; no secrets in files, screenshots, or Git history.
- [x] [Draft PR #2](https://github.com/dmich-dev/bsad6153-michaud/pull/2) targets `main` from `milestone-1` for review.
- [ ] Complete the student portions of the PR template and review log before marking the draft ready.
- [x] [Screencast recorded/provided by DJ](https://www.loom.com/share/4e4644a86a7e44a189dd7626a3d36de1), about 4:35, linked for review.
- [ ] DJ reviews the [technical clarifications and playback notes](screencast_review_2026-11-01.md) before final approval.
- [x] Submission route verified again November 1 at 19:42 UTC: Canvas now accepts online text entry,
  URL, media, or file upload. Text entry can hold both required links. The earlier `none` limitation is resolved.
- [ ] DJ authorizes final delivery; verify the resulting receipt/state. Nothing has been submitted by this preparation.
