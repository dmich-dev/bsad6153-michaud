"""Exercise HTTP behavior against a local server; no external API calls."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

SPEC = importlib.util.spec_from_file_location("fetch", Path(__file__).parents[1] / "ingest/fetch.py")
fetch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch)


def model(name):
    return {"id": "lab/" + name, "canonical_slug": "lab/" + name,
            "name": name, "pricing": {"prompt": "0"},
            "architecture": {"output_modalities": ["text"]}, "supported_parameters": ["tools"],
            "links": {"details": "/api/v1/models/lab/" + name + "/endpoints"}}


def endpoint(name):
    return {"model_id": "lab/" + name, "provider_name": "Provider", "tag": "provider", "name": name}


@contextmanager
def server(route):
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append({"path": self.path, "authorization": self.headers.get("Authorization")})
            code, payload, headers = route(self.path, len(seen))
            body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            for key, value in headers.items():
                self.send_header(key, str(value))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(http.server_port), seen
    finally:
        http.shutdown()
        http.server_close()
        thread.join()


class FetchTests(unittest.TestCase):
    def route(self, path, number):
        parts = urlsplit(path)
        if parts.path == "/api/v1/models":
            offset = int(parse_qs(parts.query)["offset"][0])
            if offset == 0:
                return 200, {"data": [model("a"), model("b")], "total_count": 3,
                             "links": {"next": "/api/v1/models?output_modalities=all&limit=2&offset=2"}}, {}
            return 200, {"data": [model("c")], "total_count": 3, "links": {"next": None}}, {}
        name = parts.path.split("/")[-2]
        return 200, {"data": {"endpoints": [endpoint(name)]}}, {}

    def run_case(self, route=None, **options):
        with tempfile.TemporaryDirectory() as directory, server(route or self.route) as (base, seen):
            waits = []
            client = fetch.Client(directory, base_url=base, key="synthetic-test-key", delay=0.01,
                                  retries=options.pop("retries", 2), sleep=waits.append, allow_local_http=True)
            result = fetch.collect(client, page_size=2, endpoint_models=options.pop("endpoint_models", 1), minimum_models=3, **options)
            files = {p.relative_to(directory).as_posix(): p.read_bytes() for p in Path(directory).rglob("*") if p.is_file()}
            return result, seen, waits, files

    def test_real_http_pagination_relationships_and_raw_preservation(self):
        result, seen, waits, files = self.run_case()
        self.assertTrue(result["complete"])
        self.assertEqual(result["unique_catalog_ids"], 3)
        self.assertEqual(result["related_endpoints"], 1)
        self.assertEqual(len(seen), 3)
        self.assertEqual(waits, [0.01, 0.01])
        self.assertTrue(all(item["authorization"] == "Bearer synthetic-test-key" for item in seen))
        self.assertEqual(json.loads(files["catalog/page-0001.json"])["data"][0], model("a"))
        self.assertNotIn(b"synthetic-test-key", b"".join(files.values()))

    def test_newest_catalog_entry_replaces_fixed_gpt41_and_invalid_dates_do_not_win(self):
        for created, expected in ((300, "lab/c"), ("9999999999", "openai/gpt-4.1"),
                                  (True, "openai/gpt-4.1"), (-10, "openai/gpt-4.1")):
            with self.subTest(created=created):
                def route(path, number):
                    if path == "/api/v1/models/openai/gpt-4.1/endpoints":
                        return 200, {"data": {"endpoints": [{"model_id": "openai/gpt-4.1", "provider_name": "Provider", "tag": "old"}]}}, {}
                    code, payload, headers = self.route(path, number)
                    if "?" in path:
                        for row in payload["data"]:
                            if row["id"] == "lab/a":
                                row.update(id="openai/gpt-4.1", created=100,
                                           links={"details": "/api/v1/models/openai/gpt-4.1/endpoints"})
                            elif row["id"] == "lab/c":
                                row["created"] = created
                    return code, payload, headers
                result, seen, _, _ = self.run_case(route)
                self.assertTrue(result["complete"])
                self.assertEqual(result["endpoint_sources"][0]["catalog_id"], expected)
                self.assertEqual(result["related_record_selection"], "most_recent_catalog_created_text_with_tools")

    def test_empty_provider_list_is_preserved_and_distinguished_from_invalid_response(self):
        for condition in ("one_empty", "all_empty", "invalid_array"):
            with self.subTest(condition=condition):
                def route(path, number):
                    code, payload, headers = self.route(path, number)
                    if path.endswith('/endpoints') and (condition == 'all_empty' or '/a/' in path):
                        payload['data']['endpoints'] = None if condition == 'invalid_array' else []
                    return code, payload, headers
                result, _, _, files = self.run_case(route, endpoint_models=2)
                self.assertEqual(result['complete'], condition == 'one_empty')
                saved = json.loads(files['endpoints/model-0001.json'])['data']['endpoints']
                self.assertIsNone(saved) if condition == 'invalid_array' else self.assertEqual(saved, [])
                if condition == 'one_empty':
                    self.assertEqual(result['related_endpoints'], 1)
                    self.assertEqual(result['endpoint_models_without_providers'], ['lab/a'])
                    self.assertTrue(result['warnings'])
                    self.assertFalse(result['issues'])

    def test_429_retry_after_and_server_error_fallback(self):
        def route(path, number):
            if number == 1:
                return 429, {}, {"Retry-After": "3"}
            if number == 2:
                return 503, {}, {}
            return self.route(path, number)
        result, _, waits, _ = self.run_case(route)
        self.assertTrue(result["complete"])
        self.assertEqual([item["seconds"] for item in result["retry_waits"]], [3, 4])
        self.assertIn(3, waits)
        self.assertIn(4, waits)

    def test_retry_exhaustion_is_incomplete_and_saved(self):
        result, seen, _, files = self.run_case(lambda path, n: (503, {}, {}))
        self.assertFalse(result["complete"])
        self.assertEqual(len(seen), 3)
        self.assertIn("summary.json", files)

    def test_long_retry_hint_stops_without_retrying_early(self):
        result, seen, waits, _ = self.run_case(lambda path, n: (429, {}, {"Retry-After": "1000"}))
        self.assertFalse(result["complete"])
        self.assertEqual(len(seen), 1)
        self.assertEqual(waits, [])

    def test_missing_boundary_and_changing_total_are_incomplete(self):
        for condition in ("missing_boundary", "changed_total"):
            with self.subTest(condition=condition):
                def route(path, number):
                    code, payload, headers = self.route(path, number)
                    if "?" in path and condition == "missing_boundary":
                        payload["links"] = {}
                    if "offset=2" in path and condition == "changed_total":
                        payload["total_count"] = 4
                    return code, payload, headers
                result, _, _, _ = self.run_case(route)
                self.assertFalse(result["complete"])

    def test_response_echoing_key_is_not_saved(self):
        result, seen, _, files = self.run_case(lambda path, n: (200, {"echo": "synthetic-test-key"}, {}))
        self.assertFalse(result["complete"])
        self.assertNotIn(b"synthetic-test-key", b"".join(files.values()))
        self.assertEqual(len(seen), 1)

    def test_authentication_failure_is_not_retried(self):
        result, seen, _, _ = self.run_case(lambda path, n: (401, {}, {}))
        self.assertFalse(result["complete"])
        self.assertEqual(len(seen), 1)

    def test_redirect_is_not_followed_or_leaked(self):
        result, seen, _, _ = self.run_case(lambda path, n: (302, {}, {"Location": "https://example.invalid/"}))
        self.assertFalse(result["complete"])
        self.assertEqual(len(seen), 1)

    def test_off_origin_pagination_is_rejected_before_request(self):
        def route(path, number):
            code, payload, headers = self.route(path, number)
            payload["links"]["next"] = "https://example.invalid/api/v1/models?output_modalities=all&limit=2&offset=2"
            return code, payload, headers
        result, seen, _, _ = self.run_case(route)
        self.assertFalse(result["complete"])
        self.assertEqual(len(seen), 1)

    def test_repeated_or_lost_filter_pages_fail(self):
        for next_url in ("/api/v1/models?output_modalities=all&limit=2&offset=0",
                         "/api/v1/models?limit=2&offset=2"):
            with self.subTest(next_url=next_url):
                def route(path, number):
                    code, payload, headers = self.route(path, number)
                    payload["links"]["next"] = next_url
                    return code, payload, headers
                result, seen, _, _ = self.run_case(route)
                self.assertFalse(result["complete"])
                self.assertEqual(len(seen), 1)

    def test_invalid_json_archived_without_success(self):
        result, _, _, files = self.run_case(lambda path, n: (200, b"not JSON", {}))
        self.assertFalse(result["complete"])
        self.assertEqual(files["catalog/page-0001.json.invalid"], b"not JSON")

    def test_missing_id_and_orphan_endpoint_are_reported(self):
        def route(path, number):
            code, payload, headers = self.route(path, number)
            if "?" in path and "offset=0" in path:
                payload["data"].append({"name": "no identifier"})
            if path.endswith("/endpoints"):
                payload["data"]["endpoints"] = [endpoint("not-in-catalog"), {"model_id": []}]
            return code, payload, headers
        result, _, _, _ = self.run_case(route)
        self.assertFalse(result["complete"])
        self.assertEqual(result["related_endpoints"], 0)
        self.assertTrue(any("missing/invalid ID" in issue for issue in result["issues"]))

    def test_duplicates_cannot_inflate_main_count(self):
        def route(path, number):
            code, payload, headers = self.route(path, number)
            if "offset=2" in path:
                payload["data"] = [model("a")]
            return code, payload, headers
        result, _, _, _ = self.run_case(route)
        self.assertFalse(result["complete"])
        self.assertEqual(result["unique_catalog_ids"], 2)
        self.assertEqual(result["duplicate_catalog_ids"], 1)

    def test_optional_missing_fields_and_malformed_links_do_not_crash(self):
        def route(path, number):
            code, payload, headers = self.route(path, number)
            if "offset=0" in path:
                payload["data"][1]["pricing"] = None
                payload["data"][1]["links"] = []
            return code, payload, headers
        result, _, _, _ = self.run_case(route)
        self.assertTrue(result["complete"])
        self.assertTrue(result["warnings"])

    def test_wait_budget_date_hint_and_timeout_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            waits = []
            client = fetch.Client(directory, retries=1, sleep=waits.append)
            future = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=5))
            self.assertGreater(client.retry_delay(future, 0), 0)
            with self.assertRaises(fetch.RetrievalError):
                client.retry_delay("1000", 0)
            with patch.object(client.opener, "open", side_effect=TimeoutError):
                with self.assertRaises(fetch.RetrievalError):
                    client.get_json(BASE + "?output_modalities=all&limit=2&offset=0", "catalog/test.json", catalog=True)
            self.assertEqual(len(client.requests), 2)
            self.assertEqual(client.waits[0]["reason"], "timeout")

    def test_env_key_is_literal_and_not_echoed(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / ".env"
            path.write_text('OPENROUTER_API_KEY="synthetic-key" # local\nOTHER_KEY=ignored\n')
            self.assertEqual(fetch.load_key(path), "synthetic-key")
            path.write_text('OPENROUTER_API_KEY="unterminated\n')
            with self.assertRaises(fetch.RetrievalError):
                fetch.load_key(path)


BASE = "https://openrouter.ai/api/v1/models"
if __name__ == "__main__":
    unittest.main()
