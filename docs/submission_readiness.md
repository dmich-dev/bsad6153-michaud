# Submission readiness — current work

Updated November 1, 2026. **Neither assignment is ready to turn in.** A fresh authenticated Canvas API check confirmed David Michaud, user 11643, and AI Implementations, course 14628. The assignment list was paginated to completion (six assignments, one page); modules, relevant announcements, calendar, and the 1.2/1.3 self-submissions were checked. 1.3 remains due November 1 at 11:59:59 p.m. CST, and 1.4 remains locked after the same instant. Both are unsubmitted.

The submitted 1.2 comment explicitly proposes OpenRouter for this model-choice project. On November 1,
DJ confirmed retaining OpenRouter after discussing alternatives and the difference between catalog data
and paid inference. Models.dev remains a proposed backup. No instructor approval appears in the
inspected submission comments; that is not proof that approval was never given elsewhere.

## Assignment 1.3: API Connection & Data Dictionary

| Requirement | Current evidence | What is still required |
|---|---|---|
| Lecture and pre-code review | DJ confirmed Lecture 3 watched; at his request the assistant checked the documentation, then implemented/tested the importer | DJ's personal pre-code check was not recorded before implementation; review honestly without backdating or claiming that sequence occurred |
| API fit and approval | Submitted 1.2 explicitly names OpenRouter; [source comparison](data_source_options_2026-10-31.md) retained for review | Confirm non-menu approval and broad catalog scope; a source switch would require updating its explanation and documentation |
| Working retrieval: 20 points | Importer and raw evidence preserved; [student screencast](https://www.loom.com/share/4e4644a86a7e44a189dd7626a3d36de1) demonstrates/narrates 687 catalog IDs, 604 canonical identities, and 73 related endpoints | DJ completes final code/PR review and confirms the technical clarifications |
| Pagination/rate limits: 15 points | Seven real catalog pages per run; sequential pacing; offline 429/Retry-After and bounded-retry checks passed | DJ reviews/explains behavior; no actual provider rate limit was deliberately triggered |
| Error handling: 10 points | 21 passing tests cover timeout, 5xx, malformed/missing data, incomplete runs, redirects, joins, recency, saved-run restoration, and empty provider lists | DJ reviews the tests and limitations; live request-failure recovery is not claimed |
| Dictionary: 25 points | 20 field entries; November 1 sample aligned to full retrieval; historical 456-record [profile](catalog_profile_2026-10-29.json) retained with its date | DJ reviews observed quirks; source approval and public-display question remain unresolved |
| Baseline/proposal: 15 points | One reconstructed baseline entry; draft proposal | DJ supplies at least five honest entries, measured live timing, labeled reconstructions, five reflections, and verifies proposal workflow |
| Screencast: 10 points | [Student recording](https://www.loom.com/share/4e4644a86a7e44a189dd7626a3d36de1) supplied; about 4:35; existing access Public; required topics present in transcript | DJ reviews [retry/price clarifications](screencast_review_2026-11-01.md) and checks full-screen legibility/audio before final approval |
| Repository practice: 5 points | Milestone branch pushed; draft PR #2 targets main; raw folder ignored; run/test commands and recording link documented | DJ reviews the exact PR and completes personal evidence; PR remains draft |
| Required review | No credential signatures found in limited copied-file/remote-history checks; assistant work recorded in [AI log](ai_review_log.md) | DJ's actual Read/Verify/Decide evidence; do not turn limited checks into an exhaustive no-secrets claim |
| Delivery | Nov 1 live assignment still offers submission type `none` although text requests PR/screencast links; no relevant new announcements found in inspected Oct 25–Nov 3 window | Resolve destination; DJ reviews exact final work before delivery |

## Assignment 1.4: case brief and two replies

| Requirement | Current evidence | What is still required |
|---|---|---|
| Evidence/sources: 20 points | Reading worksheet with primary sources and revision warning | DJ reads both selections and cites at least two credible sources actually read; justifies his evidence rating |
| Layer/scorecard: 30 points | Required questions and scorecard factors collected | DJ's own supported choice of layer and two or three scorecard factors |
| Counterfactual: 20 points | Prompt available | DJ's specific organizational decision, responsible role, contrast, and clearly labeled inference |
| Mirror: 20 points | Concrete project artifacts linked | DJ's own connection to actual baseline evidence and clearly distinguished measurement proposal |
| Replies: 10 points | Requirements collected | DJ writes two substantive evidence-based replies to classmates |
| Format/AI limits | Worksheet only; no brief/replies generated | DJ's own 400–500-word post under all five headings; references outside word count; AI research/planning disclosed as appropriate |
| Delivery boundary | Nov 1 live assignment confirms lock at Nov 1, 11:59:59 p.m. CST; live text gives no separate reply timestamp | Verify any instructor-specific reply instructions and review exact final work before posting |

## Assistant work completed so far

Restored and verified archive; preserved original project files and personal baseline; checked official source documentation; compared sources; implemented and tested retrieval; performed two complete live runs; updated the sample, dictionary, and review evidence; staged the recording workspace and verified its fresh-run button; opened the milestone PR as a draft for review. See [technical review](REVIEW_READY.md). Student personal evidence, brief/replies, review of the supplied screencast, and final submission remain outstanding.

The original unmodified files remain in the restored archive. The working copy now contains the retrieved remote Git history and a local milestone-1 branch. A four-signature scan inspected all 22 reachable remote blob objects without a match; it is not an exhaustive secret detector and does not cover the excluded Mac-only Git history. See [repository review evidence](repository_review_2026-11-01.json).
