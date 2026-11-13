# Milestone 2: current review guide

DRAFT / FOR REVIEW. Updated November 13, 2026. Assignment 3.2 requires the Mermaid ER diagram in `docs/schema.md`, at least five commented business queries, the loader/schema and a 4–6-minute student screencast. The student authorized publishing this Milestone 2 draft PR; merge and Canvas turn-in remain separate.

## Before recording

1. Open [schema.md](schema.md) on the Milestone 2 GitHub branch. Use its rendered Mermaid diagram for the relationship explanation. Supabase's visualizer is useful, but does not replace the repository diagram and written row meanings.
2. Sign into Supabase privately. Open its actual Table Editor and SQL Editor. Show the four populated tables. Keep credentials and connection dialogs offscreen.
3. Prepare the count SELECT and Q1/Q2 from [queries.sql](../db/queries.sql). Run counts before replay, start the loader, explain Q1 and Q2 while it runs, then show its successful completion and run counts again.
4. Use your existing server terminal as `hermes-worker`. No new installation, schema application, table clearing or refetch is needed.

```console
cd /home/hermes-worker/repos/bsad6153-michaud-review-20261107
unset DATABASE_URL
.venv/bin/python -I scripts/check_db.py
.venv/bin/python -I ingest/load.py --run-dir data/raw/milestone2-verified-20261107
```

Only start the replay after the checker succeeds. The previous real replay took about 97 seconds; do not promise a shorter duration or substitute saved output for live execution. [The recording outline](milestone2_screencast_outline.md) gives the order.

## Verified technical evidence

The historical November 8 disposable PostgreSQL suite passed 48 tests with no skips. Runtime code, original tests and baseline match that independently reviewed source; SQL comments later gained the student's actual reaction while executable statements stayed identical. The [current publication verification](milestone2_publication_verification.json) records a fresh **48/48, zero-skip** disposable PostgreSQL run and verified shutdown; the historical receipt is not rewritten.

The actual November 12 Supabase Session-pooler checker and two loader CLIs exited 0 with TLS observed. Stored counts were **705 catalog entries, 616 canonical identities, 9 providers and 19 endpoints**. Complete stored rows and audit fingerprints matched after replay; sequences may advance. All five real SELECTs returned **20 / 19 / 89 / 32 / 12 rows**. See [cloud verification](milestone2_cloud_verification.json), [actual acceptance](milestone2_live_acceptance.json) and [cloud results](milestone2_cloud_query_results.json).

The November 7 source metadata is not a current price check, coding benchmark or proof of HERMES interoperability. Endpoint detail covers only eight catalog IDs. Unknown usable rates remain NULL, not zero. Q4 measures catalog additions relative to the saved observation, not model release dates.

## Student review and unresolved evidence

- The student confirms the design review already occurred; no repeat walkthrough is required. Specific earlier acceptance/rejection reasons were not recovered and are not invented.
- The student identified the number of previously unknown free options as the biggest surprise. Q1's comment and [review notes](milestone2_student_review_notes.md) retain the exact statement. Thirteen of its twenty returned entries had zero base-token rates; that is not a catalog-wide free-model count or a quality/access guarantee.
- The preserved baseline contains no five original wished-I-knew questions. [The running questions](milestone2_questions.md) remain honestly proposed. Authentic earlier sources or instructor acceptance of a dated alternative are still needed; approval today cannot create history.
- A new student recording, final review and separate submission approval remain pending. No Milestone 1 recording or assistant-run test substitutes for the student's demonstration.

## Test safety

Database tests require `MILESTONE2_TEST_DSN` pointing only to an expendable local database. Never point tests at Supabase or valuable data. Running discovery without that variable skips 17 database tests and is not full PostgreSQL verification.

```console
python -m unittest discover -s tests -v
```

No public API/app role or later synchronization workflow is activated by this milestone. The original deadline was November 11, 2026; a draft PR does not establish a late-credit arrangement.
