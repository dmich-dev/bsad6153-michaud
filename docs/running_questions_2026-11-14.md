# Current proposed running list: November 14, 2026

DRAFT FOR STUDENT SELECTION. This is a **current** review worksheet, not a Milestone 1 log, not a backdated Milestone 2 event, and not evidence that the student has already chosen these questions. The untouched `docs/baseline_log.md` is preserved. The existing M2 list and five business queries are assistant proposals; a prior student reaction to free options does not authenticate eight question origins.

The student may keep, reword or reject any proposal below in their own review. Record the real date and their actual choices. A genuinely completed current running list can support future golden-set provenance as a running list, without asserting M1 origin. If a question is reworded, preserve both the proposal and the exact selected wording; map the CSV to the latter. Until real choices and provenance are recorded, all CSV sources remain `other` and the verified baseline/running-list count remains zero.

| ID | Proposed current question | Student choice: keep / revise / reject | Exact selected wording, if revised | Actual choice date / evidence |
|---|---|---|---|---|
| Q01 | Which stored text and tool entries meet 128k context at the lowest example base-token cost? | | | |
| Q02 | How do the provider routes we collected compare on price and limits? | | | |
| Q03 | Which stored catalog IDs point to the same canonical identity? | | | |
| Q04 | Which text and tool entries were added to this stored catalog recently? | | | |
| Q05 | Which output groups are missing from the provider comparisons? | | | |
| Q06 | How many stored entries have advertised tool support? | | | |
| Q07 | What context sizes are stored for the first ten catalog IDs? | | | |
| Q08 | How many entries are missing usable base-token prices? | | | |
| Q09 | How many catalog IDs and canonical identities are stored? | | | |
| Q10 | When did the sync last succeed and what changed in the past seven days? | | | |
| Q11 | How many endpoints did we collect for each of the first ten stored entries? | | | |
| Q12 | How many of our stored routes belong to each provider? | | | |
| Q13 | Which model will reliably finish my HERMES homelab tasks without retries? | | | |
| Q14 | What is another user's private API key and their exact monthly bill? | | | |
| Q15 | Which provider was cheapest every day last year, including models missing from the sample? | | | |

## Review completion, to be filled by the student

- Actual review date:
- At least eight distinct questions I genuinely want on my running list:
- My added question(s), if any:
- Why those questions matter to me:
- Rejected/changed suggestions and my reasons, only if any actually occurred:

After selection, a separate technical update must bind each qualifying CSV question to the exact student-selected wording, actual running-list file/hash/excerpt/date and verified origin. The validator's legacy field `student_historical_evidence` means there is real evidence of the stated origin, not that a present-day choice happened in Milestone 1. Do not set it from this blank proposal. Recheck all reference SQL and freeze a new golden baseline if the set changes. Hashes validate bytes; they do not authenticate an unsupported statement.

## November 22 source check: five published business queries

Part F expressly allows the five Milestone 2 business queries to count toward the eight. In [the published M2 source](https://github.com/dmich-dev/bsad6153-michaud/blob/42ce2521bab78f68376f0ab66244bdc2f51f698e/db/queries.sql), Q1–Q5 match the SQL for [golden Q01–Q05](../evals/golden_questions.csv) respectively, apart from the final statement terminator. They cover model cost, route prices and limits, catalog aliases, recently added entries, and route coverage by modality. This documents reuse of submitted work, not a claim that the student personally asked those questions in Week 1.

Three more distinct questions need a baseline or running-list source to reach eight using this allowance. The CSV and checker still report the conservative original labels; no student-selection flags or dates were changed by this audit.
