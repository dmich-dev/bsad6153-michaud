# Ungrounded baseline | November 23, 2026

ChatGPT declined all five questions. Four had answers in the database; the fifth could not be answered from this catalog either.

**Tool and date for all five:** ChatGPT (signed out), November 23, 2026. The five prompts below were the only messages sent in one fresh chat, in this order. No files, repository connection, data, or extra instructions were supplied. No web search was requested, and no search indicator or citations appeared in the replies; backend browsing was not observable.

**Reference check:** The four nonempty `reference_sql` statements from [the golden question set](golden_questions.csv) ran against Supabase as `app_reader` in one TLS-verified, read-only snapshot at 2026-11-23 16:48:15.272082 UTC. An independent count from the underlying rows matched all four results. The [evidence record](evidence/ungrounded_baseline_2026-11-23.json) contains the exact SQL, result columns, values and captured reply text.

The text under each **ChatGPT answer** is the rendered reply, including its original wording, punctuation, and paragraph breaks.

## Q06 | How many stored entries have advertised tool support?

**ChatGPT answer**

I can’t determine the count from the information currently available. Which stored entries are you referring to—saved memories, plugin entries, or tool registry entries?

**Correct answer:** 433 of 773 stored entries list `tools` as a supported parameter. The most recent source observation on a stored catalog entry was 2026-11-23 05:09:43.384875 UTC. This is advertised capability, not a count of successful tool calls.

**Verdict: declined.** It asked which entries the question meant and reported no count.

## Q08 | How many entries are missing usable base-token prices?

**ChatGPT answer**

I don’t have access to the stored-entry pricing records needed to calculate that count. If you provide the entries, I can count those missing usable base-token prices.

**Correct answer:** 8 of 773 entries lacked a usable base-token price. The reference SQL counts the two fields separately: 8 missing prompt price and 8 missing completion price. A separate count of entries missing either field showed these were the same 8 entries. Missing does not mean free.

**Verdict: declined.** It requested the records rather than reporting a count.

## Q09 | How many catalog IDs and canonical identities are stored?

**ChatGPT answer**

I can’t access the underlying catalog records, so I can’t reliably determine the number of stored catalog IDs or canonical identities.

**Correct answer:** 773 catalog IDs and 667 canonical identities. More than one catalog ID can refer to the same canonical identity. At this snapshot every canonical identity was referenced by a catalog entry; neither total is a count of distinct model architectures.

**Verdict: declined.** It gave neither total.

## Q10 | When did the sync last succeed and what changed in the past seven days?

**ChatGPT answer**

I can’t currently access the sync history or change log, so I can’t verify:

Last successful sync: Timestamp and status.

Past seven days: New, updated, or deleted entries.

Catalog changes: New catalog IDs or canonical identities.

Pricing changes: Added, updated, or missing base-token prices.

If you provide the sync logs or catalog snapshot, I can calculate the exact changes for the seven days preceding November 23, 2026.

**Correct answer:** The last successful sync finished at 2026-11-23 05:12:20.960142 UTC. In the seven days ending at the database check, 2 successful runs recorded 153 inserted rows and 364 updated rows across the normalized tables. These are row changes, not numbers of new models; a successful check need not change any rows.

**Verdict: declined.** It named information it would need but reported no last success or change counts.

## Q15 | Which provider was cheapest every day last year, including models missing from the sample?

**ChatGPT answer**

I can’t reliably identify the cheapest provider for every day of 2025 without the complete historical pricing records.

To answer accurately, I would need:

Daily provider and model prices throughout 2025.

Models missing from the original sample, including their historical prices.

Usable base-token prices, normalized to the same currency and token volume.

Provider availability and pricing effective dates.

The result should identify the lowest-cost provider for each of the 365 days, including days when the cheapest model was absent from the sample.

I can also calculate how many days each provider was cheapest and identify ties and missing-data days.

**Correct answer:** Decline. The project stores a selective provider sample, not a daily history of every provider’s prices for 2025. Missing models cannot be ranked. The CSV marks this question `should_decline` and intentionally leaves `reference_sql` empty; there was no reference query to run.

**Verdict: declined.** This is the expected behavior: it identified the missing historical coverage and did not name a cheapest provider.

## Consequence

ChatGPT did not invent a count or a price winner; what it missed were the four answers the database could supply. Treating its lack of a sync answer as evidence that the catalog had not changed would have hidden 153 inserted rows and 364 updated rows. For the historical price question, declining was the useful outcome: the sample cannot justify choosing a provider on the claim that it was cheapest every day.
