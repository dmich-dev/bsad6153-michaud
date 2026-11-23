-- Apply privately, AFTER the Milestone 2 catalog schema, as its administrator.
-- No table data is removed. Reapplicable only within this reviewed schema version.
BEGIN;
SET LOCAL search_path = pg_catalog, public, pg_temp;
CREATE TABLE IF NOT EXISTS public.sync_runs (
    run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    status text NOT NULL CHECK (status IN ('success','partial','failed')),
    records_fetched bigint NOT NULL DEFAULT 0 CHECK (records_fetched >= 0),
    records_inserted bigint NOT NULL DEFAULT 0 CHECK (records_inserted >= 0),
    records_updated bigint NOT NULL DEFAULT 0 CHECK (records_updated >= 0),
    error_message text,
    trigger text NOT NULL CHECK (trigger IN ('schedule','manual')),
    table_counts jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(table_counts)='object'),
    CHECK (finished_at IS NULL OR finished_at >= started_at),
    CHECK (status <> 'success' OR (finished_at IS NOT NULL AND error_message IS NULL))
);
-- This is an observation checkpoint, NOT a source modification watermark.
CREATE TABLE IF NOT EXISTS public.sync_state (
    source text PRIMARY KEY,
    last_success_run_id bigint NOT NULL REFERENCES sync_runs(run_id),
    observed_at timestamptz NOT NULL,
    snapshot_sha256 text NOT NULL CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    mode text NOT NULL CHECK (mode='full_snapshot_hash_diff')
);
CREATE INDEX IF NOT EXISTS sync_runs_finished ON public.sync_runs(finished_at DESC);
COMMIT;
