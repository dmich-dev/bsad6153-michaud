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
- Pushed the milestone branch and opened [draft PR #2](https://github.com/dmich-dev/bsad6153-michaud/pull/2)
  for review. The PR remains a draft. DJ's subsequently supplied recording is linked below; final student
  review remains pending. No Canvas submission, merge, or generated baseline entries were performed.

Canvas authentication/setup helpers are local connection tools, not the assignment's data-ingestion implementation, student screencast, or proof of project retrieval. Credentials remain outside this project folder.

## Read: DJ's own review

DJ then provided [a recorded walkthrough](https://www.loom.com/share/4e4644a86a7e44a189dd7626a3d36de1)
and its transcript. It covers authentication at 1:32, pagination at 1:58, pacing/retries at 2:34–3:18,
and raw-record relationships/units at 3:18–4:11. This records an actual student explanation, with
[two technical clarifications](screencast_review_2026-11-01.md) identified for final review. It does
not certify that every PR change was read or retroactively complete the pre-code documentation check.

DJ reported completing a recording dry run and noticed that the example stayed on GPT-4.1. The
assistant found fixed selection in both importer sampling and the demo, replaced it with catalog
recency ordering, and added a provider-backed model menu with separate catalog-added/retrieval dates.
All 21 regression tests passed. The fresh browser run had 687 catalog IDs and 73 related endpoints;
two returned empty provider lists are preserved as unavailable, rather than represented as failures
or invented records. See [selection verification](latest_selection_verification_2026-11-01.json).
These assistant corrections do not mark DJ's personal documentation/code review complete.

DJ confirmed on November 1 that Lecture 3 was watched.

Pending. DJ asked the assistant to perform the documentation check while he was busy. His personal
pre-code check was not recorded as completed before implementation, and this log does not claim it was.
He still needs to review the sources/explanations and record his own verification or corrections.

The student recording now demonstrates the run and identifies credential reading, request waits,
and 429 handling. The earlier assistant runs remain separately attributed. DJ's own official-documentation
verification and full PR review still need to be recorded honestly.

## Verify: project execution

Assistant verification is recorded in [the run report](run_verification_2026-11-01.json). DJ's supplied
screencast shows and narrates successful execution with 687 catalog IDs, 604 canonical identities,
73 related endpoints, and seven pages. Its retry-limit and pricing-unit wording need the linked clarifications.
The exact commands are in the README. No live 429 was deliberately
provoked; error behavior was verified offline. The two live runs each made 17 successful HTTP requests,
with no retries, and produced identical model-ID sets. That does not guarantee future source stability.

## Decide: DJ's decisions

DJ confirmed retaining OpenRouter and requested recent examples after his dry run exposed the fixed
GPT-4.1 choice. Final acceptance of the PR and the screencast clarifications remains pending. Instructor
approval status remains unverified outside the inspected Canvas comments. Do not claim approval or
completion of other personal requirements without evidence.

## Final review

The live November 1 check at 19:42 UTC confirmed that Canvas now accepts online text entry, URL,
media, or upload for 1.3, resolving the earlier `none` configuration. No submission has been made.

Pending: complete genuine baseline evidence/reflections, verify the proposal and dictionary, review the
milestone changes in draft PR #2, review the supplied screencast and clarifications, and
obtain DJ's review before turn-in. The working copy already contains the inspected remote Git history
and a local milestone branch; the excluded Mac-only history has not been imported.

## Additional preparation requested by DJ — November 1

DJ asked the assistant to handle the remaining preparation. The assistant rechecked the saved corrected
run's 17 original-response hashes, 687 distinct catalog IDs, 73 valid related joins, endpoint-key
uniqueness, and Terra Pro's base token-price conversion. Code is unchanged since the 21-test passing
commit; no new test run is claimed. See [preparation verification](submission_prep_verification_2026-11-01.json).

The restored project and a targeted Drive search supplied no additional genuine baseline entries.
The assistant provided a blank input sheet and asked DJ for four additional real observations and
five reflection answers. The canonical baseline remains byte-for-byte unchanged, and no personal
timings, confidence ratings, or reflections were generated.

The assistant found no source approval in the inspected Canvas comments, course-filtered inbox/archive/
sent conversations, or targeted connected-personal-Gmail searches. The course teacher identity was
verified through Canvas, and the email address through the University of Kansas consortium listing.
An approval-request email was saved as an unsent draft and fully read back: correct recipient, one
PR link, no attachments, no quoted history, and no sending. School email and other communications were
not covered, so absence in these searches is not a claim that approval was never given elsewhere.

A Canvas text-entry draft contains the PR and Loom links with the retry and price clarifications.
DJ's final review, personal evidence, and instructor approval remain pending. No student attestations
were completed on DJ's behalf. No Canvas submission, PR merge, or Loom edit was performed.

## Student baseline clarification — November 1

DJ explained that he mainly uses OpenAI because he finds 6.1 Sol cost-effective and it connects well
with HERMES. His exact wording was added to the baseline as a dated clarification. The original
observation and reflection text are retained. This is one existing reconstructed decision with
additional student-supplied context, not five distinct observations or a measured price comparison.
No timings, confidence ratings, additional events, or reflection answers were generated.

## Homelab source lookup requested by DJ — November 1

DJ described building bots for homelab tasks and asked the assistant to check DJ server for examples.
That additional description was transcribed verbatim into the baseline. The assistant checked saved
homelab notes and then the live server after its Tailscale sign-in check succeeded. Read-only SQLite
queries recovered five prior user task requests and their main-work model-usage records. The private
source notes remain outside this public repository. A session's current model field was not treated
as its full model history: one outage investigation used 6 Sol first and 6.1 Sol later.

These records support actual task/model use. They do not establish five separate deliberate
model-selection decisions, time spent choosing, confidence, measured savings, or successful task
completion. They were not converted into five AI-authored baseline entries or reflection answers.
The original baseline observation remains intact. No server project/service/configuration changes,
messages to others, Canvas submission, or PR merge were performed.

## Delegated reflection and package preparation — November 1

DJ asked the assistant to handle the remaining permitted preparation using his known context.
A fresh read of the live 1.3 assignment confirmed that its AIAS level 1 (No AI) sentence applies
specifically to the log entries. The assistant had previously treated the reflection answers too
restrictively. At DJ's request it now drafted all five reflection responses with AI assistance
disclosed, and updated the proposal's workflow to reflect DJ's stated cost/HERMES criteria and
the recovered usage history. Proposed trust/autonomy/value measures remain for DJ's final review.

The complete log-entry section was retained byte-for-byte. No new log entries, timing estimates,
confidence ratings, claimed model comparisons, or savings were generated. The fifth reflection
honestly states that the incomplete log has not yet proved an assumption wrong; its proposed
workflow hypothesis is not presented as a measured finding.

The PR's factual Direct/Read/Verify/Decide notes and the assistant technical review are prepared.
DJ's recorded walkthrough, older-example challenge, source decision, and delegation are real review
evidence; the assistant does not check an attestation that DJ read every change or personally
performed the pre-code documentation check. The Canvas text is prepared with its current limitations
stated. Final student approval, the No-AI entries, and instructor API approval remain unresolved.

## DJ accepted the prepared review — November 1

DJ said the review was fine and that we had gone through it together. This records acceptance of
the prepared review, not an assertion that every repository change was personally read or that a
pre-code documentation check happened retroactively. The same prepared review need not be approved
again. No-AI baseline entries and instructor API approval remain unresolved; no Canvas submission
or sending of the approval-request email was authorized by that acceptance.

The live assignment says non-menu APIs need approval in the proposal without naming a request
channel. Its linked syllabus, page 7, explicitly prefers email for direct communication and asks for
a descriptive subject. The instructor address on syllabus page 1 matches the saved email draft.
The draft remains unsent. An assignment comment naming the source does not itself establish an
instructor approval response.
