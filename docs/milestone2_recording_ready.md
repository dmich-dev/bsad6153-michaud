# Milestone 2 recording readiness

Updated November 13, 2026. **The technical recording path is verified; this is not a completed submission or a blanket rubric pass.** The student still records and explains the system in their own words.

## Start the recording terminal

Open a **new local Mac Terminal tab** and run this single line before recording:

```console
ssh -t root@djserver 'bash /home/hermes-worker/repos/bsad6153-michaud-review-20261107/scripts/record_milestone2.sh'
```

This is the author's already-authorized server route, not a public login for repository readers. Finish any SSH login privately. The script locates the server working copy, clears stale inherited connection overrides, requires TLS, checks the real database and waits at **READY FOR RECORDING**. The connection check has a **20-second wall limit plus a 5-second kill grace**, independently tested with a stalled synthetic checker. It does not start a replay on EOF or cancellation. No local Mac clone or Python installation is needed.

Leave that terminal open. At the recording script's step 3, **press Enter once**. No commands are pasted into remote zsh. The actual loader reports its stages, uses a 30-second per-statement and 5-second lock limit, and the recording wrapper bounds the process with a 120-second timeout plus a 10-second kill grace. It prints the actual loader status. On success it keeps the result visible until you finish recording and press Enter again. A failure is a STOP, never permission to read the success paragraph.

For an independently configured checkout, use the ordinary `check_db.py` and `ingest/load.py --run-dir` commands with your own private Session-pooler `.env`. Do not point database tests at Supabase or valuable data.

## Browser screens

1. Open [the GitHub Mermaid diagram](schema.md) on `milestone-2`. All four table names and three relationship lines must be visible. If the viewer clips its lower table, use its Zoom out and Pan down controls; page scrolling alone does not reveal internally cropped fields.
2. Open the real Supabase Table Editor and all four populated tables. Keep connection/password dialogs offscreen.
3. Prepare separate Supabase SQL tabs for Counts, Q1 and Q2. Counts before replay, the actual replay, two live queries with interpretation, and matching after counts are all part of the demonstration.
4. Rehearse the guide, then explain naturally in your own words. Aim for **4–6 minutes**; the timeline is not proof of an actual video duration. Check microphone, playback, readable text and absence of secrets before any approved upload.

## Verified evidence

- Final parent full suite: **94 tests passed, zero skips**, including real disposable PostgreSQL, rollback/interrupt/lock boundaries and an actual PTY interaction. Temporary clusters were stopped and shutdown verified.
- Actual final checker: exit 0. Actual recording entrypoint, including checker and replay: exit 0 in **2.099 seconds** with automated Enter input. A second actual loader replay: exit 0 in **1.386 seconds**. These are assistant-run measurements, not student recording times or a duration guarantee.
- Original unoptimized same-input replay measured **97.714 seconds**. Batching removes per-row synchronous WAN lookups while preserving bound values, one transaction and insert-only conflict handling.
- Complete stored rows and audit values matched before/after both final runs: **616 canonical models / 705 catalog entries / 9 providers / 19 endpoints**. Sequences may advance and are not claimed unchanged.
- All five actual read-only SELECTs returned **20 / 19 / 89 / 32 / 12 rows**. Q4 now defines thirty days as **720 elapsed hours** and has real PostgreSQL DST/timezone/boundary regression tests. These remain November 7 source metadata, not current prices, release dates, coding benchmarks or usage guarantees.
- The user separately supplied a terminal transcript of a successful earlier replay with these counts and exit 0. That is not a new video or proof that the user executed the optimized revision.

See [the exact verification receipt](milestone2_overnight_verification.json) and [actual full-suite log](milestone2_overnight_tests.log). The earlier receipts remain historical rather than being relabeled as checks of this source.

## Academic and physical-device limits

The preserved Milestone 1 baseline does not contain the five wished-I-knew question texts. Current Q1–Q5 are honestly proposed from the project context, not fabricated historical questions. Authentic prior sources or instructor acceptance of a dated alternative remain unresolved. The prior design-review occurrence is student-confirmed; specific unrecovered earlier schema rejections/reasons are not invented or demanded again.

The actual own-words video and separate final turn-in approval remain pending. Canvas still reports the assignment missing; the original deadline was November 11, 2026. The API lists 200 possible points while the embedded rubric totals 100; no scaling, grade or extension is inferred.

The Mac was unreachable over the existing SSH route during the overnight audit, so its current browser login, recorder and microphone state were not remotely certified. The guide, public GitHub rendering, server terminal, actual cloud replay and queries were exercised; do not confuse those checks with an authenticated Mac/Supabase UI recording. Data API OFF was observed in the dated setup evidence; automatic table exposure OFF was observed at creation, not independently rechecked in this audit.

No Canvas submission, instructor message, merge, new role, synchronization workflow, API exposure change or destructive schema operation was performed.
