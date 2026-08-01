"""Governed read-only web automation foundation."""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import socket
import ssl
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


def _now() -> str:
    return datetime.now(UTC).isoformat()


class WebAutomationStatus(StrEnum):
    DISABLED = "disabled"
    READY = "ready"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
    INVALID_INPUT = "invalid_input"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    APPROVAL_REQUIRED = "approval_required"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CLOSED = "closed"


class WebAutomationMode(StrEnum):
    OFF = "off"
    READ_ONLY = "read_only"
    CONFIRM = "confirm"


class WebActionType(StrEnum):
    STATUS = "status"
    OPEN_URL = "open_url"
    GET_PAGE_TITLE = "get_page_title"
    GET_CURRENT_URL = "get_current_url"
    SNAPSHOT_PAGE = "snapshot_page"
    SUMMARIZE_PAGE_METADATA = "summarize_page_metadata"
    CLOSE_SESSION = "close_session"
    CLICK = "click"
    TYPE_TEXT = "type_text"
    SUBMIT_FORM = "submit_form"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    LOGIN = "login"
    PURCHASE = "purchase"
    SEND_MESSAGE = "send_message"
    DELETE = "delete"
    ACCOUNT_CHANGE = "account_change"


class WebRiskLevel(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class WebPermission(StrEnum):
    STATUS_READ = "web_status_read"
    SESSION_CREATE = "web_session_create"
    URL_OPEN = "web_url_open"
    PAGE_READ = "web_page_read"
    SNAPSHOT = "web_snapshot"
    CLICK = "web_click"
    TYPE = "web_type"
    FORM_SUBMIT = "web_form_submit"
    DOWNLOAD = "web_download"
    UPLOAD = "web_upload"
    LOGIN = "web_login"
    MESSAGE_SEND = "web_message_send"
    PURCHASE = "web_purchase"
    DELETE = "web_delete"
    ACCOUNT_CHANGE = "web_account_change"
    AUDIT_READ = "web_audit_read"


READ_ONLY_ACTIONS = frozenset({
    WebActionType.STATUS,
    WebActionType.OPEN_URL,
    WebActionType.GET_PAGE_TITLE,
    WebActionType.GET_CURRENT_URL,
    WebActionType.SNAPSHOT_PAGE,
    WebActionType.SUMMARIZE_PAGE_METADATA,
    WebActionType.CLOSE_SESSION,
})
SENSITIVE_ACTIONS = frozenset(set(WebActionType) - set(READ_ONLY_ACTIONS))
_BLOCKED_TOPICS = re.compile(r"(?i)(adult|porn|casino|gambl|illegal[-_ ]?drug|weapon|malware|phishing|captcha[-_ ]?bypass|paywall[-_ ]?bypass|credential[-_ ]?harvest)")
_TOKEN_QUERY = re.compile(r"(?i)(token|key|secret|password|auth|session|cookie|code)")
_LONG_SECRET = re.compile(r"\b[A-Za-z0-9_-]{32,}\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_LOCAL_PATH = re.compile(r"(?i)(?:[A-Z]:\\|/(?:home|users|var|etc)/)[^\s]+")
_TEXT_CONTENT_TYPES = frozenset({"text/html", "text/plain", "application/xhtml+xml"})


class _WebInspectionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _SafeHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.description: str | None = None
        self._in_title = False
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript", "template", "svg"}:
            self._ignored_depth += 1
        if lowered == "title":
            self._in_title = True
        if lowered == "meta" and self.description is None:
            values = {str(key).lower(): value or "" for key, value in attrs}
            if values.get("name", "").lower() == "description":
                self.description = values.get("content", "")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = False
        if lowered in {"script", "style", "noscript", "template", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
        self.text_parts.append(data)


@dataclass(frozen=True, slots=True)
class WebSession:
    session_id: str
    adapter_id: str
    status: str
    created_at: str
    current_domain: str | None = None


@dataclass(frozen=True, slots=True)
class WebActionRequest:
    request_id: str
    action_type: WebActionType
    url: str | None = None
    session_id: str | None = None
    permissions: tuple[WebPermission, ...] = ()
    approval_reference: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WebPageSnapshot:
    session_id: str
    domain: str | None
    title: str | None
    current_url: str | None
    captured_at: str
    content_stored: bool = False
    screenshot_stored: bool = False
    status_code: int | None = None
    content_type: str | None = None
    byte_count: int = 0
    redirect_count: int = 0
    redirect_domains: tuple[str, ...] = ()
    description: str | None = None
    text_preview: str | None = None


@dataclass(frozen=True, slots=True)
class WebActionResult:
    request_id: str
    action_type: WebActionType
    status: WebAutomationStatus
    message: str
    session_id: str | None = None
    safe_domain: str | None = None
    title: str | None = None
    current_url: str | None = None
    snapshot: WebPageSnapshot | None = None
    error_code: str | None = None
    approval_required: bool = False


@dataclass(frozen=True, slots=True)
class WebAuditEvent:
    event_id: str
    request_id: str
    action_type: str
    risk_level: str
    status: str
    timestamp: str
    safe_domain: str | None
    policy_decision: str
    confirmation_required: bool
    result_summary: str
    final_domain: str | None = None
    redirect_count: int = 0
    content_type: str | None = None
    byte_count: int = 0
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class WebPolicyDecision:
    allowed: bool
    status: WebAutomationStatus
    reason: str
    risk_level: WebRiskLevel
    safe_domain: str | None = None
    normalized_url: str | None = None
    permission: WebPermission | None = None
    approval_required: bool = False
    error_code: str | None = None


class WebAutomationAdapter(Protocol):
    adapter_id: str
    available: bool
    capabilities: tuple[WebActionType, ...]

    def open_url(self, url: str, request_id: str) -> WebActionResult: ...
    def get_page_title(self, session_id: str, request_id: str) -> WebActionResult: ...
    def get_current_url(self, session_id: str, request_id: str) -> WebActionResult: ...
    def snapshot_page(self, session_id: str, request_id: str) -> WebActionResult: ...
    def close_session(self, session_id: str, request_id: str) -> WebActionResult: ...


class _ValidatedRedirectHandler(HTTPRedirectHandler):
    def __init__(self, validate_url: Callable[[str], WebPolicyDecision], maximum_redirects: int) -> None:
        super().__init__()
        self.validate_url = validate_url
        self.maximum_redirects = maximum_redirects
        self.redirects: list[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if len(self.redirects) >= self.maximum_redirects:
            raise _WebInspectionError("WEB_TOO_MANY_REDIRECTS", "The page exceeded the redirect limit.")
        decision = self.validate_url(newurl)
        if not decision.allowed:
            raise _WebInspectionError("WEB_REDIRECT_BLOCKED", "A redirect target was blocked by web safety policy.")
        self.redirects.append(decision.normalized_url or newurl)
        return super().redirect_request(req, fp, code, msg, headers, decision.normalized_url or newurl)


class ReadOnlyWebInspectionAdapter:
    """Bounded public HTTP(S) inspection without a browser profile or interaction."""

    adapter_id = "read-only-http"
    available = True
    capabilities = (
        WebActionType.OPEN_URL,
        WebActionType.GET_PAGE_TITLE,
        WebActionType.GET_CURRENT_URL,
        WebActionType.SNAPSHOT_PAGE,
        WebActionType.SUMMARIZE_PAGE_METADATA,
        WebActionType.CLOSE_SESSION,
    )

    def __init__(
        self,
        validate_url: Callable[[str], WebPolicyDecision],
        timeout_seconds: float = 8.0,
        maximum_redirects: int = 5,
        maximum_response_bytes: int = 524_288,
        maximum_preview_characters: int = 2_000,
        maximum_title_characters: int = 200,
    ) -> None:
        self.validate_url = validate_url
        self.timeout_seconds = min(8.0, max(0.1, float(timeout_seconds)))
        self.maximum_redirects = min(5, max(0, int(maximum_redirects)))
        self.maximum_response_bytes = min(524_288, max(1_024, int(maximum_response_bytes)))
        self.maximum_preview_characters = min(2_000, max(100, int(maximum_preview_characters)))
        self.maximum_title_characters = min(200, max(20, int(maximum_title_characters)))
        self.pages: dict[str, WebPageSnapshot] = {}

    def open_url(self, url: str, request_id: str) -> WebActionResult:
        initial_decision = self.validate_url(url)
        if not initial_decision.allowed:
            return self._failure(request_id, initial_decision.error_code or "WEB_URL_INVALID", initial_decision.reason, initial_decision.status)
        url = initial_decision.normalized_url or url
        redirect_handler = _ValidatedRedirectHandler(self.validate_url, self.maximum_redirects)
        opener = build_opener(redirect_handler)
        request = Request(
            url,
            headers={"User-Agent": "JARVIS-OS-ReadOnly/0.6", "Accept": "text/html,text/plain,application/xhtml+xml"},
            method="GET",
        )
        try:
            with opener.open(request, timeout=self.timeout_seconds) as response:
                final_decision = self.validate_url(response.geturl())
                if not final_decision.allowed:
                    raise _WebInspectionError("WEB_REDIRECT_BLOCKED", "The final response URL was blocked by web safety policy.")
                content_type = response.headers.get_content_type().lower()
                if content_type not in _TEXT_CONTENT_TYPES:
                    raise _WebInspectionError("WEB_UNSUPPORTED_CONTENT_TYPE", "The response is not a supported text page.")
                if response.headers.get("Content-Encoding", "identity").lower() not in {"", "identity"}:
                    raise _WebInspectionError("WEB_UNSUPPORTED_CONTENT_TYPE", "Compressed responses are not inspected by this bounded adapter.")
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > self.maximum_response_bytes:
                    raise _WebInspectionError("WEB_RESPONSE_TOO_LARGE", "The response exceeds the configured size limit.")
                body = response.read(self.maximum_response_bytes + 1)
                if len(body) > self.maximum_response_bytes:
                    raise _WebInspectionError("WEB_RESPONSE_TOO_LARGE", "The response exceeds the configured size limit.")
                charset = response.headers.get_content_charset() or "utf-8"
                try:
                    decoded = body.decode(charset, errors="replace")
                except LookupError:
                    decoded = body.decode("utf-8", errors="replace")
                title, description, preview = self._extract(decoded, content_type)
                session_id = str(uuid.uuid4())
                final_url = final_decision.normalized_url or response.geturl()
                redirect_domains = tuple(
                    item.safe_domain or "unknown"
                    for item in (self.validate_url(redirect_url) for redirect_url in redirect_handler.redirects)
                )
                snapshot = WebPageSnapshot(
                    session_id=session_id,
                    domain=final_decision.safe_domain,
                    title=title,
                    current_url=final_url,
                    captured_at=_now(),
                    status_code=int(getattr(response, "status", 200)),
                    content_type=content_type,
                    byte_count=len(body),
                    redirect_count=len(redirect_handler.redirects),
                    redirect_domains=redirect_domains,
                    description=description,
                    text_preview=preview,
                )
                self.pages[session_id] = snapshot
                return WebActionResult(
                    request_id, WebActionType.OPEN_URL, WebAutomationStatus.COMPLETED,
                    "Public page inspected read-only.", session_id, final_decision.safe_domain,
                    title=title, current_url=final_url, snapshot=snapshot,
                )
        except _WebInspectionError as exc:
            return self._failure(request_id, exc.code, str(exc))
        except HTTPError as exc:
            return self._failure(request_id, "WEB_HTTP_ERROR", f"The page returned HTTP status {exc.code}.")
        except (TimeoutError, socket.timeout):
            return self._failure(request_id, "WEB_TIMEOUT", "The bounded page inspection timed out.", WebAutomationStatus.TIMED_OUT)
        except ssl.SSLError:
            return self._failure(request_id, "WEB_TLS_ERROR", "TLS validation failed for the page.")
        except socket.gaierror:
            return self._failure(request_id, "WEB_DNS_ERROR", "The page hostname could not be resolved.")
        except URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, socket.gaierror):
                return self._failure(request_id, "WEB_DNS_ERROR", "The page hostname could not be resolved.")
            if isinstance(reason, ssl.SSLError):
                return self._failure(request_id, "WEB_TLS_ERROR", "TLS validation failed for the page.")
            if isinstance(reason, (TimeoutError, socket.timeout)):
                return self._failure(request_id, "WEB_TIMEOUT", "The bounded page inspection timed out.", WebAutomationStatus.TIMED_OUT)
            return self._failure(request_id, "WEB_HTTP_ERROR", "The page could not be fetched safely.")
        except (ValueError, UnicodeError):
            return self._failure(request_id, "WEB_PARSE_ERROR", "The page response could not be parsed safely.")

    def get_page_title(self, session_id: str, request_id: str) -> WebActionResult:
        snapshot = self.pages.get(session_id)
        if snapshot is None:
            return self._missing(request_id, WebActionType.GET_PAGE_TITLE, session_id)
        return WebActionResult(request_id, WebActionType.GET_PAGE_TITLE, WebAutomationStatus.COMPLETED, "Page title read.", session_id, snapshot.domain, title=snapshot.title)

    def get_current_url(self, session_id: str, request_id: str) -> WebActionResult:
        snapshot = self.pages.get(session_id)
        if snapshot is None:
            return self._missing(request_id, WebActionType.GET_CURRENT_URL, session_id)
        return WebActionResult(request_id, WebActionType.GET_CURRENT_URL, WebAutomationStatus.COMPLETED, "Current page URL read.", session_id, snapshot.domain, current_url=snapshot.current_url)

    def snapshot_page(self, session_id: str, request_id: str) -> WebActionResult:
        snapshot = self.pages.get(session_id)
        if snapshot is None:
            return self._missing(request_id, WebActionType.SNAPSHOT_PAGE, session_id)
        return WebActionResult(request_id, WebActionType.SNAPSHOT_PAGE, WebAutomationStatus.COMPLETED, "Bounded page snapshot read.", session_id, snapshot.domain, title=snapshot.title, current_url=snapshot.current_url, snapshot=snapshot)

    def close_session(self, session_id: str, request_id: str) -> WebActionResult:
        snapshot = self.pages.pop(session_id, None)
        if snapshot is None:
            return self._missing(request_id, WebActionType.CLOSE_SESSION, session_id)
        return WebActionResult(request_id, WebActionType.CLOSE_SESSION, WebAutomationStatus.CLOSED, "Web inspection session closed.", session_id, snapshot.domain)

    def _extract(self, content: str, content_type: str) -> tuple[str | None, str | None, str]:
        if content_type == "text/plain":
            title = None
            description = None
            text = content
        else:
            parser = _SafeHTMLParser()
            try:
                parser.feed(content)
                parser.close()
            except Exception as exc:
                raise _WebInspectionError("WEB_PARSE_ERROR", "The page HTML could not be parsed safely.") from exc
            title = self._sanitize(" ".join(parser.title_parts), self.maximum_title_characters) or None
            description = self._sanitize(parser.description or "", 500) or None
            text = " ".join(parser.text_parts)
        return title, description, self._sanitize(text, self.maximum_preview_characters)

    @staticmethod
    def _sanitize(value: str, limit: int) -> str:
        cleaned = " ".join(value.replace("\x00", " ").split())
        cleaned = _EMAIL.sub("[redacted-email]", cleaned)
        cleaned = _LOCAL_PATH.sub("[redacted-path]", cleaned)
        cleaned = _LONG_SECRET.sub("[redacted-value]", cleaned)
        return cleaned[:limit]

    @staticmethod
    def _failure(request_id: str, code: str, message: str, status: WebAutomationStatus = WebAutomationStatus.FAILED) -> WebActionResult:
        return WebActionResult(request_id, WebActionType.OPEN_URL, status, message, error_code=code)

    @staticmethod
    def _missing(request_id: str, action: WebActionType, session_id: str) -> WebActionResult:
        return WebActionResult(request_id, action, WebAutomationStatus.INVALID_INPUT, "No active inspected page exists.", session_id, error_code="WEB_NO_ACTIVE_PAGE")


class UnavailableBrowserAdapter:
    """Truthful placeholder; it never opens an external browser."""

    adapter_id = "unavailable-browser"
    available = False
    capabilities: tuple[WebActionType, ...] = ()

    @staticmethod
    def _result(action: WebActionType, request_id: str, session_id: str | None = None) -> WebActionResult:
        return WebActionResult(request_id, action, WebAutomationStatus.UNAVAILABLE, "No governed local browser adapter is configured.", session_id, error_code="adapter_unavailable")

    def open_url(self, url: str, request_id: str) -> WebActionResult: return self._result(WebActionType.OPEN_URL, request_id)
    def get_page_title(self, session_id: str, request_id: str) -> WebActionResult: return self._result(WebActionType.GET_PAGE_TITLE, request_id, session_id)
    def get_current_url(self, session_id: str, request_id: str) -> WebActionResult: return self._result(WebActionType.GET_CURRENT_URL, request_id, session_id)
    def snapshot_page(self, session_id: str, request_id: str) -> WebActionResult: return self._result(WebActionType.SNAPSHOT_PAGE, request_id, session_id)
    def close_session(self, session_id: str, request_id: str) -> WebActionResult: return self._result(WebActionType.CLOSE_SESSION, request_id, session_id)


class LocalBrowserAdapter(UnavailableBrowserAdapter):
    """Extension point for a future configured local read-only browser runtime."""

    adapter_id = "local-browser-placeholder"


class WebAutomationManager:
    """Validate and coordinate bounded web actions without autonomous authority."""

    def __init__(self, storage_dir: Path, settings: object | None = None, adapter: WebAutomationAdapter | None = None, logger: logging.Logger | None = None) -> None:
        config = getattr(settings, "web_automation", None)
        self.enabled = bool(getattr(config, "enabled", True))
        configured_mode = getattr(config, "mode", "read_only")
        self.mode = WebAutomationMode.OFF if isinstance(configured_mode, bool) else WebAutomationMode(str(configured_mode))
        self.allow_local_targets = bool(getattr(config, "allow_local_targets", False))
        self.allow_http = bool(getattr(config, "allow_http", False))
        self.audit_retention = max(1, int(getattr(config, "audit_retention", 100)))
        self.action_timeout_seconds = min(8.0, max(0.1, float(getattr(config, "action_timeout_seconds", 8))))
        self.maximum_redirects = min(5, max(0, int(getattr(config, "maximum_redirects", 5))))
        self.maximum_response_bytes = min(524_288, max(1_024, int(getattr(config, "maximum_response_bytes", 524_288))))
        self.maximum_preview_characters = min(2_000, max(100, int(getattr(config, "maximum_preview_characters", 2_000))))
        self.storage_dir = Path(storage_dir)
        self.audit_path = self.storage_dir / "audit.json"
        configured_adapter = str(getattr(config, "adapter", "read-only-http"))
        self.adapter = adapter or (
            ReadOnlyWebInspectionAdapter(
                self._validate_fetch_url,
                self.action_timeout_seconds,
                self.maximum_redirects,
                self.maximum_response_bytes,
                self.maximum_preview_characters,
            )
            if configured_adapter == "read-only-http"
            else UnavailableBrowserAdapter()
        )
        self.logger = logger or logging.getLogger("web_automation")
        self.sessions: dict[str, WebSession] = {}
        self._audit_events = self._load_audit()
        self.initialized = True

    def status(self) -> dict[str, Any]:
        return {
            "initialized": self.initialized,
            "enabled": self.enabled,
            "mode": self.mode.value,
            "adapter_id": self.adapter.adapter_id,
            "adapter_available": self.adapter.available,
            "read_only": True,
            "network_inspection_enabled": self.enabled and self.adapter.available,
            "interactive_actions": "blocked",
            "maximum_redirects": self.maximum_redirects,
            "maximum_response_bytes": self.maximum_response_bytes,
            "maximum_preview_characters": self.maximum_preview_characters,
            "active_sessions": len(self.sessions),
            "audit_events": len(self._audit_events),
            "page_content_persistence": False,
            "screenshot_persistence": False,
            "sensitive_actions": "blocked",
        }

    def policy(self, action: WebActionType, url: str | None = None, permissions: tuple[WebPermission, ...] = ()) -> WebPolicyDecision:
        if action in SENSITIVE_ACTIONS:
            permission = self._permission_for(action)
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Sensitive web actions are blocked by the current foundation.", WebRiskLevel.HIGH, permission=permission, approval_required=True)
        permission = self._permission_for(action)
        if permissions and permission not in permissions:
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Required web permission is missing.", WebRiskLevel.LOW, permission=permission)
        if action is WebActionType.OPEN_URL:
            return self._validate_url(url or "", permission)
        return WebPolicyDecision(True, WebAutomationStatus.READY, "Read-only action is permitted by policy.", WebRiskLevel.MINIMAL, permission=permission)

    def execute(self, request: WebActionRequest) -> WebActionResult:
        decision = self.policy(request.action_type, request.url, request.permissions)
        if not decision.allowed:
            result = WebActionResult(request.request_id, request.action_type, decision.status, decision.reason, request.session_id, decision.safe_domain, error_code=decision.error_code or "WEB_ACTION_BLOCKED", approval_required=decision.approval_required)
            self._audit(request, result, decision)
            return result
        if not self.enabled or self.mode is WebAutomationMode.OFF:
            result = WebActionResult(request.request_id, request.action_type, WebAutomationStatus.DISABLED, "Web Automation is disabled. Read-only policy remains available.", request.session_id, decision.safe_domain, error_code="web_disabled")
            self._audit(request, result, decision)
            return result
        if not self.adapter.available:
            result = WebActionResult(request.request_id, request.action_type, WebAutomationStatus.UNAVAILABLE, "No governed read-only web adapter is configured.", request.session_id, decision.safe_domain, error_code="WEB_ADAPTER_UNAVAILABLE")
            self._audit(request, result, decision)
            return result
        result = self._dispatch(request, decision)
        self._audit(request, result, decision)
        return result

    def open_url(self, url: str, request_id: str | None = None) -> WebActionResult:
        return self.execute(WebActionRequest(request_id or str(uuid.uuid4()), WebActionType.OPEN_URL, url=url, permissions=(WebPermission.URL_OPEN, WebPermission.SESSION_CREATE)))

    def title(self, session_id: str | None = None, request_id: str | None = None) -> WebActionResult:
        return self.execute(WebActionRequest(request_id or str(uuid.uuid4()), WebActionType.GET_PAGE_TITLE, session_id=session_id or self._latest_session_id(), permissions=(WebPermission.PAGE_READ,)))

    def current_url(self, session_id: str | None = None, request_id: str | None = None) -> WebActionResult:
        return self.execute(WebActionRequest(request_id or str(uuid.uuid4()), WebActionType.GET_CURRENT_URL, session_id=session_id or self._latest_session_id(), permissions=(WebPermission.PAGE_READ,)))

    def snapshot(self, session_id: str | None = None, request_id: str | None = None) -> WebActionResult:
        return self.execute(WebActionRequest(request_id or str(uuid.uuid4()), WebActionType.SNAPSHOT_PAGE, session_id=session_id or self._latest_session_id(), permissions=(WebPermission.SNAPSHOT,)))

    def close(self, session_id: str | None = None, request_id: str | None = None) -> WebActionResult:
        return self.execute(WebActionRequest(request_id or str(uuid.uuid4()), WebActionType.CLOSE_SESSION, session_id=session_id or self._latest_session_id(), permissions=(WebPermission.SESSION_CREATE,)))

    def audit_events(self) -> tuple[WebAuditEvent, ...]:
        return tuple(self._audit_events)

    def _dispatch(self, request: WebActionRequest, decision: WebPolicyDecision) -> WebActionResult:
        if request.action_type is not WebActionType.OPEN_URL and not request.session_id:
            return WebActionResult(request.request_id, request.action_type, WebAutomationStatus.INVALID_INPUT, "No active web session exists.", error_code="WEB_NO_ACTIVE_PAGE")
        if request.action_type not in self.adapter.capabilities:
            return WebActionResult(request.request_id, request.action_type, WebAutomationStatus.UNAVAILABLE, "The configured adapter does not support this read-only action.", request.session_id, decision.safe_domain, error_code="WEB_ADAPTER_UNAVAILABLE")
        try:
            if request.action_type is WebActionType.OPEN_URL:
                result = self.adapter.open_url(decision.normalized_url or "", request.request_id)
            elif request.action_type is WebActionType.GET_PAGE_TITLE:
                result = self.adapter.get_page_title(request.session_id or "", request.request_id)
            elif request.action_type is WebActionType.GET_CURRENT_URL:
                result = self.adapter.get_current_url(request.session_id or "", request.request_id)
            elif request.action_type in {WebActionType.SNAPSHOT_PAGE, WebActionType.SUMMARIZE_PAGE_METADATA}:
                result = self.adapter.snapshot_page(request.session_id or "", request.request_id)
            elif request.action_type is WebActionType.CLOSE_SESSION:
                result = self.adapter.close_session(request.session_id or "", request.request_id)
            else:
                return WebActionResult(request.request_id, request.action_type, WebAutomationStatus.BLOCKED_BY_POLICY, "Sensitive web actions are blocked.", request.session_id, error_code="policy_blocked", approval_required=True)
        except TimeoutError:
            return WebActionResult(request.request_id, request.action_type, WebAutomationStatus.TIMED_OUT, "The bounded web inspection timed out.", request.session_id, decision.safe_domain, error_code="WEB_TIMEOUT")
        except Exception:
            return WebActionResult(request.request_id, request.action_type, WebAutomationStatus.FAILED, "The web inspection adapter failed safely.", request.session_id, decision.safe_domain, error_code="WEB_ADAPTER_FAILURE")
        if result.status in {WebAutomationStatus.COMPLETED, WebAutomationStatus.CLOSED} and result.session_id:
            if request.action_type is WebActionType.CLOSE_SESSION:
                self.sessions.pop(result.session_id, None)
            else:
                self.sessions[result.session_id] = WebSession(result.session_id, self.adapter.adapter_id, "ready", _now(), result.safe_domain or decision.safe_domain)
        return result

    def _validate_url(self, url: str, permission: WebPermission) -> WebPolicyDecision:
        if not url or len(url) > 2048 or any(char in url for char in "\r\n\x00"):
            return WebPolicyDecision(False, WebAutomationStatus.INVALID_INPUT, "A valid bounded HTTP(S) URL is required.", WebRiskLevel.LOW, permission=permission, error_code="WEB_URL_INVALID")
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Only HTTP and HTTPS URLs are allowed.", WebRiskLevel.HIGH, permission=permission, error_code="WEB_SCHEME_BLOCKED")
        if parsed.username or parsed.password:
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Credential-bearing URLs are blocked.", WebRiskLevel.HIGH, permission=permission, error_code="WEB_CREDENTIAL_URL_BLOCKED")
        domain = parsed.hostname.rstrip(".").lower()
        if parsed.query and any(_TOKEN_QUERY.search(part.split("=", 1)[0]) for part in parsed.query.split("&")):
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "URLs containing sensitive query fields are blocked.", WebRiskLevel.HIGH, safe_domain=domain, permission=permission, error_code="WEB_CREDENTIAL_URL_BLOCKED")
        if _BLOCKED_TOPICS.search(domain + parsed.path):
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "The URL is blocked by web safety policy.", WebRiskLevel.HIGH, safe_domain=domain, permission=permission, error_code="WEB_DOMAIN_POLICY_BLOCKED")
        if parsed.scheme.lower() == "http" and not self.allow_http:
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Plain HTTP inspection is disabled; use HTTPS.", WebRiskLevel.MODERATE, safe_domain=domain, permission=permission, error_code="WEB_SCHEME_BLOCKED")
        if not self.allow_local_targets and self._is_local_target(domain):
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Local and private-network targets are blocked by default.", WebRiskLevel.HIGH, safe_domain=domain, permission=permission, error_code="WEB_PRIVATE_NETWORK_BLOCKED")
        normalized = urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, ""))
        return WebPolicyDecision(True, WebAutomationStatus.READY, "URL passed read-only policy.", WebRiskLevel.LOW, domain, normalized, permission)

    def _validate_fetch_url(self, url: str) -> WebPolicyDecision:
        decision = self._validate_url(url, WebPermission.URL_OPEN)
        if not decision.allowed or self.allow_local_targets:
            return decision
        domain = decision.safe_domain or ""
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)}
        except socket.gaierror:
            return WebPolicyDecision(False, WebAutomationStatus.FAILED, "The page hostname could not be resolved.", WebRiskLevel.LOW, safe_domain=domain, permission=WebPermission.URL_OPEN, error_code="WEB_DNS_ERROR")
        if not addresses or any(self._is_local_target(address) for address in addresses):
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "The hostname resolves to a private or internal network.", WebRiskLevel.HIGH, safe_domain=domain, permission=WebPermission.URL_OPEN, error_code="WEB_PRIVATE_NETWORK_BLOCKED")
        return decision

    @staticmethod
    def _is_local_target(domain: str) -> bool:
        if domain in {"localhost", "localhost.localdomain"} or domain.endswith(".local"):
            return True
        try:
            address = ipaddress.ip_address(domain.strip("[]"))
            return address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_unspecified
        except ValueError:
            return False

    @staticmethod
    def _permission_for(action: WebActionType) -> WebPermission:
        return {
            WebActionType.STATUS: WebPermission.STATUS_READ,
            WebActionType.OPEN_URL: WebPermission.URL_OPEN,
            WebActionType.GET_PAGE_TITLE: WebPermission.PAGE_READ,
            WebActionType.GET_CURRENT_URL: WebPermission.PAGE_READ,
            WebActionType.SNAPSHOT_PAGE: WebPermission.SNAPSHOT,
            WebActionType.SUMMARIZE_PAGE_METADATA: WebPermission.PAGE_READ,
            WebActionType.CLOSE_SESSION: WebPermission.SESSION_CREATE,
            WebActionType.CLICK: WebPermission.CLICK,
            WebActionType.TYPE_TEXT: WebPermission.TYPE,
            WebActionType.SUBMIT_FORM: WebPermission.FORM_SUBMIT,
            WebActionType.DOWNLOAD: WebPermission.DOWNLOAD,
            WebActionType.UPLOAD: WebPermission.UPLOAD,
            WebActionType.LOGIN: WebPermission.LOGIN,
            WebActionType.PURCHASE: WebPermission.PURCHASE,
            WebActionType.SEND_MESSAGE: WebPermission.MESSAGE_SEND,
            WebActionType.DELETE: WebPermission.DELETE,
            WebActionType.ACCOUNT_CHANGE: WebPermission.ACCOUNT_CHANGE,
        }[action]

    def _latest_session_id(self) -> str | None:
        return next(reversed(self.sessions), None) if self.sessions else None

    def _audit(self, request: WebActionRequest, result: WebActionResult, decision: WebPolicyDecision) -> None:
        snapshot = result.snapshot
        event = WebAuditEvent(
            str(uuid.uuid4()), request.request_id, request.action_type.value,
            decision.risk_level.value, result.status.value, _now(),
            decision.safe_domain, "allowed" if decision.allowed else "blocked",
            decision.approval_required, result.message[:200],
            final_domain=result.safe_domain,
            redirect_count=snapshot.redirect_count if snapshot else 0,
            content_type=snapshot.content_type if snapshot else None,
            byte_count=snapshot.byte_count if snapshot else 0,
            error_code=result.error_code,
        )
        self._audit_events.append(event)
        self._audit_events = self._audit_events[-self.audit_retention:]
        self._save_audit()
        self.logger.info("web_action_audited request_id=%s action_type=%s status=%s safe_domain=%s", request.request_id, request.action_type.value, result.status.value, event.safe_domain or "none")

    def _load_audit(self) -> list[WebAuditEvent]:
        if not self.audit_path.exists():
            return []
        try:
            payload = json.loads(self.audit_path.read_text(encoding="utf-8"))
            return [WebAuditEvent(**item) for item in payload.get("events", [])][-self.audit_retention:]
        except (OSError, ValueError, TypeError):
            return []

    def _save_audit(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.audit_path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump({"schema_version": 1, "events": [asdict(item) for item in self._audit_events]}, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.audit_path)

    @staticmethod
    def safe_url_for_display(url: str | None) -> str | None:
        if not url:
            return None
        parsed = urlsplit(url)
        query = "redacted=1" if parsed.query and any(_TOKEN_QUERY.search(part.split("=", 1)[0]) for part in parsed.query.split("&")) else parsed.query
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, ""))
