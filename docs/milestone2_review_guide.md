# Milestone 2: current review guide

DRAFT / FOR REVIEW. Updated November 13, 2026. Assignment 3.2 requires the Mermaid ER diagram in `docs/schema.md`, at least five commented business queries, the loader/schema and a 4–6-minute student screencast. The student authorized publishing this Milestone 2 draft PR; merge and Canvas turn-in remain separate.

## Before recording

1. Open [schema.md](schema.md) on the Milestone 2 GitHub branch. Use its rendered Mermaid diagram for the relationship explanation. Supabase's visualizer is useful, but does not replace the repository diagram and written row meanings.
2. Sign into Supabase privately. Open its actual Table Editor and SQL Editor. Show the four populated tables. Keep credentials and connection dialogs offscreen.
3. Prepare the count SELECT and Q1/Q2 from [queries.sql](../db/queries.sql). Run counts before replay, start the real replay at step 3, show its result, explain Q1/Q2 and then run counts again.
4. Open a **new local Mac Terminal tab** and run the single command below. The Linux paths are on djserver, not the Mac. No new installation, schema application, table clearing or refetch is needed.

```console
ssh -t root@djserver 'bash /home/hermes-worker/repos/bsad6153-michaud-review-20261107/scripts/record_milestone2.sh'
```

Complete SSH login privately. Wait for **READY FOR RECORDING**, leave that terminal open and **press Enter once at step 3**. No multiline command is pasted into remote zsh. The actual loader now has flushed progress, batches, bounded waits and a real exit-code gate; the terminal holds its result visible. The original replay measured 97.714 seconds; the current direct replay measured 1.386 seconds, not a duration guarantee. [Current readiness and limits](milestone2_recording_ready.md) and [the recording outline](milestone2_screencast_outline.md) supersede older instructions.

## Verified technical evidence

The earlier November 8 and initial-publication 48-test receipts are retained as dated history, not checks of the optimized revision. The [current overnight verification](milestone2_overnight_verification.json) records a fresh **94/94, zero-skip** integrated run with real disposable PostgreSQL and verified shutdown, plus actual final cloud checker/recording-entrypoint/replay execution. The original baseline is unchanged; runtime hardening and Q4's explicit 720-hour window are disclosed in the AI log.

The actual November 12 Supabase Session-pooler checker and two loader CLIs exited 0 with TLS observed. Stored counts were **705 catalog entries, 616 canonical identities, 9 providers and 19 endpoints**. Complete stored rows and audit fingerprints matched after replay; sequences may advance. All five real SELECTs returned **20 / 19 / 89 / 32 / 12 rows**. See [cloud verification](milestone2_cloud_verification.json), [actual acceptance](milestone2_live_acceptance.json) and [cloud results](milestone2_cloud_query_results.json).

The November 7 source metadata is not a current price check, coding benchmark or proof of HERMES interoperability. Endpoint detail covers only eight catalog IDs. Unknown usable rates remain NULL, not zero. Q4 measures catalog additions relative to the saved observation, not model release dates.

## Student review and unresolved evidence

- The student confirms the design review already occurred; no repeat walkthrough is required. Specific earlier acceptance/rejection reasons were not recovered and are not invented.
- The student identified the number of previously unknown free options as the biggest surprise. Q1's comment and [review notes](milestone2_student_review_notes.md) retain the exact statement. Thirteen of its twenty returned entries had zero base-token rates; that is not a catalog-wide free-model count or a quality/access guarantee.
- The preserved baseline contains no five original wished-I-knew questions. [The running questions](milestone2_questions.md) remain honestly proposed. Authentic earlier sources or instructor acceptance of a dated alternative are still needed; approval today cannot create history.
- A new student recording, final review and separate submission approval remain pending. No Milestone 1 recording or assistant-run test substitutes for the student's demonstration.

## Test safety

Database tests require `MILESTONE2_TEST_DSN` pointing only to an expendable local database. Never point tests at Supabase or valuable data. Running discovery without that variable skips the database-opt-in cases and is not full PostgreSQL verification.

```console
python -m unittest discover -s tests -v
```

No public API/app role or later synchronization workflow is activated by this milestone. The original deadline was November 11, 2026; a draft PR does not establish a late-credit arrangement.
