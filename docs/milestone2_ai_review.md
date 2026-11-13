# DRAFT / FOR REVIEW: Milestone 2 AI review log

Prepared by **Hermes Agent, Nous Research**. Historical November 8 and November 10 entries are preserved below, followed by November 12 real-cloud verification and subsequent student review input. The student confirmed that the design review already occurred in an earlier conversation and supplied a genuine Q1 reaction. This does not attest that every file was read or resolve the historical-question provenance, recording and publication gates. The student-only baseline is unchanged.

## Direct: actual request

> okay everything is posted iterate over the assigment due in a few days and ill review that as well and maybe we can get that done today.

Existing boundaries remain: working drafts before turn-in, no real owner credentials, no Supabase change, remote database publication/merge or Canvas submission without approval, and no invented student evidence.

## Read: work performed versus student reading

The assistant reread the assignment, rubric, schema, loader, five queries, design notes, dictionary, baseline and tests. On November 12 the student confirmed that the design review had already happened in a previous conversation and declined repeating it. That confirmation is accepted as student-reported review, not an assertion of a personal review of every file or a new acceptance/rejection reason. Code/SQL is AIAS 4 system-building; documentation is AIAS 3 and must match actual data. Assistant-run tests are not student user-test events.

## Verify: actual execution

- Preserved source-only snapshots and hashes before and after the fix. Original tests, baseline, sample and recording evidence are unchanged.
- Fresh disposable PostgreSQL 17.11 execution passed **48 tests, exit 0, zero skips**: 17 database/SQL, 18 local-HTTP, 3 recording-selection and 10 connectivity tests.
- Loaded the actual November 7 public metadata: **705 catalog entries, 616 canonical identities, 9 providers, 19 endpoints**. A same-input replay preserved complete stored rows and audit timestamps. All 705 stored catalog payloads/hashes were checked.
- Executed Q1-Q5 read-only: **20, 19, 89, 32, 12 rows**. Fresh Q2 includes `endpoint_name`, preserving distinct routes. Full output is in `milestone2_query_results.json`; older differently shaped receipts remain historical.
- Independently reviewed schema/loader/query filtering using five healthy domain registers and adversarial cases; no logic defects were confirmed. The required connection helper's diagnostic disclosure was a confirmed pre-existing security defect, not an optional hardening suggestion.
- Fixed that helper in four observed RED/GREEN behavior cycles. Static errors replace driver text, imports no longer execute the CLI, project-root dotenv prevents upward discovery, and blank values fail before connection. Companion malformed-URI and driver-error negative controls fail against the old script and pass against the fix.
- Ran the real connectivity script and its `--app` flag plus two real loader CLI runs against the disposable cluster. Both flags deliberately used the same synthetic local role, not proof of app-role authorization.
- Python 3.13.5, psycopg 3.3.6 and python-dotenv 1.2.4 were exercised. Python 3.12 was not. The cluster stopped and its port/PID closure checks passed. No real credentials or live Supabase connection were used.
- Focused independent review of the corrected helper passed all 10 new tests and 38 additional bounded probe cases, with no confirmed security concerns or logic errors. All 58 frozen file hashes stayed unchanged. This focused review did not repeat the initial database review or the parent's full 48-test/real-CLI acceptance. Neither remote CI nor a verified commit is claimed.

## Decide: actual student input and remaining evidence

The assistant proposes separate canonical identities/catalog entries to preserve variants and endpoint FK targets, and nullable-tier-safe endpoint uniqueness. Those are assistant rationales, not student rejections.

- **Design review:** student-confirmed as already completed in a previous conversation. Do not require another walkthrough. See the exact correction below.
- **Specific earlier schema acceptances or changes and reasons:** carry forward only authentic recovered review notes. The statement that review occurred does not itself identify a specific accepted or rejected schema suggestion; none is fabricated.
- **Actual assistant error corrected by the student:** the assistant unnecessarily asked to repeat the completed design review. The preparation workflow now carries it forward. This is real process feedback, not an invented schema rejection.
- **Historical question sources:** not established in the preserved baseline; the five SQL questions remain proposals. An instructor-approved transparently dated alternative is not yet established.
- **Genuine Q1 surprise:** the student identified the number of previously unknown free model options as the biggest surprise. Their exact wording is recorded below and above Q1 in `db/queries.sql`. No numerical prior expectation or quality/access judgment is inferred.
- **Publication:** on November 13 the student authorized publishing the prepared Milestone 2 files and opening its draft PR. **Merge and turn-in:** not authorized by that publication approval; the student's recording, remaining evidence and final review still apply.

The five SQL questions remain proposals. Today's confirmation cannot make them historical baseline entries. No baseline questions, personal reactions, timings, confidence ratings or decisions were fabricated.

## Historical November 8 status: outside completed assistant work

Student reading/decisions and result interpretation; historical-question provenance or instructor permission for an alternative; actual Supabase settings, Session pooler and table-editor proof; the student's 4-6-minute recording; authorized Milestone 2 PR and final turn-in. Source/display permission for later public applications is separate from this milestone's named checklist. No new database PR, cloud change, recording or Canvas submission was performed.

## November 10 continuation: assistant-run cloud schema setup

The sections above describe the November 8 local iteration. The student subsequently authorized creating the isolated Supabase course project and asked to finish the remaining assignment while routing questions through Telegram. This is authorization for technical preparation, not an attestation of the student's reading, decisions or final publication approval.

- Found the actual SQL connector actions after earlier guessed names were unavailable. A project-metadata 403 was not a database-query denial; harmless SQL probes succeeded.
- Confirmed the intended project `kzituurwslaqzehlrxte` had zero public tables and supported PostgreSQL 17.11, then applied the four-table source schema in a bounded transaction through the authenticated Management API. No owner password, role creation, API enablement, extension, DROP or existing application database was used.
- Read back all four tables, each primary key, all three foreign keys, unique/check constraints and both timestamp audit columns per table. `docs/milestone2_cloud_verification.json` records the exact observed structure and open gates. All four tables remain empty; no real cloud load or pooler/loader CLI execution is claimed.
- Prepared a project-local environment and the complete saved input, verifying all 21 source-file hashes. The actual loader validator accepted 705 catalog rows and 19 endpoints, with 616 canonical identities and 9 providers. Input is dated November 7, not a new price check.
- Fresh non-database discovery passed 31 tests with 17 database tests intentionally skipped, exit 0. The full November 8 48-pass/no-skip PostgreSQL execution remains separate historical evidence. Executable SQL/Python and the student-only baseline are unchanged.
- Prepared a PR body and student recording checklist. Necessary questions were sent through the requested Telegram channel with replies deferred until parked. Student decisions, historical-question provenance, genuine reaction, publication approval and own recording remain pending.

At the end of that November 10 iteration, the private Session pooler configuration and actual checker/loader/replay still had to be performed. No Milestone 2 code publication, merge or Canvas submission occurred in that iteration.

## November 12 continuation: actual Supabase loader and query verification

The student privately saved the Session pooler connection in the server working copy. The assistant checked file ownership, mode 0600 and Git-ignore status without displaying its contents. The configured target matched the authorized course project; TLS was observed on the actual connection. No password or complete connection string entered the evidence.

- The real `scripts/check_db.py` CLI exited 0, reporting `postgres` and PostgreSQL 17.11 through the Session pooler. This was not the Management API standing in for the required CLI.
- The real `ingest/load.py` CLI ran twice on the identical saved November 7 directory. Both exited 0 with 705 catalog entries, 616 canonical identities, 9 providers and 19 endpoints. The first took 96.750 seconds and the replay 97.027 seconds. Printed counts are total stored rows, not newly inserted rows.
- Full-row fingerprints, including every stored audit value, matched after the first and second runs. This establishes unchanged stored rows on same-input replay, not unchanged sequence counters or update-in-place synchronization.
- A query-splitting mistake in the assistant's verification harness removed SQL comment prefixes and caused its first query stage to fail. No canonical SQL or loader defect was found. A header-preservation regression was observed failing, then passing after the harness-only fix. The assistant resumed only read-only SELECTs; neither loader was repeated and the original failed-stage receipt remains preserved.
- All five canonical queries then ran successfully inside a read-only transaction on the real Supabase connection: Q1 20 rows, Q2 19, Q3 89, Q4 32 and Q5 12, totaling 172 rows. Complete results are in `milestone2_cloud_query_results.json`; `milestone2_live_acceptance.json` preserves execution and replay evidence.
- The dedicated Management API read-only action independently confirmed the populated counts. A subsequent real-cloud quality readback found zero duplicate catalog-ID groups, zero duplicate canonical-slug groups, zero orphan catalog parents and zero orphan endpoints. Eight catalog rows had NULL prompt rates and eight had NULL completion rates; unknown usable prices were not replaced by zero. Endpoint coverage remained eight catalog entries, not the whole catalog.
- All seven historical executable/schema/test/baseline hashes and all 21 saved-input hashes matched. This is a comparison to the historical 48-test run, not a fresh full-suite run. No destructive integration tests were directed at Supabase, no schema was reapplied, and no API setting was enabled.

`milestone2_cloud_verification.json` separates the historical schema deployment from the current cloud result. The saved Data API OFF observation remains dated November 10; no new visual settings or Table Editor inspection is claimed. No `app_reader` cloud role is claimed here; that is the next milestone.

Student question provenance, actual design acceptance or changes, genuine interpretation, own 4-6-minute recording and final review/publication approval remain open. Nothing was published, merged or submitted during this continuation.

## November 12 student review and pre-recording preparation

After viewing the actual cloud query results, the student was asked which result, if any, differed from what they expected. Their exact response, retained in [the contemporaneous student review notes](milestone2_student_review_notes.md), was:

> Honeslty the amount of free models i didn't even know existed to be honest is probably the biggest one.

The student's stated reason was that they had not realized so many of these free options existed. The actual Q1 result contains 13 zero-base-token-rate entries among its 20 returned entries, not a catalog-wide count of free models. Advertised rates do not establish unrestricted availability or performance. The illustrative workload and context threshold remain assistant examples, not measured student consumption or a personal decision supplied by this reaction.

The student then corrected the proposed repeat design review:

> we already did it in the previous conversation in terms of review of the design I don't really need to see it is there anything else?

That is student-confirmed prior review. The assistant is not requiring the review again or inventing an earlier schema change, rejection or rationale. Bounded historical-source recovery is documented separately; absence in a bounded search is not proof that the earlier conversation did not happen.

At the student's subsequent request, the assistant added the authentic reaction to the Q1 SQL comment and updated these review notes. Only SQL comments changed; executable SELECT statements, the schema, loader and connectivity helper remain unchanged. Verification of this comment-only change is separate from the earlier real PostgreSQL and Supabase acceptance. No fresh database integration run or additional loader execution is implied.

The recording preparation now uses Q1 and Q2 as suggested demonstrations so it can include the student's genuine reaction; this is an assistant-selected outline for review, not a claim that these were historical student questions. The earlier Q2/Q5 kit remains preserved as a dated version. The student still makes and explains their own recording. Historical-question provenance and exact earlier schema-decision reasons must not be invented. No database write, publication, merge, message to the instructor or Canvas submission was authorized or performed by that November 12 preparation step.

## November 13 publication authorization

The assistant re-fetched the exact live Canvas assignment, confirming **3.2 Database Design, SQL**, assignment 242145, and the requirement for a Mermaid ER diagram in `docs/schema.md`. The student then explicitly authorized publication:

> okay do it what do i need to do before recording?

This authorizes publishing the prepared Milestone 2 branch and opening a draft PR so the repository diagram can be viewed on GitHub. It does not authorize merging either milestone, submitting to Canvas, creating a student recording, inventing baseline questions or activating later synchronization work. Milestone 1 remains the base because its existing PR is still open. Only the explicitly allowlisted Milestone 2 files are included; private `.env`, raw downloads, virtual environments and unrelated later coursework are excluded. The prior design-review occurrence is student-confirmed and is not repeated.

Before publication, a fresh full disposable PostgreSQL run passed **48 tests, zero skips, exit 0** and verified cluster shutdown. See [the publication verification](milestone2_publication_verification.json) and [its actual test log](milestone2_publication_tests.log). Schema, loader, connection helper, tests and original baseline still match the independently reviewed source; only SQL comments changed. No live Supabase load was repeated for publication.
