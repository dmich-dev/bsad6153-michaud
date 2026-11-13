-- DRAFT / FOR REVIEW. Apply once to a NEW, trusted PostgreSQL 15+ schema.
-- No DROP, owner roles, API grants, credentials, extensions or production changes.
CREATE TABLE canonical_models (
    canonical_model_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    canonical_slug text NOT NULL UNIQUE CHECK (canonical_slug <> '' AND canonical_slug !~ '[[:space:]]'),
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (last_updated_at >= first_seen_at)
);

CREATE TABLE catalog_entries (
    catalog_entry_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    catalog_id text NOT NULL UNIQUE CHECK (catalog_id <> '' AND catalog_id !~ '[[:space:]]'),
    canonical_model_id bigint REFERENCES canonical_models(canonical_model_id),
    name text,
    catalog_created_at timestamptz,
    context_length bigint CHECK (context_length >= 0),
    max_completion_tokens bigint CHECK (max_completion_tokens >= 0),
    prompt_usd_per_token numeric CHECK (prompt_usd_per_token >= 0 AND prompt_usd_per_token < 'Infinity'::numeric),
    completion_usd_per_token numeric CHECK (completion_usd_per_token >= 0 AND completion_usd_per_token < 'Infinity'::numeric),
    input_modalities text[],
    output_modalities text[],
    supported_parameters text[],
    pricing jsonb CHECK (jsonb_typeof(pricing) = 'object'),
    raw_payload jsonb NOT NULL CHECK (jsonb_typeof(raw_payload) = 'object'),
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    source_observed_at timestamptz NOT NULL,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (last_updated_at >= first_seen_at)
);

CREATE TABLE providers (
    provider_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    provider_name text NOT NULL UNIQUE CHECK (btrim(provider_name) <> ''),
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (last_updated_at >= first_seen_at)
);

CREATE TABLE serving_endpoints (
    serving_endpoint_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    catalog_entry_id bigint NOT NULL REFERENCES catalog_entries(catalog_entry_id),
    provider_id bigint NOT NULL REFERENCES providers(provider_id),
    tag text,
    name text,
    service_tier text,
    context_length bigint CHECK (context_length >= 0),
    max_completion_tokens bigint CHECK (max_completion_tokens >= 0),
    prompt_usd_per_token numeric CHECK (prompt_usd_per_token >= 0 AND prompt_usd_per_token < 'Infinity'::numeric),
    completion_usd_per_token numeric CHECK (completion_usd_per_token >= 0 AND completion_usd_per_token < 'Infinity'::numeric),
    supported_parameters text[],
    pricing jsonb CHECK (jsonb_typeof(pricing) = 'object'),
    raw_payload jsonb NOT NULL CHECK (jsonb_typeof(raw_payload) = 'object'),
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    source_observed_at timestamptz NOT NULL,
    UNIQUE NULLS NOT DISTINCT (catalog_entry_id, provider_id, tag, name, service_tier),
    CHECK (coalesce(tag, '') <> '' OR coalesce(name, '') <> ''),
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (last_updated_at >= first_seen_at)
);
