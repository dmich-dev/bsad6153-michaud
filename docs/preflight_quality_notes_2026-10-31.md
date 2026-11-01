# Saved-data quality checks

Assistant inspection, October 31, 2026. These checks inspect October 29 files; they are not fresh API observations or DJ's personal discoveries. See [machine-readable evidence](preflight_audit_2026-10-31.json).

## Counts and completeness

- The default catalog file actually contains 456 records with 456 distinct nonempty IDs.
- The all-modalities file contains **two** records. Its reported total is 689 and it links to another page. The file does not contain 689 downloaded records.
- The small linked sample contains one model and three endpoints. All three endpoint `model_id` values join to that sample model.
- These files do not establish a complete, repeatable, 500-main-record milestone run.

## Names are not endpoint identifiers

Two endpoint records have the identical name `Azure | openai/gpt-4.1-2025-04-14`, but their tags are `azure` and `azure/swedencentral`. Grouping by name or provider alone would collapse distinct offerings. The proposed model-ID/tag/name/service-tier composite is unique across these three samples, but has not been validated across the broader endpoint population or time.

## Output limits conflict with the provider documentation

The saved model summary and OpenAI endpoint report 32,768 maximum output tokens. Both saved Azure entries report 942,818. Microsoft's current [GPT-4.1 capability table](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure#gpt-41-series) lists a 32,768 output maximum for GPT-4.1 (2025-04-14).

This establishes a source discrepancy; it does not establish why OpenRouter returned that value or prove the effective limit of a particular routed deployment. Preserve the raw values and flag the conflict. Do not market 942,818 as verified output capacity, silently replace the raw data, or perform a paid inference test without a separate reason and authorization.

## Price calculation is reproducible but conditional

Decimal arithmetic on the sample's base rates gives $2 per million input tokens and $8 per million output tokens. These are sample API token rates, not a fresh price quote or a subscription comparison. The [OpenRouter model guide](https://openrouter.ai/docs/guides/overview/models) describes distinct charge units and conditional overrides, so the eventual comparison must retain the pricing object rather than rely solely on two scalar rates.

## Dictionary corrections supported by this check

- Label the counts and example values with the October 29 observation date.
- Make the duplicate endpoint-name risk explicit in the identifier section.
- Document conflicting limits as a quality issue requiring source validation.
- Keep missing, null, and zero distinct; avoid interpreting absent performance data as measured speed or suitability.

The existing baseline log was left unchanged. The final assignment's personal observations and interpretation still belong to DJ.
