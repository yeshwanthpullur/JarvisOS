"""Localhost-only desktop interface for the existing JARVIS runtime."""

from __future__ import annotations

import hmac
import ipaddress
import json
import logging
import re
import secrets
import socket
import threading
import time
import webbrowser
from collections import deque
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from config.schema import InterfaceConfig
from core import StartupManager


LOGGER = logging.getLogger("local_interface")
STATIC_DIRECTORY = Path(__file__).resolve().parents[1] / "desktop"
TOKEN_PLACEHOLDER = "__JARVIS_SESSION_TOKEN__"
SECRET_PATTERN = re.compile(
    r"(?i)(authorization|api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[^\s,;]+"
)
AUTHORIZATION_PATTERN = re.compile(r"(?i)authorization\s*[:=]\s*(?:bearer\s+)?[^\s,;]+")
BEARER_PATTERN = re.compile(r"(?i)bearer\s+[a-z0-9._~+/-]+")
HIDDEN_REASONING_PATTERN = re.compile(r"(?i)(chain[- ]of[- ]thought|hidden reasoning|private scratch)")


class LoopbackThreadingHTTPServer(ThreadingHTTPServer):
    """Prevent multiple desktop-interface processes from sharing one port."""

    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def json_safe(value: Any) -> Any:
    """Convert observable models to JSON-safe values without hidden internals."""
    if is_dataclass(value):
        return {key: json_safe(item) for key, item in asdict(value).items()}
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def redact_text(value: str, maximum_length: int = 2000) -> str:
    """Redact credentials and hidden-reasoning markers from observable text."""
    redacted = AUTHORIZATION_PATTERN.sub("Authorization=[REDACTED]", value)
    redacted = SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", redacted)
    redacted = BEARER_PATTERN.sub("Bearer [REDACTED]", redacted)
    redacted = HIDDEN_REASONING_PATTERN.sub("[REDACTED INTERNAL CONTENT]", redacted)
    return redacted[:maximum_length]


@dataclass(frozen=True, slots=True)
class InterfaceResponse:
    interface_request_id: str
    jarvis_request_id: str | None
    conversation_id: str | None
    status: str
    response_type: str
    content: str
    safe_markdown: bool = True
    provider_id: str | None = None
    model_id: str | None = None
    command_name: str | None = None
    tool_invocation_id: str | None = None
    coordination_id: str | None = None
    plan_id: str | None = None
    workflow_id: str | None = None
    approval_id: str | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    created_at: str = ""
    completed_at: str | None = None
    duration: float = 0.0
    cancellable: bool = False


@dataclass(frozen=True, slots=True)
class ActivityRecord:
    sequence: int
    event_type: str
    status: str
    request_id: str | None
    summary: str
    created_at: str
    duration: float = 0.0
    provider_id: str | None = None
    model_id: str | None = None
    invocation_id: str | None = None
    coordination_id: str | None = None
    plan_id: str | None = None
    error: str | None = None


class LocalInterfaceService:
    """Presentation adapter over the already initialized JARVIS runtime."""

    def __init__(
        self,
        startup: StartupManager,
        config: InterfaceConfig,
        *,
        static_directory: Path = STATIC_DIRECTORY,
        logger: logging.Logger | None = None,
    ) -> None:
        self.startup = startup
        self.config = config
        self.static_directory = static_directory.resolve()
        self.logger = logger or LOGGER
        self.session_token = secrets.token_urlsafe(32)
        self.session_created_at = time.monotonic()
        self._server: ThreadingHTTPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._stopped = threading.Event()
        self._stop_lock = threading.Lock()
        self._conversation_lock = threading.RLock()
        self._request_slots = threading.BoundedSemaphore(2)
        self._stream_slots = threading.BoundedSemaphore(4)
        self._active_requests: dict[str, threading.Event] = {}
        self._request_results: dict[str, InterfaceResponse] = {}
        self._activity: deque[ActivityRecord] = deque(maxlen=config.max_activity_entries)
        self._event_sequence = 0
        self._activity_lock = threading.Lock()
        self._preferences: dict[str, object] = {
            "theme": config.theme,
            "density": "compact" if config.compact_mode else "comfortable",
            "auto_scroll": True,
            "notifications": False,
            "last_view": config.default_view,
        }
        self._validate_binding()
        self.logger.info("interface_initialized host=%s port=%s", config.host, config.port)

    @property
    def url(self) -> str:
        port = self._server.server_address[1] if self._server is not None else self.config.port
        return f"http://{self.config.host}:{port}"

    @property
    def running(self) -> bool:
        return self._server is not None and not self._stopping.is_set()

    def _validate_binding(self) -> None:
        try:
            address = ipaddress.ip_address(self.config.host)
            loopback = address.is_loopback
        except ValueError:
            loopback = self.config.host.lower() == "localhost"
        if not loopback and not self.config.allow_remote:
            raise ValueError("remote_interface_binding_blocked")
        if self.config.allow_remote:
            raise ValueError("remote_interface_not_supported_in_this_milestone")
        if not 1 <= self.config.port <= 65535:
            raise ValueError("invalid_interface_port")

    def start(self, *, background: bool = False, open_browser: bool | None = None) -> None:
        """Bind the loopback service and optionally serve in a background thread."""
        self._stopping.clear()
        self._stopped.clear()
        self.logger.info("interface_starting host=%s port=%s", self.config.host, self.config.port)
        handler = self._handler_class()
        self._server = LoopbackThreadingHTTPServer((self.config.host, self.config.port), handler)
        self._server.daemon_threads = True
        self._server.service = self  # type: ignore[attr-defined]
        self._record("interface_started", "completed", None, f"Interface ready at {self.url}")
        self.logger.info("interface_started host=%s port=%s", self.config.host, self._server.server_address[1])
        should_open = self.config.open_browser if open_browser is None else open_browser
        if should_open:
            try:
                webbrowser.open(self.url, new=1)
            except Exception as exc:  # pragma: no cover - platform dependent
                self.logger.warning("interface_browser_open_failed error=%s", type(exc).__name__)
        if background:
            self._server_thread = threading.Thread(
                target=self._server.serve_forever,
                name="jarvis-local-interface",
                daemon=True,
            )
            self._server_thread.start()
            return
        self._server.serve_forever()

    def stop(self) -> None:
        """Stop accepting requests and release the interface port."""
        with self._stop_lock:
            server = self._server
            if server is None:
                return
            if self._stopping.is_set():
                wait_for_stop = True
            else:
                self._stopping.set()
                wait_for_stop = False
        if wait_for_stop:
            self._stopped.wait(timeout=5)
            return
        self.logger.info("interface_stopping")
        voice = self._voice()
        if voice is not None:
            voice.interrupt()
        for cancellation in tuple(self._active_requests.values()):
            cancellation.set()
        try:
            server.shutdown()
            server.server_close()
            if self._server_thread is not None and self._server_thread is not threading.current_thread():
                self._server_thread.join(timeout=5)
            with self._stop_lock:
                if self._server is server:
                    self._server = None
            self.logger.info("interface_stopped")
        finally:
            self._stopped.set()

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        service = self

        class InterfaceHandler(BaseHTTPRequestHandler):
            server_version = "JarvisLocalInterface/1"
            protocol_version = "HTTP/1.1"

            def log_message(self, format_string: str, *args: object) -> None:
                service.logger.debug("interface_http %s", format_string % args)

            def do_GET(self) -> None:  # noqa: N802
                service._handle_get(self)

            def do_POST(self) -> None:  # noqa: N802
                service._handle_post(self)

        return InterfaceHandler

    def _request_allowed(self, handler: BaseHTTPRequestHandler, *, mutation: bool) -> tuple[bool, str]:
        try:
            if not ipaddress.ip_address(handler.client_address[0]).is_loopback:
                return False, "non_local_client"
        except ValueError:
            return False, "invalid_client_address"
        host = handler.headers.get("Host", "")
        host_name = host.rsplit(":", 1)[0].strip("[]").lower()
        if host_name not in {"127.0.0.1", "localhost", "::1"}:
            return False, "invalid_host"
        origin = handler.headers.get("Origin")
        current_origins = {self.url, self.url.replace("127.0.0.1", "localhost")}
        allowed_origins = current_origins | set(self.config.allowed_origins)
        if origin and origin not in allowed_origins:
            return False, "invalid_origin"
        if mutation:
            token = handler.headers.get("X-Jarvis-Session", "")
            if time.monotonic() - self.session_created_at > self.config.session_token_lifetime:
                return False, "session_expired"
            if not token or not hmac.compare_digest(token, self.session_token):
                return False, "invalid_session_token"
        return True, "allowed"

    def _handle_get(self, handler: BaseHTTPRequestHandler) -> None:
        allowed, reason = self._request_allowed(handler, mutation=False)
        if not allowed:
            self._security_rejection(handler, reason)
            return
        parsed = urlparse(handler.path)
        if parsed.path == "/api/events":
            self._serve_events(handler)
            return
        if parsed.path.startswith("/api/"):
            self._serve_api_get(handler, parsed.path, parse_qs(parsed.query))
            return
        self._serve_static(handler, parsed.path)

    def _handle_post(self, handler: BaseHTTPRequestHandler) -> None:
        allowed, reason = self._request_allowed(handler, mutation=True)
        if not allowed:
            self._security_rejection(handler, reason)
            return
        content_length = int(handler.headers.get("Content-Length", "0") or 0)
        if content_length <= 0:
            self._write_json(handler, HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"status": "rejected", "error": "invalid_request_size"})
            return
        if content_length > self.config.max_request_size:
            # Drain only modest rejected bodies so Windows can deliver the 413
            # instead of resetting a connection that still has unread bytes.
            drain_limit = min(max(self.config.max_request_size * 2, 65_536), 131_072)
            if content_length <= drain_limit:
                handler.rfile.read(content_length)
            else:
                handler.close_connection = True
            self._write_json(handler, HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"status": "rejected", "error": "invalid_request_size"})
            return
        try:
            payload = json.loads(handler.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._write_json(handler, HTTPStatus.BAD_REQUEST, {"status": "rejected", "error": "malformed_json"})
            return
        if not isinstance(payload, dict):
            self._write_json(handler, HTTPStatus.BAD_REQUEST, {"status": "rejected", "error": "object_body_required"})
            return
        path = urlparse(handler.path).path
        routes = {
            "/api/messages": self.start_message,
            "/api/cancel": self.cancel,
            "/api/conversations": self.create_conversation,
            "/api/conversations/open": self.open_conversation,
            "/api/voice/speak": self.speak,
            "/api/voice/stop": self.stop_voice,
            "/api/approvals/decision": self.decide_approval,
            "/api/settings": self.update_settings,
            "/api/shutdown": self.request_shutdown,
        }
        operation = routes.get(path)
        if operation is None:
            self._write_json(handler, HTTPStatus.NOT_FOUND, {"status": "failed", "error": "endpoint_not_found"})
            return
        try:
            result = operation(payload)
            self._write_json(handler, HTTPStatus.OK, result)
        except ValueError as exc:
            self.logger.info("interface_request_rejected failure_reason=%s", str(exc))
            self._write_json(handler, HTTPStatus.BAD_REQUEST, {"status": "rejected", "error": redact_text(str(exc), 240)})
        except Exception as exc:  # pragma: no cover - defensive API boundary
            self.logger.exception("interface_request_failed failure_reason=%s", type(exc).__name__)
            self._write_json(handler, HTTPStatus.INTERNAL_SERVER_ERROR, {"status": "failed", "error": "interface_operation_failed"})

    def _serve_api_get(self, handler: BaseHTTPRequestHandler, path: str, query: dict[str, list[str]]) -> None:
        if path == "/api/bootstrap":
            data = self.bootstrap()
        elif path == "/api/health":
            data = self.health()
        elif path == "/api/status":
            data = self.status()
        elif path == "/api/conversations":
            data = {"conversations": self.conversations()}
        elif path.startswith("/api/conversations/"):
            data = self.conversation(path.rsplit("/", 1)[-1])
        elif path == "/api/activity":
            data = {"activity": self.activity()}
        elif path.startswith("/api/requests/"):
            data = self.request_status(path.rsplit("/", 1)[-1])
        elif path == "/api/logs":
            data = {"logs": self.safe_logs(query)}
        elif path == "/api/providers":
            data = self.providers()
        elif path == "/api/voice":
            data = self.voice_status()
        elif path == "/api/tools":
            data = {"tools": self.tools()}
        elif path.startswith("/api/tools/"):
            data = self.tool(path.rsplit("/", 1)[-1])
        elif path == "/api/plans":
            data = {"plans": self.plans()}
        elif path.startswith("/api/plans/"):
            data = self.plan(path.rsplit("/", 1)[-1])
        elif path == "/api/multiagent":
            data = {"coordinations": self.coordinations()}
        elif path.startswith("/api/multiagent/"):
            data = self.coordination(path.rsplit("/", 1)[-1])
        elif path == "/api/approvals":
            data = {"approvals": self.approvals()}
        elif path == "/api/settings":
            data = self.settings()
        else:
            self._write_json(handler, HTTPStatus.NOT_FOUND, {"status": "failed", "error": "endpoint_not_found"})
            return
        self._write_json(handler, HTTPStatus.OK, data)

    def _serve_static(self, handler: BaseHTTPRequestHandler, path: str) -> None:
        mapping = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/app.css": ("app.css", "text/css; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
        }
        record = mapping.get(path)
        if record is None:
            self._write_json(handler, HTTPStatus.NOT_FOUND, {"status": "failed", "error": "asset_not_found"})
            return
        asset_path = self.static_directory / record[0]
        try:
            data = asset_path.read_bytes()
        except OSError:
            self._write_json(handler, HTTPStatus.SERVICE_UNAVAILABLE, {"status": "failed", "error": "interface_asset_unavailable"})
            return
        if record[0] == "index.html":
            data = data.replace(TOKEN_PLACEHOLDER.encode("ascii"), self.session_token.encode("ascii"))
        self._write_bytes(handler, HTTPStatus.OK, data, record[1])

    def _write_json(self, handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: object) -> None:
        data = json.dumps(json_safe(payload), ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        if len(data) > self.config.max_response_size:
            data = json.dumps({"status": "failed", "error": "response_size_limit_exceeded"}).encode("utf-8")
            status = HTTPStatus.INTERNAL_SERVER_ERROR
        self._write_bytes(handler, status, data, "application/json; charset=utf-8")

    def _write_bytes(self, handler: BaseHTTPRequestHandler, status: HTTPStatus, data: bytes, content_type: str) -> None:
        handler.send_response(status)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        handler.send_header("X-Content-Type-Options", "nosniff")
        handler.send_header("X-Frame-Options", "DENY")
        handler.send_header("Referrer-Policy", "no-referrer")
        handler.end_headers()
        handler.wfile.write(data)

    def _security_rejection(self, handler: BaseHTTPRequestHandler, reason: str) -> None:
        self.logger.warning("interface_security_rejection failure_reason=%s", reason)
        self._write_json(handler, HTTPStatus.FORBIDDEN, {"status": "rejected", "error": reason})

    def _serve_events(self, handler: BaseHTTPRequestHandler) -> None:
        if not self._stream_slots.acquire(blocking=False):
            self._write_json(handler, HTTPStatus.TOO_MANY_REQUESTS, {"status": "blocked", "error": "event_stream_limit"})
            return
        self.logger.info("interface_event_stream_connected")
        try:
            handler.send_response(HTTPStatus.OK)
            handler.send_header("Content-Type", "text/event-stream")
            handler.send_header("Cache-Control", "no-store")
            handler.send_header("Connection", "close")
            handler.end_headers()
            query = parse_qs(urlparse(handler.path).query)
            requested_sequence = (query.get("since") or ["0"])[0]
            try:
                last_sequence = max(
                    int(handler.headers.get("Last-Event-ID", "0") or 0),
                    int(requested_sequence or 0),
                )
            except (TypeError, ValueError):
                last_sequence = 0
            deadline = time.monotonic() + self.config.event_timeout
            while not self._stopping.is_set() and time.monotonic() < deadline:
                events = [item for item in self.activity() if int(item["sequence"]) > last_sequence]
                if events:
                    for event in events:
                        last_sequence = int(event["sequence"])
                        packet = f"id: {last_sequence}\nevent: activity\ndata: {json.dumps(event, ensure_ascii=True)}\n\n"
                        handler.wfile.write(packet.encode("utf-8"))
                    handler.wfile.flush()
                else:
                    handler.wfile.write(b": heartbeat\n\n")
                    handler.wfile.flush()
                time.sleep(1)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, TimeoutError):
            pass
        finally:
            self._stream_slots.release()
            self.logger.info("interface_event_stream_disconnected")

    def _record(
        self,
        event_type: str,
        status: str,
        request_id: str | None,
        summary: str,
        **metadata: object,
    ) -> ActivityRecord:
        with self._activity_lock:
            self._event_sequence += 1
            record = ActivityRecord(
                self._event_sequence,
                event_type,
                status,
                request_id,
                redact_text(summary, 320),
                utc_now(),
                duration=float(metadata.get("duration", 0.0) or 0.0),
                provider_id=metadata.get("provider_id") if isinstance(metadata.get("provider_id"), str) else None,
                model_id=metadata.get("model_id") if isinstance(metadata.get("model_id"), str) else None,
                invocation_id=metadata.get("invocation_id") if isinstance(metadata.get("invocation_id"), str) else None,
                coordination_id=metadata.get("coordination_id") if isinstance(metadata.get("coordination_id"), str) else None,
                plan_id=metadata.get("plan_id") if isinstance(metadata.get("plan_id"), str) else None,
                error=redact_text(str(metadata["error"]), 240) if metadata.get("error") else None,
            )
            self._activity.append(record)
            return record

    def bootstrap(self) -> dict[str, object]:
        return {
            "application": "JARVIS OS",
            "version": "31.5-mvp",
            "interface": {"url": self.url, "host": self.config.host, "port": self._server.server_address[1] if self._server else self.config.port, "transport": self.config.event_transport},
            "status": self.status(),
            "health": self.health(),
            "conversations": self.conversations(),
            "settings": self.settings(),
        }

    def start_message(self, payload: dict[str, object]) -> InterfaceResponse:
        """Accept a UI request and expose its server-generated correlation ID immediately."""
        self._validate_message_payload(payload)
        if not self._request_slots.acquire(blocking=False):
            raise ValueError("concurrent_request_limit")
        interface_request_id = str(uuid4())
        cancellation = threading.Event()
        self._active_requests[interface_request_id] = cancellation
        manager = self.startup.conversation_manager
        accepted = InterfaceResponse(
            interface_request_id,
            interface_request_id,
            manager.active_session.conversation_id if manager else None,
            "accepted",
            "conversation",
            "",
            created_at=utc_now(),
            cancellable=True,
        )
        self._request_results[interface_request_id] = accepted

        def worker() -> None:
            try:
                result = self.submit_message(
                    payload,
                    interface_request_id=interface_request_id,
                    cancellation=cancellation,
                    slot_acquired=True,
                )
            except Exception:
                self.logger.exception("interface_request_failed interface_request_id=%s", interface_request_id)
                result = replace(
                    accepted,
                    status="failed",
                    content="JARVIS could not complete this request.",
                    errors=("interface_operation_failed",),
                    completed_at=utc_now(),
                    cancellable=False,
                )
            self._request_results[interface_request_id] = result
            if len(self._request_results) > self.config.max_activity_entries:
                oldest = next(iter(self._request_results))
                if oldest not in self._active_requests:
                    self._request_results.pop(oldest, None)

        threading.Thread(target=worker, name=f"jarvis-interface-{interface_request_id[:8]}", daemon=True).start()
        return accepted

    def request_status(self, interface_request_id: str) -> InterfaceResponse | dict[str, object]:
        return self._request_results.get(interface_request_id, {"status": "unavailable", "error": "request_not_found"})

    def _validate_message_payload(self, payload: dict[str, object]) -> str:
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message_required")
        if len(message) > min(16000, self.config.max_request_size // 2):
            raise ValueError("message_size_limit_exceeded")
        return message

    def submit_message(
        self,
        payload: dict[str, object],
        *,
        interface_request_id: str | None = None,
        cancellation: threading.Event | None = None,
        slot_acquired: bool = False,
    ) -> InterfaceResponse:
        """Run one validated message through the existing Conversation Manager."""
        message = self._validate_message_payload(payload)
        manager = self.startup.conversation_manager
        if manager is None or not manager.initialized:
            raise ValueError("conversation_engine_unavailable")
        conversation_id = payload.get("conversation_id")
        if conversation_id and (not isinstance(conversation_id, str) or not manager.activate_conversation(conversation_id)):
            raise ValueError("conversation_not_found")
        if not slot_acquired:
            if not self._request_slots.acquire(blocking=False):
                raise ValueError("concurrent_request_limit")
            interface_request_id = interface_request_id or str(uuid4())
            cancellation = cancellation or threading.Event()
            self._active_requests[interface_request_id] = cancellation
        assert interface_request_id is not None
        assert cancellation is not None
        created = utc_now()
        started = time.monotonic()
        parsed = manager.command_manager.parser.parse(message.strip().lower())
        is_command = manager.command_manager.registry.lookup(parsed.name) is not None
        self.logger.info("interface_request_received interface_request_id=%s conversation_id=%s", interface_request_id, manager.active_session.conversation_id)
        self._record("request_received", "processing", interface_request_id, "Request received")
        try:
            if cancellation.is_set():
                return InterfaceResponse(interface_request_id, interface_request_id, manager.active_session.conversation_id, "cancelled", "interface", "Request cancelled before execution.", created_at=created, completed_at=utc_now())
            self._record("request_validated", "processing", interface_request_id, "Request validated")
            self._record("reasoning_started" if not is_command else "command_started", "processing", interface_request_id, "Existing JARVIS processing started")
            with self._conversation_lock:
                if cancellation.is_set():
                    return InterfaceResponse(interface_request_id, interface_request_id, manager.active_session.conversation_id, "cancelled", "interface", "Request cancelled before execution.", created_at=created, completed_at=utc_now())
                response = manager.handle_input(message.strip(), request_id=interface_request_id)
            duration = time.monotonic() - started
            summary = dict(response.execution_summary)
            metadata = dict(response.metadata)
            provider_id = summary.get("provider_id")
            model_id = summary.get("model_id")
            response_type = "command" if is_command else str(summary.get("strategy") or "conversation")
            if summary.get("tool_id") or summary.get("invocation_id"):
                response_type = "tool"
            elif summary.get("coordination_id"):
                response_type = "multiagent"
            elif summary.get("plan_id"):
                response_type = "planning"
            status = "failed" if response.warnings and not response.response else "completed"
            content = response.response[: self.config.max_response_size // 2].strip()
            if is_command and parsed.name == "voice say" and "Audio reference:" in content:
                content = content.split("Audio reference:", 1)[0].rstrip() + " Local audio output is available."
            warnings = tuple(response.warnings)
            errors = tuple(response.diagnostics) if status == "failed" else ()
            if not content:
                status = "failed"
                content = "JARVIS received an empty response. Retry the request or select another provider."
                errors = (*errors, "empty_response")
            if len(response.response) > len(content):
                warnings = (*warnings, "response_display_limit_applied")
            normalized = InterfaceResponse(
                interface_request_id=interface_request_id,
                jarvis_request_id=str(metadata.get("jarvis_request_id") or interface_request_id),
                conversation_id=manager.active_session.conversation_id,
                status=status,
                response_type=response_type,
                content=content,
                safe_markdown=self.config.safe_markdown,
                provider_id=str(provider_id) if provider_id else None,
                model_id=str(model_id) if model_id else None,
                command_name=parsed.name if is_command else None,
                tool_invocation_id=str(summary.get("invocation_id")) if summary.get("invocation_id") else None,
                coordination_id=str(summary.get("coordination_id")) if summary.get("coordination_id") else None,
                plan_id=str(summary.get("plan_id")) if summary.get("plan_id") else None,
                workflow_id=str(summary.get("workflow_id")) if summary.get("workflow_id") else None,
                approval_id=str(summary.get("approval_id")) if summary.get("approval_id") else None,
                warnings=warnings,
                errors=errors,
                created_at=created,
                completed_at=utc_now(),
                duration=duration,
                cancellable=False,
            )
            self._record(
                "response_ready" if status == "completed" else "request_failed",
                status,
                interface_request_id,
                f"{response_type.title()} response ready",
                duration=duration,
                provider_id=normalized.provider_id,
                model_id=normalized.model_id,
                invocation_id=normalized.tool_invocation_id,
                coordination_id=normalized.coordination_id,
                plan_id=normalized.plan_id,
            )
            self.logger.info("interface_request_completed interface_request_id=%s jarvis_request_id=%s conversation_id=%s status=%s duration=%s", interface_request_id, normalized.jarvis_request_id, normalized.conversation_id, status, duration)
            return normalized
        finally:
            self._active_requests.pop(interface_request_id, None)
            self._request_slots.release()

    def cancel(self, payload: dict[str, object]) -> dict[str, object]:
        cancelled = False
        request_id = payload.get("request_id")
        if isinstance(request_id, str) and request_id in self._active_requests:
            self._active_requests[request_id].set()
            cancelled = True
        invocation_id = payload.get("invocation_id")
        tools = self._tools_manager()
        if isinstance(invocation_id, str) and tools is not None:
            cancelled = tools.cancel(invocation_id) or cancelled
        coordination_id = payload.get("coordination_id")
        orchestrator = self._orchestrator()
        if isinstance(coordination_id, str) and orchestrator is not None:
            cancelled = orchestrator.cancel(coordination_id) or cancelled
        plan_id = payload.get("plan_id")
        planning = self._planning()
        if isinstance(plan_id, str) and planning is not None and plan_id in planning.plans:
            planning.cancel(plan_id)
            cancelled = True
        voice = self._voice()
        if voice is not None:
            cancelled = voice.interrupt() or cancelled
        event = "request_cancelled" if cancelled else "request_cancel_failed"
        self._record(event, "cancelled" if cancelled else "unavailable", request_id if isinstance(request_id, str) else None, "Cancellation applied" if cancelled else "No matching cancellable operation")
        return {"status": "cancelled" if cancelled else "unavailable", "cancelled": cancelled}

    def create_conversation(self, payload: dict[str, object]) -> dict[str, object]:
        del payload
        manager = self.startup.conversation_manager
        if manager is None:
            raise ValueError("conversation_engine_unavailable")
        with self._conversation_lock:
            session = manager.create_conversation()
        return {"status": "completed", "conversation_id": session.conversation_id, "conversations": self.conversations()}

    def open_conversation(self, payload: dict[str, object]) -> dict[str, object]:
        conversation_id = payload.get("conversation_id")
        manager = self.startup.conversation_manager
        if not isinstance(conversation_id, str) or manager is None or not manager.activate_conversation(conversation_id):
            raise ValueError("conversation_not_found")
        return self.conversation(conversation_id)

    def conversations(self) -> list[dict[str, object]]:
        manager = self.startup.conversation_manager
        return list(manager.list_conversations()) if manager is not None else []

    def conversation(self, conversation_id: str) -> dict[str, object]:
        manager = self.startup.conversation_manager
        messages = manager.conversation_messages(conversation_id, self.config.max_history_messages) if manager is not None else None
        if messages is None:
            return {"status": "unavailable", "error": "conversation_not_found"}
        return {"status": "completed", "conversation_id": conversation_id, "messages": messages}

    def status(self) -> dict[str, object]:
        manager = self.startup.conversation_manager
        session = manager.active_session if manager is not None else None
        metadata = dict(session.metadata) if session is not None else {}
        provider_history = self.startup.provider_execution_manager.history.list() if self.startup.provider_execution_manager is not None else ()
        last = provider_history[-1] if provider_history else None
        return {
            "runtime": self.startup.status.state.value,
            "conversation": "ready" if manager is not None and manager.initialized else "unavailable",
            "conversation_id": session.conversation_id if session else None,
            "execution_policy": metadata.get("execution_policy", "automatic"),
            "local_only": bool(metadata.get("local_only", False)),
            "cloud_only": bool(metadata.get("cloud_only", False)),
            "provider_preference": metadata.get("provider_preference"),
            "model_preference": metadata.get("model_preference"),
            "last_provider": getattr(last, "provider", None),
            "last_model": getattr(last, "model", None),
            "last_latency_ms": getattr(last, "latency_ms", None),
            "active_requests": len(self._active_requests),
        }

    def health(self) -> dict[str, object]:
        provider_records = self.providers()["providers"]
        voice = self.voice_status()
        tools = self._tools_manager()
        orchestrator = self._orchestrator()
        planning = self._planning()
        checks = {item.name: item.status.value for item in self.startup.health_results}
        return {
            "overall": self.startup.status.state.value,
            "interface": "healthy" if self.running else "disabled",
            "conversation": "healthy" if self.startup.conversation_manager and self.startup.conversation_manager.initialized else "unavailable",
            "provider_execution": "healthy" if self.startup.provider_execution_manager and self.startup.provider_execution_manager.initialized else "unavailable",
            "ollama": next((item["health"] for item in provider_records if item["provider_id"] == "ollama"), "unavailable"),
            "tools": "healthy" if tools is not None else "unavailable",
            "multiagent": "healthy" if orchestrator is not None else "unavailable",
            "planning": "healthy" if planning is not None else "unavailable",
            "voice": "healthy" if voice.get("framework_ready") else "unavailable",
            "windows_sapi": voice.get("tts_status", "unknown"),
            "stt": voice.get("stt_status", "unknown"),
            "persistence": checks.get("memory", "unknown"),
            "temporary_storage": "healthy" if self.startup.settings and self.startup.settings.data_dir.exists() else "unavailable",
        }

    def providers(self) -> dict[str, object]:
        manager = self.startup.provider_manager
        records: list[dict[str, object]] = []
        if manager is not None:
            for record in manager.registry.all():
                provider = record.provider
                health = getattr(record.health, "available", False)
                models = provider.list_models() if provider is not None else ()
                records.append({
                    "provider_id": record.config.provider_id,
                    "kind": record.config.kind.value,
                    "local": bool(record.config.local_only),
                    "enabled": bool(record.config.enabled and provider is not None and provider.enabled),
                    "credentialed": bool(getattr(provider, "credential_ready", True)) if provider is not None else False,
                    "health": "healthy" if health else "unavailable" if record.config.enabled else "disabled",
                    "models": [item.model_id for item in models],
                    "latency_ms": getattr(record.health, "latency_ms", None),
                })
        return {"providers": records, "selection": self.status()}

    def voice_status(self) -> dict[str, object]:
        voice = self._voice()
        if voice is None:
            return {"framework_ready": False, "status": "unavailable"}
        health = voice.health()
        return {
            "framework_ready": voice.initialized,
            "enabled": voice.enabled,
            "input_enabled": voice.input_enabled,
            "output_enabled": voice.output_enabled,
            "mode": voice.mode.value,
            "privacy_mode": voice.privacy_mode,
            "input_backend": voice.selected_input_backend,
            "output_backend": voice.selected_output_backend,
            "language": voice.language,
            "rate": voice.rate,
            "volume": voice.volume,
            "microphone_available": bool(voice.devices("input")),
            "tts_status": health.get("windows-sapi", {}).get("status", "unknown"),
            "stt_status": health.get("offline-stt", {}).get("status", "unknown"),
            "raw_audio_persistence": voice.raw_audio_persistence,
        }

    def speak(self, payload: dict[str, object]) -> dict[str, object]:
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError("valid_speech_text_required")
        voice = self._voice()
        if voice is None:
            raise ValueError("voice_unavailable")
        if not voice.output_enabled:
            raise ValueError("voice_output_disabled")
        request_id = str(uuid4())
        self._record("voice_synthesis_started", "processing", request_id, "Voice synthesis started")
        result = voice.say(text.strip(), parent_request_id=request_id, playback=True)
        self._record("voice_synthesis_completed", result.status.value, request_id, "Voice synthesis completed")
        self.logger.info("interface_voice_requested interface_request_id=%s status=%s", request_id, result.status.value)
        return {"status": result.status.value, "synthesis_id": result.synthesis_id, "backend_id": result.backend_id, "audio_available": bool(result.audio_reference)}

    def stop_voice(self, payload: dict[str, object]) -> dict[str, object]:
        del payload
        voice = self._voice()
        stopped = bool(voice and voice.interrupt())
        self.logger.info("interface_voice_stopped status=%s", "cancelled" if stopped else "unavailable")
        return {"status": "cancelled" if stopped else "unavailable", "stopped": stopped}

    def request_shutdown(self, payload: dict[str, object]) -> dict[str, object]:
        """Schedule a graceful stop after the authenticated response is sent."""
        del payload
        request_id = str(uuid4())
        self._record("interface_shutdown_requested", "accepted", request_id, "Interface shutdown requested")

        def delayed_stop() -> None:
            time.sleep(0.2)
            self.stop()

        threading.Thread(target=delayed_stop, name="jarvis-interface-shutdown", daemon=True).start()
        return {"status": "accepted", "request_id": request_id}

    def tools(self) -> list[dict[str, object]]:
        manager = self._tools_manager()
        if manager is None:
            return []
        return [
            {
                "tool_id": item.tool_id,
                "name": item.name,
                "description": item.description,
                "capabilities": item.capabilities,
                "operations": item.capabilities,
                "risk_class": item.risk_class.value,
                "permissions": item.permissions,
                "enabled": item.enabled,
                "available": item.available,
                "health": "healthy" if item.healthy and item.available else "unavailable",
                "dry_run": True,
            }
            for item in manager.list_tools()
        ]

    def tool(self, tool_id: str) -> dict[str, object]:
        return next((item for item in self.tools() if item["tool_id"] == tool_id), {"status": "unavailable", "error": "tool_not_found"})

    def plans(self) -> list[dict[str, object]]:
        planning = self._planning()
        if planning is None:
            return []
        return [self._plan_summary(item) for item in sorted(planning.plans.values(), key=lambda record: record.updated_at, reverse=True)[:50]]

    def plan(self, plan_id: str) -> dict[str, object]:
        planning = self._planning()
        record = planning.plans.get(plan_id) if planning is not None else None
        return json_safe(record) if record is not None else {"status": "unavailable", "error": "plan_not_found"}

    def _plan_summary(self, record: object) -> dict[str, object]:
        return {
            "plan_id": record.plan_id,
            "title": record.title,
            "status": record.status.value,
            "version": record.version,
            "risk": record.risk_summary,
            "steps": len(record.steps),
            "validation": record.validation.valid if record.validation else False,
            "approvals": record.required_approvals,
            "updated_at": record.updated_at,
        }

    def coordinations(self) -> list[dict[str, object]]:
        orchestrator = self._orchestrator()
        if orchestrator is None:
            return []
        return [
            {
                "coordination_id": item.coordination_id,
                "parent_request_id": item.parent_request_id,
                "objective": item.objective,
                "status": item.status.value,
                "mode": item.mode.value,
                "agents": item.plan.participating_agents,
                "subtasks": [{"subtask_id": task.subtask_id, "agent_id": task.assigned_agent_id, "status": task.status.value} for task in item.plan.subtasks],
                "conflicts": len(item.conflicts),
                "warnings": item.warnings,
                "created_at": item.created_at,
            }
            for item in orchestrator.store.list()[:50]
        ]

    def coordination(self, coordination_id: str) -> dict[str, object]:
        orchestrator = self._orchestrator()
        record = orchestrator.store.get(coordination_id) if orchestrator is not None else None
        return json_safe(record) if record is not None else {"status": "unavailable", "error": "coordination_not_found"}

    def approvals(self) -> list[dict[str, object]]:
        pending: list[dict[str, object]] = []
        planning = self._planning()
        if planning is not None:
            for plan in planning.plans.values():
                if plan.status.value in {"awaiting_review", "awaiting_approval"}:
                    pending.append({
                        "approval_id": plan.plan_id,
                        "requesting_system": "autonomous_planning",
                        "action": "Approve plan for authoritative handoff",
                        "target": plan.title,
                        "side_effects": "Approval permits handoff; it does not execute the plan.",
                        "risk_class": plan.risk_summary,
                        "permission": ", ".join(plan.required_permissions),
                        "request_id": plan.parent_request_id,
                        "plan_id": plan.plan_id,
                        "status": plan.status.value,
                        "expires_at": None,
                    })
        return pending[:50]

    def decide_approval(self, payload: dict[str, object]) -> dict[str, object]:
        approval_id = payload.get("approval_id")
        decision = payload.get("decision")
        if not isinstance(approval_id, str) or decision not in {"approve", "reject"}:
            raise ValueError("valid_approval_decision_required")
        if not any(item["approval_id"] == approval_id for item in self.approvals()):
            raise ValueError("stale_or_missing_approval")
        manager = self.startup.conversation_manager
        if manager is None:
            raise ValueError("command_engine_unavailable")
        command = f"plan {'approve' if decision == 'approve' else 'reject'} {approval_id}"
        with self._conversation_lock:
            result = manager.handle_input(command, request_id=str(uuid4()))
        self.logger.info("interface_approval_submitted approval_id=%s status=%s", approval_id, decision)
        return {"status": "completed", "approval_id": approval_id, "decision": decision, "content": result.response}

    def activity(self) -> list[dict[str, object]]:
        with self._activity_lock:
            return [json_safe(item) for item in tuple(self._activity)]

    def safe_logs(self, query: dict[str, list[str]]) -> list[dict[str, object]]:
        settings = self.startup.settings
        if settings is None:
            return []
        path = settings.logs_dir / settings.logging.log_file
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-self.config.max_log_entries * 4:]
        except OSError:
            return []
        level_filter = (query.get("level") or [""])[0].upper()
        subsystem_filter = (query.get("subsystem") or [""])[0].lower()
        request_filter = (query.get("request_id") or [""])[0]
        entries: list[dict[str, object]] = []
        for line in reversed(lines):
            safe = redact_text(line, 1000)
            if level_filter and f"| {level_filter} |" not in safe:
                continue
            if subsystem_filter and subsystem_filter not in safe.lower():
                continue
            if request_filter and request_filter not in safe:
                continue
            parts = [part.strip() for part in safe.split("|", 3)]
            entries.append({
                "timestamp": parts[0] if parts else "",
                "level": parts[1] if len(parts) > 1 else "INFO",
                "subsystem": parts[2] if len(parts) > 2 else "jarvis",
                "message": parts[3] if len(parts) > 3 else safe,
            })
            if len(entries) >= self.config.max_log_entries:
                break
        return entries

    def settings(self) -> dict[str, object]:
        session = self.startup.conversation_manager.active_session if self.startup.conversation_manager else None
        metadata = dict(session.metadata) if session else {}
        voice = self.voice_status()
        tools = self._tools_manager()
        orchestrator = self._orchestrator()
        planning = self._planning()
        return {
            "interface": {**self._preferences, "port": self._server.server_address[1] if self._server else self.config.port},
            "provider": {
                "execution_policy": metadata.get("execution_policy", "automatic"),
                "provider_preference": metadata.get("provider_preference"),
                "model_preference": metadata.get("model_preference"),
                "local_only": bool(metadata.get("local_only", False)),
            },
            "voice": voice,
            "tool": {"mode": tools.mode.value if tools else "unavailable", "limits": json_safe(tools.limits) if tools else {}},
            "multiagent": {"mode": orchestrator.mode.value if orchestrator else "unavailable", "limits": json_safe(orchestrator.limits) if orchestrator else {}},
            "planning": {"mode": planning.mode.value if planning else "unavailable", "limits": json_safe(planning.limits) if planning else {}},
        }

    def update_settings(self, payload: dict[str, object]) -> dict[str, object]:
        section = payload.get("section")
        key = payload.get("key")
        value = payload.get("value")
        if not isinstance(section, str) or not isinstance(key, str):
            raise ValueError("setting_section_and_key_required")
        manager = self.startup.conversation_manager
        if section == "interface":
            allowed: dict[str, set[object] | None] = {
                "theme": {"system", "dark", "light"},
                "density": {"comfortable", "compact"},
                "auto_scroll": {True, False},
                "notifications": {True, False},
                "last_view": {"chat", "activity", "plans", "tools", "multiagent", "voice", "health", "logs", "settings"},
            }
            if key not in allowed or value not in allowed[key]:
                raise ValueError("unsupported_interface_setting")
            self._preferences[key] = value
        elif manager is None:
            raise ValueError("command_engine_unavailable")
        else:
            command = self._setting_command(section, key, value)
            if command is not None:
                with self._conversation_lock:
                    result = manager.handle_input(command, request_id=str(uuid4()))
                if result.warnings:
                    raise ValueError("setting_update_failed")
            elif section == "provider":
                self._update_provider_setting(manager.active_session, key, value)
            else:
                raise ValueError("unsupported_setting")
        self.logger.info("interface_setting_changed section=%s key=%s", section, key)
        return {"status": "completed", "settings": self.settings()}

    def _setting_command(self, section: str, key: str, value: object) -> str | None:
        if section == "provider" and key == "execution_policy" and value in {"local_only", "cloud_only", "automatic", "prefer_local", "prefer_cloud"}:
            if value == "local_only":
                return "local only on"
            if value == "cloud_only":
                return "cloud only on"
            return None
        if section == "voice" and key == "output_enabled" and isinstance(value, bool):
            return f"voice output {'on' if value else 'off'}"
        if section == "voice" and key == "privacy_mode" and value in {"strict", "standard", "diagnostic"}:
            return f"voice privacy {value}"
        if section == "voice" and key == "rate" and isinstance(value, int) and -10 <= value <= 10:
            return f"voice rate {value}"
        if section == "voice" and key == "volume" and isinstance(value, int) and 0 <= value <= 100:
            return f"voice volume {value}"
        if section == "voice" and key == "language" and isinstance(value, str) and re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", value):
            return f"voice language {value}"
        if section == "voice" and key == "raw_audio_persistence" and isinstance(value, bool):
            return f"voice raw-audio {'on' if value else 'off'}"
        if section == "tool" and key == "mode" and value in {"off", "confirm", "automatic-safe", "automatic"}:
            return f"tool mode {value}"
        if section == "multiagent" and key == "mode" and value in {"off", "confirm", "automatic-safe", "automatic"}:
            return f"multiagent mode {value}"
        if section == "planning" and key == "mode" and value in {"off", "suggest", "confirm", "automatic-safe"}:
            return f"plan mode {value}"
        return None

    def _update_provider_setting(self, session: Any, key: str, value: object) -> None:
        if key == "execution_policy" and value in {"automatic", "prefer_local", "prefer_cloud"}:
            session.metadata.update({
                "execution_policy": value,
                "local_only": False,
                "cloud_only": False,
            })
            return
        if key in {"provider_preference", "model_preference"}:
            if value in {None, ""}:
                session.metadata.pop(key, None)
                return
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}", value):
                raise ValueError("invalid_provider_preference")
            session.metadata[key] = value
            return
        raise ValueError("unsupported_provider_setting")

    def _voice(self) -> Any | None:
        return self.startup.jarvis_core.manager.voice_intelligence if self.startup.jarvis_core is not None else None

    def _tools_manager(self) -> Any | None:
        return self.startup.jarvis_core.manager.tools if self.startup.jarvis_core is not None else None

    def _planning(self) -> Any | None:
        return self.startup.jarvis_core.manager.autonomous_planning if self.startup.jarvis_core is not None else None

    def _orchestrator(self) -> Any | None:
        return self.startup.agent_manager.orchestrator if self.startup.agent_manager is not None else None


def run_local_interface(*, port: int | None = None, open_browser: bool = True) -> int:
    """Start JARVIS and block on the localhost interface until interrupted."""
    startup = StartupManager()
    service: LocalInterfaceService | None = None
    try:
        startup.start()
        if startup.settings is None:
            raise RuntimeError("settings_unavailable")
        config = startup.settings.interface
        if port is not None:
            config = replace(config, port=port, allowed_origins=(f"http://127.0.0.1:{port}", f"http://localhost:{port}"))
        service = LocalInterfaceService(startup, config)
        print(f"JARVIS local interface: http://127.0.0.1:{config.port}")
        print("Press Ctrl+C to stop.")
        service.start(open_browser=open_browser)
        return 0
    except KeyboardInterrupt:
        print("\nStopping JARVIS local interface.")
        return 0
    except OSError as exc:
        LOGGER.error("interface_start_failed failure_reason=%s", type(exc).__name__)
        print("JARVIS interface could not start. The configured local port may already be in use.")
        return 1
    except Exception:
        LOGGER.exception("interface_start_failed")
        print("JARVIS interface could not start. Check the local logs for details.")
        return 1
    finally:
        if service is not None:
            service.stop()
        startup.shutdown()
