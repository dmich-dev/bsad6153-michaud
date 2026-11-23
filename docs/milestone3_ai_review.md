# Milestone 3 AI review log

**November 22, 2026.** Hermes assisted with Python and SQL, test cases, reference queries, and drafting this log. The student's decisions below come from their project review and [recorded walkthrough](https://www.loom.com/share/553667de249549b4b422f01b6086bdd7). The walkthrough explains captured results; it is not a claim that the student personally ran each command.

## What the student changed and how they checked the result

The student rejected the proposal to use only synthetic tests to demonstrate a hosted sync and read-only permissions. A local fixture could show how the code handled a deliberately broken run, but it could not show which permissions a real Supabase user had. The recording and documentation were revised to use the hosted results for those claims and to identify the fixture separately.

| Where in the walkthrough | What the student reviewed | Result and its limit |
|---|---|---|
| 0:29–1:45 | Compared the login identity and the read and write results on the same catalog table. | The hosted `app_reader` counted 773 entries. PostgreSQL denied its `DELETE` with `permission denied for table catalog_entries`. The statement matched no rows, so the demonstration could not remove data. This was a row-delete check, not an attempt to drop a table. [Role evidence](schema.md#access-roles) |
| 1:45–3:07 | Distinguished the push-triggered GitHub test from the manual hosted run and read the sync audit counts. | Live run 2 fetched 767 source records, inserted 153 database rows and updated 352. Fetched records and writes to normalized tables measure different things. The manual run is not scheduler evidence. [Run history](sync_tests.md#live-manual-sync-and-recovery) |
| 3:07–3:48 | Explained how a snapshot can be checked twice without reporting the same change twice. | A new stable ID inserts a row. A known ID with a changed fingerprint updates the row. An unchanged fingerprint leaves it alone. An interrupted live attempt committed no catalog writes; the retry was logged separately. |
| 3:48–4:08 | Interpreted provider-route coverage rather than treating a missing route as an unavailable service. | The catalog had a collected route for 0 of 61 image-only entries versus 17 of 478 text-only entries. That describes this sample, not what providers offer. [Dated quality checks](data_quality.md#live-quality-measurement) |

The student separately confirmed on November 22 that the Supabase Data API was off. The reader permission test does not measure that setting. The proposed company ownership and alert recipients are documented in the [data dictionary](data_dictionary.md#ownership); they are not evidence that anyone received an alert.

## Questions the student chose

On November 22 the student kept these three AI-proposed questions on the [project running list](running_questions_2026-11-14.md). This records the decision on the day it happened, not as a Milestone 1 entry.

| ID | Selected question |
|---|---|
| Q08 | How many entries are missing usable base-token prices? |
| Q10 | When did the sync last succeed and what changed in the past seven days? |
| Q06 | How many stored entries have advertised tool support? |

Q01–Q05 separately reuse the five published [Milestone 2 business queries](../db/queries.sql), as Part F permits. The three choices above do not change the origins recorded in the earlier reference-check receipt.

## Predict, then check

Before the **local fixture** ran, the assistant's test harness recorded expected insert and update counts. For an immediate replay it expected 0 inserts and 0 updates; the audit row showed 0 and 0. After changing one catalog context value and one endpoint price, it expected 0 inserts and 2 updates; the audit row showed 0 and 2. The [prediction table](sync_tests.md#predictions-before-actual-cli-invocations) preserves the other cases. These are assistant-authored expectations. No student-authored prediction made before the live run is documented, so the live counts are reported as observations, not predictions.

The hosted [reference checker](sync_tests.md#live-reference-baseline) returned 12 nonempty SQL answers as `app_reader`. The other three questions intentionally require a decline. A second check returned the same answers, but no scheduled sync intervened. Neither check substitutes for the required comparison after two scheduled updates.

## Earlier technical review (November 14)

The assistant reconciled the M2 and M3 implementations and exercised them against disposable PostgreSQL and synthetic HTTP data. The regression tests exposed a whitespace-only route reaching the writer and a recent-entry query whose results depended on a daylight-saving boundary. The corresponding validation and time-window logic were corrected. Additional checks covered reader grants, transaction rollback, retry limits, and keeping credentials out of diagnostics. These were assistant-run technical checks, not an independent human sign-off or production runs.
