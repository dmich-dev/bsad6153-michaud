# AI review log — Milestone 1 preparation

Status: preparation in progress, November 1, 2026. This log distinguishes assistant work from DJ's own review. It does not certify readiness or replace the PR template.

## Direct: instructions received

DJ asked the assistant to start the assignments, continue toward work ready for review before turn-in, compare possible data sources, and check Canvas. The live 1.2 submission identifies the project as daily model choice for coding/agent tasks and explicitly proposes OpenRouter. No source switch or final submission has been authorized.

On November 1, after clarifying that this project uses catalog metadata rather than buying model calls,
DJ explicitly confirmed retaining OpenRouter and asked the assistant to continue. This confirms the
source choice; it does not assert that DJ has completed the separate documentation check.

## Assistant preparation and verification

- Restored the school archive and verified its recorded SHA-256 and ZIP integrity. Preserved all 26 original project files in the source archive; later working-copy dictionary annotations are identified as assistant work.
- Preserved the personal baseline log byte-for-byte. No observations, timings, confidence ratings, or student reflections were invented.
- Compared documented APIs and live source metadata, labeling discovery counts separately from reproducible project ingestion.
- Audited the saved sample: one model and three related endpoints, with valid sample joins; duplicate endpoint names and conflicting output limits are documented with evidence.
- Prepared the API explanation, fetch/test plan, source comparison, case reading/planning worksheet, and readiness matrix. Case-brief text and replies were not generated.
- Verified the live Canvas account/course and current assignments on November 1. 1.3 and the substantive 1.4 discussion remain unsubmitted; deadline/lock boundary is November 1 at 11:59:59 p.m. CST. 1.0–1.2 are already submitted.
- At DJ's subsequent request to do the documentation check while he was busy, checked official authentication, catalog pagination, and rate-limit references. Bearer authentication is documented; anonymous catalog success is an observation, not a universal guarantee. Offset/limit, all-modalities filtering, and Retry-After/backoff behavior were checked. This is assistant verification.
- Implemented `ingest/fetch.py` using Python 3.12's standard library, avoiding extra installation requirements for retrieval. The existing requests-based proposal was changed for that reason; full website dependencies remain unchanged.
- Passed all 16 offline tests, including HTTP pagination/retry cases, missing/invalid data, duplicate counts, rejected redirects/origins, retry exhaustion, timeout handling, and credential-echo rejection.
- Performed a clean live run and an independent rerun. Each has seven catalog pages, 687 catalog IDs, 604 canonical identities, and 15 related endpoints from ten model lookups, with no run issues. Both used anonymous metadata GETs; neither made a paid inference call. Raw response hashes and summaries are in [verification evidence](run_verification_2026-11-01.json).
- Corrected the proposed endpoint identity to include provider name, preventing provider-name collisions from being silently merged. Verified uniqueness across the 15 collected related records; global/time-stable uniqueness remains unproven.
- At DJ's request to prepare everything for recording, built a local browser workspace that displays
  actual source sections and a preserved raw record, runs the real importer into a new output folder,
  and provides a timed recording outline. Verified the button with another complete assistant run
  (687 catalog IDs, 604 canonical identities, 15 related endpoints). No recording or student sign-off
  was created. Local access checks and provenance are recorded in [recording verification](recording_verification_2026-11-01.json).

Canvas authentication/setup helpers are local connection tools, not the assignment's data-ingestion implementation, student screencast, or proof of project retrieval. Credentials remain outside this project folder.

## Read: DJ's own review

DJ confirmed on November 1 that Lecture 3 was watched.

Pending. DJ asked the assistant to perform the documentation check while he was busy. His personal
pre-code check was not recorded as completed before implementation, and this log does not claim it was.
He still needs to review the sources/explanations and record his own verification or corrections.

Before DJ runs the script himself, he reads it and identifies where credentials are read, where requests
wait, and how 429 responses are handled. The recorded live runs above were performed by the assistant.

## Verify: project execution

Assistant verification is recorded in [the run report](run_verification_2026-11-01.json). Student execution
and interpretation remain pending. The exact commands are in the README. No live 429 was deliberately
provoked; error behavior was verified offline. The two live runs each made 17 successful HTTP requests,
with no retries, and produced identical model-ID sets. That does not guarantee future source stability.

## Decide: DJ's decisions

Pending. Record the choices DJ actually makes after review, including accepted/rejected/corrected assistant suggestions. Instructor approval status remains unverified outside the inspected Canvas comments. Do not claim approval, personal understanding, tests, or a recording without evidence.

## Final review

Pending: complete genuine baseline evidence/reflections, verify the proposal and dictionary, review the
local milestone changes and eventual PR, record the student screencast, resolve delivery location, and
obtain DJ's review before turn-in. The working copy already contains the inspected remote Git history
and a local milestone branch; the excluded Mac-only history has not been imported.
