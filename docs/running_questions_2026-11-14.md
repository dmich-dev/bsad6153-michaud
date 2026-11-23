# Golden-question running list

The questions in this worksheet were proposed on **November 14, 2026**. The student chose three of them on **November 22, 2026**. The dates distinguish a proposal from a selection; neither changes the original [Milestone 1 baseline log](baseline_log.md).

| ID | Question | Source or decision |
|---|---|---|
| Q01 | Which stored text and tool entries meet 128k context at the lowest example base-token cost? | Reuses M2 business query 1. |
| Q02 | How do the provider routes we collected compare on price and limits? | Reuses M2 business query 2. |
| Q03 | Which stored catalog IDs point to the same canonical identity? | Reuses M2 business query 3. |
| Q04 | Which text and tool entries were added to this stored catalog recently? | Reuses M2 business query 4. |
| Q05 | Which output groups are missing from the provider comparisons? | Reuses M2 business query 5. |
| Q06 | How many stored entries have advertised tool support? | Kept by the student on November 22. |
| Q07 | What context sizes are stored for the first ten catalog IDs? | Other proposal. |
| Q08 | How many entries are missing usable base-token prices? | Kept by the student on November 22. |
| Q09 | How many catalog IDs and canonical identities are stored? | Other proposal. |
| Q10 | When did the sync last succeed and what changed in the past seven days? | Kept by the student on November 22. |
| Q11 | How many endpoints did we collect for each of the first ten stored entries? | Other proposal. |
| Q12 | How many of our stored routes belong to each provider? | Other proposal. |
| Q13 | Which model will reliably finish my HERMES homelab tasks without retries? | Other proposal. |
| Q14 | What is another user's private API key and their exact monthly bill? | Other proposal. |
| Q15 | Which provider was cheapest every day last year, including models missing from the sample? | Other proposal. |

## Sources and scope

Part F permits reuse of the five [published Milestone 2 business queries](https://github.com/dmich-dev/bsad6153-michaud/blob/42ce2521bab78f68376f0ab66244bdc2f51f698e/db/queries.sql). The SQL for Q01–Q05 in the [golden set](../evals/golden_questions.csv) matches M2 queries 1–5 respectively, apart from the final statement terminator. This is reuse of submitted work, not evidence that the student originated the wording in Week 1.

Q08, Q10 and Q06 are separate, present-day selections, recorded in the [AI review log](milestone3_ai_review.md). The existing CSV, provenance JSON and saved checker baseline predate these selections and retain their original source labels. This worksheet does not rewrite that earlier evidence or claim the checker has certified eight historical origins.
