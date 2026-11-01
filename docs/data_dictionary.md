# Data dictionary: Agent Model Selection

**Status:** Codex draft for DJ review, updated November 1. The example values below were reconfirmed in
the November 1 real linked sample. Historical October 29 profiling is explicitly labeled separately.
The importer and two live runs are now assistant-verified: 687 distinct catalog IDs, 604 canonical
identities, and 15 related endpoints per run. Instructor source approval, DJ's review, and final
public-display terms review remain pending. See [run verification](run_verification_2026-11-01.json).

## Source and meaning of a record

Source: OpenRouter. Base URL: `https://openrouter.ai/api/v1`.

- Main resource: `GET /models?output_modalities=all&limit=100&offset=0`, followed by `links.next`.
  One model record describes one catalog entry, including a specific variant when its ID differs.
- Related resource: `GET /models/{author}/{slug}/endpoints`, preferably reached through the model's
  returned `links.details`. One endpoint record describes a provider's serving offering for that model.
- References: [model listing](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties),
  [model endpoints](https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model),
  [model/pricing guide](https://openrouter.ai/docs/guides/overview/models), and [terms](https://openrouter.ai/terms).
- Authentication: the reference specifies bearer tokens; the public GETs tested returned 200 without
  a key. This is an observation about those GETs, not an authorization rule for every OpenRouter endpoint.

The [small linked sample](../data/sample/openrouter_sample.json) includes one actual model and its
three returned endpoint records. Sample values below are observations, not current availability guarantees.

## Important fields

`model.` and `endpoint.` indicate the source resource; they are not literal prefixes in the JSON.
Null/missing policy below describes the implemented handling. The saved default-filter response was also
profiled across all 456 records; its observations are evidence for that dated snapshot, not guarantees
about future responses. See the [field profile](catalog_profile_2026-10-29.json).

| Field | JSON type | Observed example | Meaning | Null/missing policy |
|---|---|---|---|---|
| `model.id` | string | `openai/gpt-4.1` | Catalog/request identifier | Required; reject a record without it |
| `model.canonical_slug` | string | `openai/gpt-4.1-2025-04-14` | Canonical version identity | Preserve null if absent; do not substitute for `id` |
| `model.name` | string | `OpenAI: GPT-4.1` | Human-readable label | Report absent label |
| `model.created` | integer | `1744651385` | Unix seconds when added to OpenRouter | Unknown if absent; not a modification timestamp |
| `model.context_length` | integer | `1047576` | Advertised model context in tokens | Unknown if absent; never assume zero |
| `model.architecture.input_modalities` | array of strings | `["image", "text", "file"]` | Accepted input types | Unknown if absent |
| `model.architecture.output_modalities` | array of strings | `["text"]` | Produced output types | Unknown if absent; needed for shortlist filtering |
| `model.pricing.prompt` | decimal string | `"0.000002"` | Base USD per input token | Preserve decimal precision; unknown if absent |
| `model.pricing.completion` | decimal string | `"0.000008"` | Base USD per output token | Preserve decimal precision; unknown if absent |
| `model.supported_parameters` | array of strings | Includes `tools` and `tool_choice` | Advertised request features | Missing is unknown, not verified support |
| `model.top_provider.max_completion_tokens` | integer or null | `32768` | Advertised primary-provider output ceiling | Unknown if absent/null; null in 6 of 456 saved records |
| `model.per_request_limits` | object or null | `null` | Catalog's optional request-limit metadata | Null is not a promise of unlimited traffic |
| `model.links.details` | string | `/api/v1/models/openai/gpt-4.1-2025-04-14/endpoints` | Link to related serving data | Check host/path before following |
| `endpoint.model_id` | string | `openai/gpt-4.1` | Parent model reference | Required; verify it joins to a fetched model |
| `endpoint.provider_name` | string | `Azure` | Serving provider, distinct from model author | Required for a usable provider comparison |
| `endpoint.tag` | string | `azure` | Returned provider/endpoint routing tag | Preserve if present; do not assume globally unique |
| `endpoint.context_length` | integer | `1047576` | Endpoint-specific context ceiling | Unknown if absent |
| `endpoint.pricing.prompt` | decimal string | `"0.000002"` | This endpoint's base USD per input token | Unknown if absent; keep separate from catalog price |
| `endpoint.max_completion_tokens` | integer | `942818` | Returned endpoint output ceiling | Preserve with source; do not silently replace model limit |
| `endpoint.latency_last_30m` | object or null | `null` | Optional recent latency statistics | Null means no usable measurement here |

Token-price example: the observed prompt rate multiplied by 1,000,000 is $2 per million input tokens;
the completion rate is $8 per million output tokens. This excludes other charge units and any conditional
pricing overrides. It is not the price of a ChatGPT/Codex subscription. Keep the full pricing object
so later calculations can account for extra units and overrides.

## Identifiers and relationships

Within a snapshot, `model.id` identifies a main record. Preserve `canonical_slug` too: an alias can point
to a versioned identity. Join `endpoint.model_id` to `model.id`, not to a provider name or ID prefix.
The model author prefix (`openai`) is not necessarily the host (`Azure`).

In the saved 456-record default response, 320 records have an `id` different from their
`canonical_slug`, and 79 canonical slugs are shared by multiple IDs. A count of distinct catalog IDs
therefore must not be described as a count of distinct underlying model architectures. Record both
catalog-ID counts and canonical-identity counts in each run report; retain aliases/variants
as source records, with their identity relationships visible.

The endpoint response supplies no obvious universal record ID. The importer uses a composite of model
ID, provider name, tag, endpoint name, and service tier. That key is unique across the 15 retrieved related
records in each verified run. It is not yet established as a permanent global key across all endpoints
and time. Model-to-endpoint is one-to-many; a provider can serve many models. Endpoint limits/prices
remain independent of the catalog summary.

The saved sample already demonstrates why endpoint name alone is unsafe: two Azure offerings have the
same name but distinct tags (`azure` and `azure/swedencentral`). The earlier proposed four-field key was
expanded to include provider name during implementation. See the
[saved-data quality audit](preflight_quality_notes_2026-10-31.md) for the historical finding.

## Update behavior

The API can add or remove models, change prices/features, and change serving availability; no fixed
refresh interval was established. Proposed sync: keep a fetch timestamp and compare full snapshots by
model ID and normalized payload hash. The `created` field alone cannot detect price changes. Distinguish
a removed record from one absent because a fetch failed, and retain last-known data with its timestamp.

## Observed quirks for DJ to review

These are Codex's observations, not claims about what surprised DJ personally.

1. The default response contained 456 model records; `output_modalities=all` reported 689. Default
   filters can make a source appear too small. Those October 29 counts are historical: the complete
   November 1 all-modalities run actually retrieved 687 catalog IDs and 604 canonical identities.
2. Prices are decimal strings. Convert with decimal arithmetic; a missing rate is different from `"0"`.
3. `id`, `canonical_slug`, and the slug in `links.details` can differ. The sample's endpoint `model_id`
   still joins to the unversioned model ID.
4. The sample's model-level output limit was 32,768, while the Azure endpoints returned 942,818.
   Microsoft's published GPT-4.1 table lists 32,768 maximum output tokens. This is an unresolved source
   conflict, not verified evidence of a larger routed limit. Preserve the raw observations and flag the
   disagreement; do not silently rewrite them. Source and limits of the check are in the
   [quality notes](preflight_quality_notes_2026-10-31.md).
5. Recent latency can be null even when an endpoint is present. Availability does not prove measured speed.
6. The broader saved profile has six null maximum-output limits, while every `per_request_limits`
   value is null. Unknown output capacity and absent request-limit metadata must remain distinct from
   zero capacity or a measured unlimited allowance.
7. The saved default response has 19 zero prompt-price strings and 21 zero completion-price strings.
   These are individual rate fields. A zero token rate is not evidence that every charge component or
   every future request is free. Preserve other units and conditional overrides.

## Data-use ethics: draft answers for review

- **Storage/display/commercial use/attribution:** OpenRouter's [terms](https://openrouter.ai/terms)
  restrict automated scraping/copying (section 7), resale/competing-service use (section 7), and use of
  protected materials without authorization (section 12). The documented API establishes an integration
  surface but does not, in the references inspected, expressly settle bulk catalog redistribution or a
  public comparison site's permission/attribution requirements. Retain provenance and resolve those
  specific uses before public launch; this dictionary makes no blanket storage/display/commercial-use grant.
- **Identifiable people:** this selected dataset describes models and providers, not individual users.
  Do not add account activity, prompts, credentials, or employer data to the public dataset.
- **Realistic harm:** stale or misinterpreted prices/capabilities could lead someone to choose an
  unsuitable model or underestimate cost. Label freshness and estimates; do not claim benchmark results.
- **Access:** proposed design gives the ingestion process write access and the public site read-only
  access to approved catalog fields. Personal workflow logs and secrets remain outside public views.

AI disclosure: Codex drafted this dictionary from official documentation and public response samples.
DJ's review, corrections, and understanding must be recorded before submission.

## Review status

Assistant source checks, field profiling, implementation, tests, and full ingestion evidence are complete
for this technical draft. DJ confirmed Lecture 3 was watched and later asked the assistant to perform
the documentation checks while he was busy. His own review is not marked complete. Instructor source
approval and the final public-display decision also remain pending.
