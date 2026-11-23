-- Apply ONCE, privately as a role/table administrator. No password here.
-- An existing name is deliberately refused, never adopted or modified.
BEGIN;
SET LOCAL search_path = pg_catalog, public, pg_temp;
CREATE ROLE catalog_sync_writer LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOINHERIT NOREPLICATION NOBYPASSRLS;

-- The new role has no direct privileges/memberships. Refuse a deployment
-- where the PUBLIC baseline already gives it lasting DDL or application writes.
-- Never repair a shared installation by revoking other users' permissions.
DO $$
DECLARE w name := 'catalog_sync_writer';
BEGIN
    IF EXISTS (SELECT FROM pg_auth_members WHERE member=w::regrole)
        OR has_database_privilege(w,current_database(),'CREATE')
        OR EXISTS (SELECT FROM pg_namespace n WHERE n.nspname !~ '^pg_(toast_)?temp_' AND has_schema_privilege(w,n.oid,'CREATE')) THEN
        RAISE EXCEPTION 'Writer inherits role membership or schema creation; review ACLs privately';
    END IF;
    IF EXISTS (SELECT FROM pg_class c JOIN pg_namespace n ON c.relnamespace=n.oid
               WHERE n.nspname NOT IN ('information_schema','pg_catalog') AND n.nspname !~ '^pg_(toast_)?temp_'
               AND has_schema_privilege(w,n.oid,'USAGE') AND c.relkind IN ('r','p','v','m','f') AND
                 (has_table_privilege(w,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') OR
                  has_any_column_privilege(w,c.oid,'INSERT,UPDATE,REFERENCES'))) THEN
        RAISE EXCEPTION 'Writer inherits unexpected table or column writes; review ACLs privately';
    END IF;
    IF NOT has_database_privilege(w,current_database(),'CONNECT') THEN
        EXECUTE format('GRANT CONNECT ON DATABASE %I TO catalog_sync_writer', current_database());
    END IF;
END $$;

GRANT USAGE ON SCHEMA public TO catalog_sync_writer;
-- Read access supports key lookups, comparison and INSERT ... RETURNING xmax.
GRANT SELECT ON public.canonical_models, public.catalog_entries, public.providers,
                public.serving_endpoints, public.sync_runs, public.sync_state TO catalog_sync_writer;
GRANT INSERT (canonical_slug) ON public.canonical_models TO catalog_sync_writer;
GRANT INSERT (provider_name) ON public.providers TO catalog_sync_writer;
GRANT INSERT (catalog_id, canonical_model_id, name, catalog_created_at, context_length,
              max_completion_tokens, prompt_usd_per_token, completion_usd_per_token,
              input_modalities, output_modalities, supported_parameters, pricing,
              raw_payload, payload_sha256, source_observed_at),
      UPDATE (canonical_model_id, name, catalog_created_at, context_length,
              max_completion_tokens, prompt_usd_per_token, completion_usd_per_token,
              input_modalities, output_modalities, supported_parameters, pricing,
              raw_payload, payload_sha256, source_observed_at, last_updated_at)
    ON public.catalog_entries TO catalog_sync_writer;
GRANT INSERT (catalog_entry_id, provider_id, tag, name, service_tier, context_length,
              max_completion_tokens, prompt_usd_per_token, completion_usd_per_token,
              supported_parameters, pricing, raw_payload, payload_sha256, source_observed_at),
      UPDATE (context_length, max_completion_tokens, prompt_usd_per_token, completion_usd_per_token,
              supported_parameters, pricing, raw_payload, payload_sha256, source_observed_at, last_updated_at)
    ON public.serving_endpoints TO catalog_sync_writer;
GRANT INSERT (status, trigger, error_message),
      UPDATE (finished_at, status, records_fetched, records_inserted, records_updated, error_message, table_counts)
    ON public.sync_runs TO catalog_sync_writer;
GRANT INSERT (source, last_success_run_id, observed_at, snapshot_sha256, mode),
      UPDATE (last_success_run_id, observed_at, snapshot_sha256)
    ON public.sync_state TO catalog_sync_writer;
-- IDENTITY defaults require no sequence grants. No DELETE, TRUNCATE, DDL,
-- ownership, role membership, grant option, default privileges or blanket grants.
COMMIT;
