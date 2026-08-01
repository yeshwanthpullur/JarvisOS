"""Governed read-only web automation foundation."""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlsplit, urlunsplit


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


class WebAutomationAdapter(Protocol):
    adapter_id: str
    available: bool
    capabilities: tuple[WebActionType, ...]

    def open_url(self, url: str, request_id: str) -> WebActionResult: ...
    def get_page_title(self, session_id: str, request_id: str) -> WebActionResult: ...
    def get_current_url(self, session_id: str, request_id: str) -> WebActionResult: ...
    def snapshot_page(self, session_id: str, request_id: str) -> WebActionResult: ...
    def close_session(self, session_id: str, request_id: str) -> WebActionResult: ...


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
        self.enabled = bool(getattr(config, "enabled", False))
        configured_mode = getattr(config, "mode", "off")
        self.mode = WebAutomationMode.OFF if isinstance(configured_mode, bool) else WebAutomationMode(str(configured_mode))
        self.allow_local_targets = bool(getattr(config, "allow_local_targets", False))
        self.audit_retention = max(1, int(getattr(config, "audit_retention", 100)))
        self.storage_dir = Path(storage_dir)
        self.audit_path = self.storage_dir / "audit.json"
        self.adapter = adapter or UnavailableBrowserAdapter()
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
            result = WebActionResult(request.request_id, request.action_type, decision.status, decision.reason, request.session_id, decision.safe_domain, error_code="policy_blocked", approval_required=decision.approval_required)
            self._audit(request, result, decision)
            return result
        if not self.enabled or self.mode is WebAutomationMode.OFF:
            result = WebActionResult(request.request_id, request.action_type, WebAutomationStatus.DISABLED, "Web Automation is disabled. Read-only policy remains available.", request.session_id, decision.safe_domain, error_code="web_disabled")
            self._audit(request, result, decision)
            return result
        if not self.adapter.available:
            result = WebActionResult(request.request_id, request.action_type, WebAutomationStatus.UNAVAILABLE, "No governed local browser adapter is configured.", request.session_id, decision.safe_domain, error_code="adapter_unavailable")
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
            return WebActionResult(request.request_id, request.action_type, WebAutomationStatus.INVALID_INPUT, "No active web session exists.", error_code="missing_session")
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
            return WebActionResult(request.request_id, request.action_type, WebAutomationStatus.TIMED_OUT, "The bounded browser action timed out.", request.session_id, decision.safe_domain, error_code="timeout")
        except Exception:
            return WebActionResult(request.request_id, request.action_type, WebAutomationStatus.FAILED, "The browser adapter failed safely.", request.session_id, decision.safe_domain, error_code="adapter_failure")
        if result.status is WebAutomationStatus.COMPLETED and result.session_id:
            if request.action_type is WebActionType.CLOSE_SESSION:
                self.sessions.pop(result.session_id, None)
            else:
                self.sessions[result.session_id] = WebSession(result.session_id, self.adapter.adapter_id, "ready", _now(), result.safe_domain or decision.safe_domain)
        return result

    def _validate_url(self, url: str, permission: WebPermission) -> WebPolicyDecision:
        if not url or len(url) > 2048 or any(char in url for char in "\r\n\x00"):
            return WebPolicyDecision(False, WebAutomationStatus.INVALID_INPUT, "A valid bounded HTTP(S) URL is required.", WebRiskLevel.LOW, permission=permission)
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Only HTTP and HTTPS URLs are allowed.", WebRiskLevel.HIGH, permission=permission)
        if parsed.username or parsed.password:
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Credential-bearing URLs are blocked.", WebRiskLevel.HIGH, permission=permission)
        domain = parsed.hostname.rstrip(".").lower()
        if _BLOCKED_TOPICS.search(domain + parsed.path):
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "The URL is blocked by web safety policy.", WebRiskLevel.HIGH, safe_domain=domain, permission=permission)
        if not self.allow_local_targets and self._is_local_target(domain):
            return WebPolicyDecision(False, WebAutomationStatus.BLOCKED_BY_POLICY, "Local and private-network targets are blocked by default.", WebRiskLevel.HIGH, safe_domain=domain, permission=permission)
        normalized = urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, ""))
        return WebPolicyDecision(True, WebAutomationStatus.READY, "URL passed read-only policy.", WebRiskLevel.LOW, domain, normalized, permission)

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
        event = WebAuditEvent(str(uuid.uuid4()), request.request_id, request.action_type.value, decision.risk_level.value, result.status.value, _now(), result.safe_domain or decision.safe_domain, "allowed" if decision.allowed else "blocked", decision.approval_required, result.message[:200])
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
