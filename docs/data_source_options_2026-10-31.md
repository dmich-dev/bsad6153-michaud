# Data-source decision: keep the model-choice project

Checked October 31, 2026, around 11:35 p.m. Central. This is source evaluation, not a completed milestone. DJ has said the model-choice topic is acceptable, and has asked to compare data sources before choosing.

## Recommendation

Models.dev is the strongest candidate for keeping the topic focused on model comparison: the live provider-independent catalog contained **607 distinct models, 574 with text output**. The single-snapshot format needs instructor clarification because the assignment explicitly assesses pagination. OpenRouter remains the option with a documented, paginated model catalog and the most existing preparation. Neither source has documented instructor approval in the available course snapshot.

| Source | What it would power | Evidence and relationships | Main tradeoff |
|---|---|---|---|
| Models.dev | Compare model capabilities and provider offerings | Live `/models.json`: 607 unique top-level model entries. `/catalog.json`: 235 providers and 8,940 provider/model offerings. Of those offerings, 7,562 explicitly join to an existing canonical model. | Official examples serve full JSON snapshots; no pagination mechanism is documented in those examples. Instructor must accept this approach and approve the non-menu source. |
| OpenRouter | Compare models available through OpenRouter and their serving endpoints | Live one-record page reports 452 text-output models, or 687 across all output modalities. Related endpoint route supplies provider offerings. The saved project already has a dictionary/proposal/sample. | Reaching 500 main records requires the broader catalog under current counts. The eventual coding shortlist must be narrower. Public-display terms remain unresolved. |
| GitHub REST | A changed focus: track AI-tool issues/releases, or prioritize work | Repositories, issues, comments, labels, and releases form related records. Official pagination and rate-limit docs are available; GitHub is on the instructor's example menu. | This is a change to the decision/workflow and baseline, not a replacement feed for model pricing/capabilities. A chosen repository and at least 500 appropriate main records still need validation. |

**Models.dev counts are not interchangeable:** 8,940 is a count of provider/model offerings, not distinct underlying models. Only 472 canonical models advertised tool calling in this snapshot. A 500-model collection therefore cannot be described as 500 verified tool-capable coding models. Collecting the text catalog and then filtering recommendations is a plausible design; scope still needs review.

## Models.dev relationship and quality checks

The combined snapshot has `models` and `providers` objects. Provider/model entries can contain `canonical_model_id`. In this snapshot, 7,631 offerings supplied it, 69 pointed outside the canonical model set, and 1,309 omitted it. Use explicitly valid joins first; report unresolved mappings instead of joining names by guesswork. Counts and one concrete linked example are in [the evaluation record](modelsdev_source_evaluation_2026-10-31.json).

The repository has an [MIT license](https://raw.githubusercontent.com/anomalyco/models.dev/dev/LICENSE), including copyright/permission-notice retention. Treat provider metadata as community-maintained source claims requiring verification. Dataset metadata does not confer a license to a provider's underlying model or service.

## Canvas's role

The Canvas API can refresh course instructions, lock dates, and self-submission status. It is not needed as the model-comparison dataset. Making coursework planning the project would change the topic and would require its own record-count, access, and public-display evaluation.

The transferred context excludes the Mac's Canvas credential file. No Canvas credentials are configured in this session's environment, the last browser attempt required sign-in, and plugin discovery found no Canvas LMS connector. The October 30 authenticated snapshots remain the available course evidence. No new Canvas token has been created or requested.

## Sources

- [Models.dev API documentation](https://github.com/anomalyco/models.dev#api): documents separate model metadata and provider offerings, plus the combined catalog.
- Live research GETs: [model metadata](https://models.dev/models.json), [provider offerings](https://models.dev/api.json), [combined catalog](https://models.dev/catalog.json). These are discovery observations, not the later reproducible importer.
- [OpenRouter catalog reference](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties). Current counts came from anonymous GETs using `limit=1`, `offset=0`, and either `output_modalities=text` or `all`.
- [GitHub pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api) and [rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api). Public unauthenticated requests have a 60/hour primary limit; authenticated limits depend on the authentication context.
- [Canvas assignment API reference](https://developerdocs.instructure.com/services/canvas/resources/assignments) and the saved October 30 Assignment 1.3 requirements.

Next decision: select the source and resolve its course fit. Then DJ checks that source's authentication, paging behavior, and limits against its docs before fetch-code implementation. The earlier OpenRouter review sheet does not cover a switch to Models.dev.
