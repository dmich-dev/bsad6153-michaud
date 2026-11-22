-- DRAFT / FOR REVIEW. Execute privately as owner only AFTER student approval.
-- Deliberately no password statement. Assign the password privately in Supabase.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='app_reader') THEN
        CREATE ROLE app_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='app_reader'
               AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls OR NOT rolcanlogin))
       OR EXISTS (SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member
                  WHERE r.rolname='app_reader') THEN
        RAISE EXCEPTION 'app_reader has incompatible privileges or memberships; review privately';
    END IF;
    -- Ownership authorizes DROP/ALTER independently of ordinary ACLs. Refuse
    -- rather than silently transfer objects or alter PUBLIC/unrelated roles.
    IF EXISTS (SELECT 1 FROM pg_database
               WHERE datname=current_database() AND datdba='app_reader'::regrole)
       OR EXISTS (SELECT 1 FROM pg_namespace
                  WHERE nspname='public' AND nspowner='app_reader'::regrole)
       OR EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                  WHERE n.nspname='public' AND c.relowner='app_reader'::regrole) THEN
        RAISE EXCEPTION 'app_reader owns the database, public schema or a public relation; review ownership privately';
    END IF;
END $$;
GRANT USAGE ON SCHEMA public TO app_reader;
REVOKE ALL ON public.canonical_models, public.catalog_entries, public.providers,
              public.serving_endpoints, public.sync_runs, public.sync_state FROM app_reader;
GRANT SELECT ON public.canonical_models TO app_reader;
GRANT SELECT ON public.catalog_entries TO app_reader;
GRANT SELECT ON public.providers TO app_reader;
GRANT SELECT ON public.serving_endpoints TO app_reader;
GRANT SELECT ON public.sync_runs TO app_reader;
-- Refuse inherited PUBLIC permissions instead of silently changing other roles.
DO $$
BEGIN
    IF has_schema_privilege('app_reader','public','CREATE') THEN
        RAISE EXCEPTION 'PUBLIC schema CREATE remains available; owner must review schema ACL';
    END IF;
    IF EXISTS (
        SELECT 1 FROM unnest(ARRAY['canonical_models','catalog_entries','providers',
                                  'serving_endpoints','sync_runs','sync_state']) t
        WHERE has_table_privilege('app_reader','public.'||t,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
           OR has_any_column_privilege('app_reader','public.'||t,'INSERT,UPDATE,REFERENCES')
    ) THEN
        RAISE EXCEPTION 'Inherited write privilege remains; owner must review table ACL';
    END IF;
END $$;
COMMIT;
