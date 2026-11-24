"""Read only the public catalogue through the project's standalone Session pooler login."""
import os
from pathlib import Path
import re
from urllib.parse import parse_qsl, unquote, urlsplit

import psycopg


class CatalogueUnavailable(Exception):
    """Safe to catch at the UI boundary; never carry connection details."""


def _reader_options():
    # No dotenv discovery, administrator fallback, or ambient libpq overrides.
    if any(key.startswith("PG") for key in os.environ):
        raise CatalogueUnavailable()
    url = urlsplit(os.environ.get("APP_DATABASE_URL", ""))
    allowed = {"sslmode", "sslrootcert", "gssencmode", "connect_timeout"}
    if not (
        url.scheme in {"postgres", "postgresql"}
        and re.fullmatch(r"app_reader\.[a-z0-9]{20}", url.username or "")
        and re.fullmatch(r"[a-z0-9-]+\.pooler\.supabase\.com", url.hostname or "")
        and url.port in (None, 5432) and url.path == "/postgres"
        and url.password and not url.fragment
        and all(k in allowed for k, _ in parse_qsl(url.query, keep_blank_values=True, strict_parsing=True))
    ):
        raise CatalogueUnavailable()
    # Use our verified CA, not a machine-specific path or weaker mode in the URL.
    return dict(host=url.hostname, port=5432, dbname="postgres", user=url.username,
                password=unquote(url.password, errors="strict"), sslmode="verify-full",
                sslrootcert=str(Path(__file__).resolve().parents[1] / "db" / "supabase-root-2021.crt"),
                gssencmode="disable", connect_timeout=6)


def _select(sql, params=()):
    try:
        with psycopg.connect(**_reader_options()) as conn:
            if not conn.pgconn.ssl_in_use:
                raise CatalogueUnavailable()
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '8s'")
            identity = conn.execute(
                "SELECT session_user, current_user, current_setting('transaction_read_only')"
            ).fetchone()
            if identity != ("app_reader", "app_reader", "on"):
                raise CatalogueUnavailable()
            return conn.execute(sql, params).fetchall()
    except (psycopg.Error, ValueError, OSError):
        raise CatalogueUnavailable() from None


SHORTLIST = """
SELECT c.catalog_id, c.context_length,
       c.prompt_usd_per_token * 1000000, c.completion_usd_per_token * 1000000,
       c.prompt_usd_per_token * 1000000 + c.completion_usd_per_token * 250000 AS example_usd
FROM public.catalog_entries AS c
WHERE 'text' = ANY(c.output_modalities) AND 'tools' = ANY(c.supported_parameters)
  AND c.context_length >= %s
  AND c.prompt_usd_per_token IS NOT NULL AND c.completion_usd_per_token IS NOT NULL
  AND (NOT %s OR EXISTS (
      SELECT 1 FROM public.serving_endpoints AS e
      WHERE e.catalog_entry_id = c.catalog_entry_id AND 'tools' = ANY(e.supported_parameters)))
ORDER BY example_usd, c.catalog_id
LIMIT 20
"""


def shortlist(minimum, sampled):
    return _select(SHORTLIST, (minimum, sampled))


ROUTES = """
SELECT p.provider_name, e.tag, e.name, e.service_tier, e.context_length, e.max_completion_tokens,
       e.prompt_usd_per_token * 1000000, e.completion_usd_per_token * 1000000
FROM public.serving_endpoints AS e
JOIN public.providers AS p USING (provider_id)
JOIN public.catalog_entries AS c USING (catalog_entry_id)
WHERE c.catalog_id = %s AND 'text' = ANY(c.output_modalities)
  AND 'tools' = ANY(c.supported_parameters) AND 'tools' = ANY(e.supported_parameters)
ORDER BY e.prompt_usd_per_token NULLS LAST, p.provider_name, e.tag, e.service_tier NULLS FIRST,
         e.name NULLS FIRST, e.serving_endpoint_id
"""


def routes(model):
    return _select(ROUTES, (model,))


def latest_sync():
    return _select("SELECT max(finished_at) FROM public.sync_runs WHERE status = %s", ("success",))[0][0]
