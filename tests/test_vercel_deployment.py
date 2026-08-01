"""Regression tests for the status-only Vercel deployment boundary."""

from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

from api.index import STATUS, build_response, handler


ROOT = Path(__file__).resolve().parents[1]


class VercelDeploymentTests(unittest.TestCase):
    def test_config_builds_only_the_online_entrypoint(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertEqual(config["builds"], [{"src": "api/index.py", "use": "@vercel/python"}])
        destinations = {route["dest"] for route in config["routes"]}
        self.assertEqual(destinations, {"/api/index.py"})
        self.assertNotIn("main.py", json.dumps(config))

    def test_cli_entrypoint_remains_cli_only(self) -> None:
        spec = importlib.util.spec_from_file_location("jarvis_cli_main", ROOT / "main.py")
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(callable(module.main))
        for deployment_name in ("app", "application", "handler"):
            self.assertFalse(hasattr(module, deployment_name))

    def test_vercel_handler_contract_is_available(self) -> None:
        self.assertTrue(issubclass(handler, object))
        self.assertTrue(callable(handler.do_GET))

    def test_health_and_status_return_safe_schema(self) -> None:
        required = {
            "service", "status", "deployment_mode", "primary_mode", "release",
            "vision", "online_sync", "web_automation", "mobile_automation",
        }
        for path in ("/api/health", "/api/status", "/api/status?source=test"):
            with self.subTest(path=path):
                status, content_type, body = build_response(path)
                payload = json.loads(body)
                self.assertEqual(status, 200)
                self.assertEqual(content_type, "application/json; charset=utf-8")
                self.assertEqual(set(payload), required)
                self.assertEqual(payload, STATUS)
                self.assertEqual(payload["web_automation"], "partial_read_only")

    def test_status_exposes_no_secrets_or_local_paths(self) -> None:
        body = json.dumps(STATUS)
        self.assertIsNone(re.search(r"(?i)(api[_-]?key|password|token|secret)\s*[:=]", body))
        self.assertNotRegex(body, r"[A-Za-z]:\\")
        self.assertNotIn("/Users/", body)
        self.assertNotIn("/home/", body)

    def test_root_page_explains_the_limited_online_surface(self) -> None:
        status, content_type, body = build_response("/")
        page = body.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "text/html; charset=utf-8")
        self.assertIn("CLI-first", page)
        self.assertIn("status foundation", page)
        self.assertIn("Local-only features", page)

    def test_unknown_route_is_bounded_json_404(self) -> None:
        status, content_type, body = build_response("/private")
        self.assertEqual(status, 404)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(json.loads(body), {"error": "not_found", "status": 404})


if __name__ == "__main__":
    unittest.main()
