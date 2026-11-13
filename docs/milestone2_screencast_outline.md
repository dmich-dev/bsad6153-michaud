# Milestone 2: recording order

AI-assisted preparation, not a recording or attestation. Aim for 4–6 minutes. The prior design review is already student-confirmed; showing the diagram here is the assignment demonstration, not another review.

1. **GitHub Mermaid diagram:** open [docs/schema.md](schema.md) on the Milestone 2 branch. Explain the four table row meanings and all three relationships. The catalog's canonical FK is optional; both endpoint FKs are required.
2. **Populated Supabase tables:** show all four tables in the actual Table Editor. Run the before-count SELECT. Verified historical totals: 616 canonical_models, 705 catalog_entries, 9 providers and 19 serving_endpoints. Read the actual current output.
3. **Start the genuine loader replay early:** use the existing server working copy and saved input after check_db.py succeeds. Previous replay took about 97 seconds. Leave it running while you explain queries. Never reapply the schema or clear tables for the recording.
4. **Run Q1 live:** explain the text/tool/context filters and illustrative total workload. The student's real surprise was the number of free options they had not known existed. The saved result had thirteen zero-base-rate entries among twenty returned, not a catalog-wide count.
5. **Run Q2 live:** explain endpoint/catalog/provider joins and route-level prices. The saved result had nineteen rows; seven routes belonged to the GPT-6.1 Terra catalog entry. These are dated metadata, not a current price or speed guarantee.
6. **Show completion and after counts:** wait for the actual loader exit. Only claim success if it succeeds, then compare the real before/after counts. Count equality alone does not establish every row/audit value; the prior cloud fingerprint receipt is separate.
7. **Close:** disclose AI assistance accurately. Check audible voice, readable screen, actual 4–6-minute duration and absence of secrets before any approved upload or turn-in.

The prepared one-file recording script is a reading aid, not evidence of a completed recording. The five queries remain proposed because original baseline-question origins have not been established. No schema rejection, earlier design reason, instructor permission, recording link or student-run result is fabricated. Publishing the draft PR is authorized separately from merge and submission.
