"""Safe, status-only Vercel entry point for JARVIS OS."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Final
from urllib.parse import urlsplit


STATUS: Final[dict[str, str]] = {
    "service": "JARVIS OS",
    "status": "online",
    "deployment_mode": "status-foundation",
    "primary_mode": "local-cli",
    "release": "v0.6.0-alpha",
    "vision": "partial",
    "online_sync": "not_started",
    "web_automation": "partial_read_only",
    "mobile_automation": "partial_planning_only",
}

ROOT_PAGE: Final[str] = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JARVIS OS Status</title></head>
<body><main>
<h1>JARVIS OS</h1>
<p>JARVIS OS is currently CLI-first. This deployment is only the online status foundation.</p>
<p>Full cloud sync and web or mobile automation are not available yet. Local-only features run on the user's device.</p>
<p><a href="/api/status">View deployment status</a></p>
</main></body></html>"""


def build_response(path: str) -> tuple[int, str, bytes]:
    """Build a bounded response without reading environment or local runtime state."""
    route = urlsplit(path).path.rstrip("/") or "/"
    if route in {"/api/health", "/api/status"}:
        return 200, "application/json; charset=utf-8", json.dumps(STATUS, sort_keys=True).encode("utf-8")
    if route == "/":
        return 200, "text/html; charset=utf-8", ROOT_PAGE.encode("utf-8")
    body = json.dumps({"error": "not_found", "status": 404}).encode("utf-8")
    return 404, "application/json; charset=utf-8", body


class handler(BaseHTTPRequestHandler):
    """Vercel Python Function handler for the status-only deployment."""

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        status, content_type, body = build_response(self.path)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=60")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Avoid emitting request details from this status-only function."""
