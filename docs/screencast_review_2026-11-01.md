# Assignment 1.3 screencast review

DJ provided [the Loom recording](https://www.loom.com/share/4e4644a86a7e44a189dd7626a3d36de1)
and its transcript on November 1, 2026. The player reports 274.78 seconds (about **4:35**), within
the required 3–5 minutes. Its existing General access setting reads **Public — Anyone can find and view**.
No sharing permissions, captions, title, or video content were changed by this review.

## Evidence provided

- **0:55–1:32:** fresh collection, saved original responses, successful completion, and narrated counts
  of 687 catalog IDs, 604 canonical identities, 73 related endpoints, and seven pages. A sampled video
  frame shows the matching successful-run screen.
- **1:32–3:18:** optional authentication, next-page links and all-modalities filter, request pacing,
  bounded retries, 429/Retry-After behavior, and the distinction between offline failure tests and live runs.
- **3:18–4:11:** a model record, request and canonical identities, source file/time, token-price units,
  missing values, and the model-to-provider relationship.
- **4:11–4:35:** dictionary, update/source limitations, and public-display permission still unresolved.

This evidence supports the recorded demonstration. It does not certify that every PR change was read,
that the personal pre-code documentation check occurred, or that the baseline/reflections are complete.

## Technical clarifications to accompany the video

1. **Around 2:48 — exact retry limit:** the current code configures **four retries after the initial
   request, for five total attempts maximum**. The narration's “five times, seven times” example is not
   the configured value. The fallback backoff waits are 2, 4, 8, and 16 seconds, in addition to normal pacing.
2. **Around 3:42 — pricing unit:** `pricing.prompt` is expressed in **USD per input token**. It does not
   imply a price of one dollar for each token. The saved GPT-6.1 Terra Pro example has a base prompt
   rate of `0.000001` USD/token, or **$1 per million input tokens**, before conditional overrides and
   other charges. Describe the actual selected record's value rather than treating the unit as the price.

Use the written source name **OpenRouter**, `.env`, and `Retry-After` in the PR. Some names in the
automatic transcript differ from those spellings; the transcript alone cannot establish the spoken pronunciation.

## Review limits and remaining work

The assistant checked the provided and visible Loom transcripts, player duration/resolution, existing
link access, sampled clean-run/dictionary frames, and the implementation. This was not an independent
audio-quality audit. The video is 1324×720; some code/table text is small in the embedded player, so
DJ should check legibility in full screen and microphone playback before final approval.

The link is attached for final review with these clarifications. The PR stays a draft; no Canvas
submission or merge is authorized by providing the recording. The genuine baseline/reflections,
remaining personal review, API approval confirmation, and delivery location still need resolution.
