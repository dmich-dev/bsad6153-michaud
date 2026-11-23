"""Retrieve OpenRouter catalog metadata only; no inference or paid-model calls.

Standard library only; the caller supplies a private temporary directory.
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.client import HTTPException
import json
from pathlib import Path
import re
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://openrouter.ai"


class RetrievalError(Exception):
    """A safe, credential-free diagnostic for an unsuccessful request/run."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_bytes(path, value):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    except OSError:
        raise RetrievalError("Could not save the raw response; run is incomplete") from None


class Client:
    def __init__(self, output, *, base_url=BASE_URL, delay=1.0,
                 retries=4, max_wait=60.0, timeout=30.0, sleep=time.sleep,
                 allow_local_http=False):
        origin = urlsplit(base_url)
        if origin.scheme != "https" and not (
            allow_local_http and origin.scheme == "http" and origin.hostname == "127.0.0.1"
        ):
            raise RetrievalError("HTTPS is required")
        self.base_url = base_url.rstrip("/")
        self.origin = (origin.scheme, origin.netloc)
        self.output = Path(output)
        self.delay, self.retries, self.max_wait = delay, retries, max_wait
        self.timeout, self.sleep = timeout, sleep
        self.opener = build_opener(NoRedirect())
        self.requests = []
        self.waits = []

    def checked_url(self, value, *, catalog=False):
        if not isinstance(value, str) or not value or not value.isascii() or any(ord(c) <= 32 or ord(c) == 127 for c in value):
            raise RetrievalError("Missing request URL")
        url = urljoin(self.base_url + "/", value)
        parsed = urlsplit(url)
        if ((parsed.scheme, parsed.netloc) != self.origin or parsed.username
                or parsed.password or parsed.fragment):
            raise RetrievalError("Rejected a request outside the configured API origin")
        if catalog and parsed.path == "/api/v1/models":
            query = parse_qs(parsed.query, keep_blank_values=True)
            if set(query) != {"limit", "offset", "output_modalities"}:
                raise RetrievalError("Unexpected catalog query parameters")
            if any(len(values) != 1 for values in query.values()):
                raise RetrievalError("Repeated catalog query parameters")
            if query["output_modalities"] != ["all"]:
                raise RetrievalError("Catalog pagination lost the all-modalities filter")
            if not query["offset"][0].isdigit() or not query["limit"][0].isdigit():
                raise RetrievalError("Invalid catalog paging values")
            if not 1 <= int(query["limit"][0]) <= 1000:
                raise RetrievalError("Catalog page size is outside the documented range")
        elif not catalog:
            parts = parsed.path.split("/")
            if (len(parts) != 7 or parts[:4] != ["", "api", "v1", "models"]
                    or parts[-1] != "endpoints" or parsed.query
                    or any(part in (".", "..") or not re.fullmatch(r"[A-Za-z0-9_.:~-]+", part) for part in parts[4:6])):
                raise RetrievalError("Unexpected model-endpoint route")
        else:
            raise RetrievalError("Pagination changed the catalog route")
        return url

    def retry_delay(self, header, attempt):
        wait = 2.0 ** (attempt + 1)
        if header is not None:
            try:
                wait = max(0.0, float(header))
            except ValueError:
                try:
                    when = parsedate_to_datetime(header)
                    if when.tzinfo is None:
                        when = when.replace(tzinfo=timezone.utc)
                    wait = max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
                except (ValueError, TypeError, OverflowError):
                    pass  # Invalid retry hint: use bounded exponential backoff.
        if not 0 <= wait <= self.max_wait:
            raise RetrievalError("Server retry wait exceeds this run's wait budget; stopped without retrying early")
        return wait

    def get_json(self, value, destination, *, catalog=False):
        url = self.checked_url(value, catalog=catalog)
        for attempt in range(self.retries + 1):
            if self.requests:
                self.sleep(self.delay)  # Sequential pacing also applies to retries.
            headers = {"Accept": "application/json", "User-Agent": "BSAD6153-catalog-review/1.0"}
            record = {"url": url, "attempt": attempt + 1, "started_at": utc_now()}
            self.requests.append(record)
            retry_hint = None
            try:
                with self.opener.open(Request(url, headers=headers), timeout=self.timeout) as response:
                    record["status"] = response.status
                    body = response.read(16 * 1024 * 1024 + 1)
                if len(body) > 16 * 1024 * 1024:
                    raise RetrievalError("Response exceeds the per-request size budget")
                try:
                    payload = json.loads(body)
                except (ValueError, UnicodeError):
                    save_bytes(self.output / (destination + ".invalid"), body)
                    raise RetrievalError("Invalid JSON response was archived and reported") from None
                path = self.output / destination
                save_bytes(path, body)  # Preserve the original successful response bytes.
                record["raw_file"] = destination
                return payload
            except HTTPError as error:
                record["status"] = error.code
                retry_hint = error.headers.get("Retry-After")
                error.close()
                if error.code in (401, 403):
                    raise RetrievalError(f"HTTP {error.code}: access was refused; anonymous metadata access denied") from None
                if error.code not in (408, 429) and not 500 <= error.code <= 599:
                    raise RetrievalError(f"HTTP {error.code}: request was not retried") from None
                reason = "http_" + str(error.code)
            except (URLError, TimeoutError, OSError, HTTPException) as error:
                underlying = getattr(error, "reason", error)
                if isinstance(underlying, (ssl.SSLError, ssl.CertificateError)):
                    raise RetrievalError("TLS verification failed; no security checks were bypassed") from None
                reason = "timeout" if isinstance(underlying, TimeoutError) else "connection_error"
                record["error"] = reason
            if attempt == self.retries:
                raise RetrievalError("Retry budget exhausted after " + reason)
            wait = self.retry_delay(retry_hint, attempt)
            self.waits.append({"reason": reason, "seconds": wait, "request": len(self.requests)})
            self.sleep(wait)
        raise AssertionError("Unreachable retry state")


def newest_catalog_first(row):
    """Order by catalog addition time, not model release date or quality."""
    created = row.get("created")
    created = created if type(created) is int and 0 <= created <= 253402300799 else -1
    return (-created, row["id"])


def collect(client, *, page_size=100, endpoint_models=10, minimum_models=500, max_pages=100):
    models, endpoints, issues, warnings = {}, {}, [], []
    summary = {"started_at": utc_now(), "source": client.base_url, "resource": "catalog metadata",
               "paid_inference_calls": 0, "authentication": "anonymous catalog GET",
               "minimum_main_records": minimum_models, "minimum_request_gap_seconds": client.delay,
               "related_record_selection": "most_recent_catalog_created_text_with_tools",
               "issues": issues, "warnings": warnings}
    finished, totals, visited, duplicate_models = False, [], set(), 0
    url = client.base_url + "/api/v1/models?" + urlencode({"output_modalities": "all", "limit": page_size, "offset": 0})
    selected, endpoint_successes, without_providers = [], 0, []
    try:
        for page_number in range(1, max_pages + 1):
            url = client.checked_url(url, catalog=True)
            if url in visited:
                raise RetrievalError("Repeated catalog pagination URL")
            visited.add(url)
            page = client.get_json(url, f"catalog/page-{page_number:04d}.json", catalog=True)
            if not isinstance(page, dict) or not isinstance(page.get("data"), list):
                raise RetrievalError("Catalog response has no records array")
            total = page.get("total_count")
            if isinstance(total, bool) or not isinstance(total, int) or total < 0:
                raise RetrievalError("Catalog response has no valid total count")
            totals.append(total)
            for row in page["data"]:
                model_id = row.get("id") if isinstance(row, dict) else None
                if not isinstance(model_id, str) or not model_id or any(c.isspace() for c in model_id):
                    issues.append("Skipped a model record with a missing/invalid ID")
                    continue
                if model_id in models:
                    duplicate_models += 1
                    if models[model_id] != row:
                        issues.append("Conflicting payloads for one model ID")
                    continue
                models[model_id] = row
                for field in ("name", "pricing", "architecture", "supported_parameters"):
                    if row.get(field) is None:
                        warnings.append(f"Model {model_id}: {field} is missing/null; preserved as unknown")
                for field, expected in (("pricing", dict), ("architecture", dict),
                                        ("supported_parameters", list), ("links", dict)):
                    if row.get(field) is not None and not isinstance(row[field], expected):
                        warnings.append(f"Model {model_id}: malformed {field}; not trusted for endpoint selection")
            links = page.get("links")
            if not isinstance(links, dict) or "next" not in links:
                raise RetrievalError("Catalog pagination boundary is missing")
            next_url = links["next"]
            if next_url is None:
                finished = True
                break
            checked = client.checked_url(next_url, catalog=True)
            old_offset = int(parse_qs(urlsplit(url).query)["offset"][0])
            new_offset = int(parse_qs(urlsplit(checked).query)["offset"][0])
            if not page["data"] or new_offset <= old_offset:
                raise RetrievalError("Catalog pagination made no forward progress")
            url = checked
        if not finished:
            issues.append("Catalog page limit reached before completion")
        if len(set(totals)) > 1:
            issues.append("Catalog reported total changed during retrieval; coverage is uncertain")
        if totals and len(models) != totals[-1]:
            issues.append("Unique retrieved model count differs from the reported total")
    except RetrievalError as error:
        issues.append(str(error))

    if finished:
        candidates = sorted(models.values(), key=newest_catalog_first)
        seen_details = set()
        for row in candidates:
            architecture = row.get("architecture") or {}
            output_modalities = architecture.get("output_modalities") if isinstance(architecture, dict) else None
            if not isinstance(output_modalities, list) or "text" not in output_modalities:
                continue
            parameters = row.get("supported_parameters")
            if not isinstance(parameters, list) or "tools" not in parameters:
                continue
            links = row.get("links")
            details = links.get("details") if isinstance(links, dict) else None
            if not details:
                warnings.append(f"Model {row['id']}: no endpoint-details link; not selected")
                continue
            try:
                details = client.checked_url(details)
            except RetrievalError as error:
                issues.append(str(error))
                continue
            if details in seen_details:
                continue
            seen_details.add(details)
            selected.append({"catalog_id": row["id"], "url": details})
            if len(selected) == endpoint_models:
                break
        if not selected:
            issues.append("No text/tool-capable models with valid endpoint links were available")
        for index, source in enumerate(selected, 1):
            try:
                payload = client.get_json(source["url"], f"endpoints/model-{index:04d}.json")
                data = payload.get("data") if isinstance(payload, dict) else None
                rows = data.get("endpoints") if isinstance(data, dict) else None
                if not isinstance(rows, list):
                    raise RetrievalError("Selected model returned an invalid endpoint-records array")
                if not rows:
                    without_providers.append(source["catalog_id"])
                    warnings.append(f"Model {source['catalog_id']}: provider list is empty; raw response preserved, no availability assumed")
                    continue
                accepted = 0
                for row in rows:
                    if (not isinstance(row, dict) or not isinstance(row.get("model_id"), str)
                            or row["model_id"] not in models
                            or not isinstance(row.get("provider_name"), str) or not row["provider_name"]
                            or not (row.get("tag") or row.get("name"))):
                        issues.append("Skipped endpoint with missing fields or an unmatched parent model")
                        continue
                    key = tuple(row.get(field) for field in ("model_id", "provider_name", "tag", "name", "service_tier"))
                    try:
                        hash(key)
                    except TypeError:
                        issues.append("Skipped endpoint with malformed identity fields")
                        continue
                    if key in endpoints and endpoints[key] != row:
                        issues.append("Conflicting payloads for an endpoint identity")
                    endpoints.setdefault(key, row)
                    accepted += 1
                if accepted:
                    endpoint_successes += 1
                else:
                    issues.append("Selected model had no usable related records")
            except RetrievalError as error:
                issues.append(f"Related-record request {index}: {error}")
    if len(models) < minimum_models:
        issues.append(f"Fewer than {minimum_models} unique catalog records were retrieved")
    if not endpoints:
        issues.append("No valid related endpoint records were retrieved")
    canonical = {row.get("canonical_slug") for row in models.values() if isinstance(row.get("canonical_slug"), str)}
    summary.update(finished_at=utc_now(), catalog_finished=finished, reported_totals=totals,
                   catalog_pages=len(visited), unique_catalog_ids=len(models), unique_canonical_slugs=len(canonical),
                   duplicate_catalog_ids=duplicate_models, related_endpoints=len(endpoints),
                   endpoint_models_selected=len(selected), endpoint_models_succeeded=endpoint_successes,
                   endpoint_models_without_providers=without_providers,
                   endpoint_sources=selected, requests=client.requests, retry_waits=client.waits,
                   complete=finished and len(models) >= minimum_models and bool(endpoints)
                   and endpoint_successes + len(without_providers) == len(selected) and not issues)
    write_json(client.output / "models.json", {"data": list(models.values())})
    write_json(client.output / "endpoints.json", {"data": list(endpoints.values())})
    write_json(client.output / "summary.json", summary)
    return summary
