# Assignment 1.3 recording guide

The recording workspace is a local presentation aid. It shows the actual source code and real API
responses and runs the actual importer into a new folder. It does not record, upload, submit, or
automatically mark student review complete.

On this Windows desktop, double-click **Prepare Recording.cmd** in the outputs folder. The browser
opens the prepared workspace. Keep its helper window open while recording. Alternatively, from the
repository run `python scripts/recording_room.py`.

## Set up once

1. Read the authentication, pacing, retry, and pagination sections under **Code**. Follow the official
   documentation links and record your actual review/corrections in the AI log; do not backdate anything.
2. Open your recorder (Loom is recommended by the assignment). Choose the prepared browser window
   or its tab, enable your microphone, and check the input. A camera image is not listed in the assignment.
3. Start recording, then use **Clean run → Run a fresh live collection**. New run counts are displayed
   dynamically; use the actual results instead of memorizing historical counts.

## Four-minute outline

| Time | Show | Explain in your own words |
|---|---|---|
| 0:00–0:25 | Opening/project title | The daily decision and what catalog metadata can help compare |
| 0:25–1:20 | Clean run, command, and result | Fresh destination, real requests, model/endpoint counts, completeness |
| 1:20–2:45 | Actual Code sections | Optional bearer key; next-page links and all-modalities filter; one-second pacing; Retry-After or bounded backoff on 429 |
| 2:45–3:45 | Raw record and related provider | What one row means; model ID join; USD per token; one null, alias, or source conflict |
| 3:45–4:15 | Dictionary | One genuine limitation: metadata does not establish coding quality, and endpoint limits can disagree |

The baseline of two assistant runs was 687 catalog IDs, 604 canonical identities, and 15 related
endpoints, with 16 offline tests passed. These are historical assistant results. The recording room's
own latest run replaces its example view after completion. The original raw JSON object is read from
a preserved response page; the displayed provenance names that file. Related records are shown separately.

## After recording

Check the recording's duration, microphone audio, legible code, fresh-run completion, and raw-record
explanation. Save/upload using the recorder and provide the resulting link for the PR. Final turn-in
still requires your review and authorization.

Recording is not the only outstanding assignment requirement: the saved personal baseline has one
reconstructed entry, and your own review, reflections, API approval confirmation, and eventual screencast
link remain outstanding. See [submission readiness](submission_readiness.md). Assignment 1.4 is separate.
