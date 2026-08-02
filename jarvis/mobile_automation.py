"""Governed planning-only mobile automation foundation."""

from __future__ import annotations

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


def _now() -> str:
    return datetime.now(UTC).isoformat()


class MobileAutomationStatus(StrEnum):
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
    READY = "ready"
    NO_DEVICE = "no_device"
    DEVICE_DETECTED = "device_detected"
    PERMISSION_REQUIRED = "permission_required"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    ACTION_BLOCKED = "action_blocked"
    FAILED = "failed"
    PARTIAL = "partial"
    FUTURE = "future"
    CLOSED = "closed"


class MobileAutomationMode(StrEnum):
    OFF = "off"
    PLANNING_ONLY = "planning_only"
    READ_ONLY_STATUS = "read_only_status"
    MANUAL_APPROVAL_REQUIRED = "manual_approval_required"
    FUTURE_AUTOMATIC = "future_automatic"


class MobilePlatform(StrEnum):
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"
    EMULATOR = "emulator"
    FUTURE = "future"


class MobileDeviceState(StrEnum):
    UNKNOWN = "unknown"
    NOT_CONNECTED = "not_connected"
    DETECTED = "detected"
    UNAVAILABLE = "unavailable"


class MobileConnectionState(StrEnum):
    DISCONNECTED = "disconnected"
    PLANNED = "planned"
    PERMISSION_REQUIRED = "permission_required"
    CONNECTED = "connected"


class MobileCapability(StrEnum):
    STATUS = "status"
    POLICY = "policy"
    CAPABILITIES = "capabilities"
    DEVICE_SUMMARY = "device_summary"
    CONNECTION_PLAN = "connection_plan"
    SETUP_GUIDE = "setup_guide"
    AUDIT_READ = "audit_read"
    CLOSE_SESSION = "close_session"


class MobileRiskLevel(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class MobilePermission(StrEnum):
    STATUS_READ = "mobile_status_read"
    POLICY_READ = "mobile_policy_read"
    SETUP_GUIDE_READ = "mobile_setup_guide_read"
    DEVICE_SUMMARY_READ = "mobile_device_summary_read"
    CONNECTION_PLAN_CREATE = "mobile_connection_plan_create"
    AUDIT_READ = "mobile_audit_read"
    DEVICE_CONNECT = "mobile_device_connect"
    NOTIFICATION_READ = "mobile_notification_read"
    MESSAGE_READ = "mobile_message_read"
    MESSAGE_SEND = "mobile_message_send"
    CALL_START = "mobile_call_start"
    CALL_RECORD = "mobile_call_record"
    CONTACT_READ = "mobile_contact_read"
    PHOTO_READ = "mobile_photo_read"
    CAMERA_ACCESS = "mobile_camera_access"
    MICROPHONE_ACCESS = "mobile_microphone_access"
    LOCATION_ACCESS = "mobile_location_access"
    APP_OPEN = "mobile_app_open"
    TAP = "mobile_tap"
    TYPE = "mobile_type"
    SWIPE = "mobile_swipe"
    FILE_TRANSFER = "mobile_file_transfer"
    APP_INSTALL = "mobile_app_install"
    APP_UNINSTALL = "mobile_app_uninstall"
    SETTING_CHANGE = "mobile_setting_change"
    PURCHASE = "mobile_purchase"
    LOGIN = "mobile_login"
    UNLOCK = "mobile_unlock"
    BACKGROUND_MONITOR = "mobile_background_monitor"


class MobileActionType(StrEnum):
    STATUS = "status"
    POLICY = "policy"
    CAPABILITIES = "capabilities"
    DEVICE_SUMMARY = "device_summary"
    CONNECTION_PLAN = "connection_plan"
    SETUP_GUIDE = "setup_guide"
    AUDIT_READ = "audit_read"
    CLOSE_SESSION = "close_session"
    READ_NOTIFICATIONS = "read_notifications"
    READ_MESSAGES = "read_messages"
    SEND_MESSAGE = "send_message"
    MAKE_CALL = "make_call"
    ANSWER_CALL = "answer_call"
    RECORD_CALL = "record_call"
    READ_CONTACTS = "read_contacts"
    READ_PHOTOS = "read_photos"
    ACCESS_CAMERA = "access_camera"
    ACCESS_MICROPHONE = "access_microphone"
    ACCESS_LOCATION = "access_location"
    OPEN_APP = "open_app"
    TAP = "tap"
    TYPE_TEXT = "type_text"
    SWIPE = "swipe"
    SUBMIT_FORM = "submit_form"
    INSTALL_APP = "install_app"
    UNINSTALL_APP = "uninstall_app"
    CHANGE_SETTING = "change_setting"
    TRANSFER_FILE = "transfer_file"
    DELETE_FILE = "delete_file"
    PURCHASE = "purchase"
    LOGIN = "login"
    UNLOCK_DEVICE = "unlock_device"
    BACKGROUND_MONITOR = "background_monitor"


SAFE_ACTIONS = frozenset({
    MobileActionType.STATUS, MobileActionType.POLICY, MobileActionType.CAPABILITIES,
    MobileActionType.DEVICE_SUMMARY, MobileActionType.CONNECTION_PLAN,
    MobileActionType.SETUP_GUIDE, MobileActionType.AUDIT_READ,
    MobileActionType.CLOSE_SESSION,
})


@dataclass(frozen=True, slots=True)
class MobileActionRequest:
    request_id: str
    action_type: MobileActionType
    summary: str = ""
    permissions: tuple[MobilePermission, ...] = ()
    approval_reference: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MobileActionResult:
    request_id: str
    action_type: MobileActionType
    status: MobileAutomationStatus
    message: str
    error_code: str | None = None
    session_id: str | None = None
    risk_level: MobileRiskLevel = MobileRiskLevel.MINIMAL
    approval_required: bool = False


@dataclass(frozen=True, slots=True)
class MobileSession:
    session_id: str
    adapter_id: str
    status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class MobileDeviceSummary:
    alias: str
    platform: MobilePlatform
    state: MobileDeviceState
    connection_state: MobileConnectionState
    private_identifiers_stored: bool = False


@dataclass(frozen=True, slots=True)
class MobileAuditEvent:
    event_id: str
    request_id: str
    timestamp: str
    action_type: str
    risk_level: str
    policy_decision: str
    status: str
    adapter_id: str
    safe_summary: str
    error_code: str | None = None


class MobileAutomationAdapter(Protocol):
    adapter_id: str
    available: bool
    live_control: bool
    capabilities: tuple[MobileCapability, ...]

    def execute(self, request: MobileActionRequest) -> MobileActionResult: ...


class NullMobileAutomationAdapter:
    adapter_id = "null-mobile"
    available = False
    live_control = False
    capabilities: tuple[MobileCapability, ...] = ()

    def execute(self, request: MobileActionRequest) -> MobileActionResult:
        return MobileActionResult(request.request_id, request.action_type, MobileAutomationStatus.UNAVAILABLE, "No mobile adapter is configured. No device was accessed.", "MOBILE_NO_ADAPTER")


class PlanningOnlyMobileAdapter:
    adapter_id = "planning-only"
    available = True
    live_control = False
    capabilities = tuple(MobileCapability)

    def execute(self, request: MobileActionRequest) -> MobileActionResult:
        messages = {
            MobileActionType.STATUS: "Mobile planning foundation is available; live phone control is off.",
            MobileActionType.POLICY: "Only status, policy, setup, capability summaries, connection planning, audit reading, and session closure are allowed.",
            MobileActionType.CAPABILITIES: "Current capabilities are planning and status only; device control and private data access are blocked.",
            MobileActionType.DEVICE_SUMMARY: "No real device is connected or inspected.",
            MobileActionType.CONNECTION_PLAN: "A future connection would require an explicitly approved local adapter and scoped permissions. Nothing was connected.",
            MobileActionType.SETUP_GUIDE: "Future Android support may use ADB, an emulator, Appium, or a companion app after explicit approval. None is enabled now.",
            MobileActionType.CLOSE_SESSION: "Mobile planning session state cleared.",
        }
        status = MobileAutomationStatus.CLOSED if request.action_type is MobileActionType.CLOSE_SESSION else MobileAutomationStatus.PARTIAL
        return MobileActionResult(request.request_id, request.action_type, status, messages.get(request.action_type, "Planning-only mobile action completed without device access."))


_PRIVATE_TERMS = re.compile(r"(?i)\b(notification|message|call|contact|photo|camera|microphone|location|install|uninstall|setting|purchase|login|unlock|tap|swipe|type|background|monitor|record|send|read)\b")


class MobileAutomationManager:
    """Policy gate and planning coordinator with no phone execution authority."""

    def __init__(self, storage_dir: Path, settings: object | None = None, adapter: MobileAutomationAdapter | None = None, logger: logging.Logger | None = None) -> None:
        config = getattr(settings, "mobile", None)
        self.enabled = bool(getattr(config, "automation_enabled", True))
        self.mode = MobileAutomationMode(str(getattr(config, "automation_mode", "planning_only")))
        self.audit_retention = min(500, max(1, int(getattr(config, "audit_retention", 100))))
        configured = str(getattr(config, "automation_adapter", "planning-only"))
        self.adapter = adapter or (PlanningOnlyMobileAdapter() if configured == "planning-only" else NullMobileAutomationAdapter())
        self.storage_dir = Path(storage_dir)
        self.audit_path = self.storage_dir / "audit.json"
        self.logger = logger or logging.getLogger("mobile_automation")
        self.sessions: dict[str, MobileSession] = {}
        self._audit = self._load_audit()
        self.initialized = True

    def status(self) -> dict[str, Any]:
        return {
            "initialized": self.initialized, "enabled": self.enabled,
            "status": MobileAutomationStatus.PARTIAL.value if self.enabled else MobileAutomationStatus.DISABLED.value,
            "mode": self.mode.value, "adapter_id": self.adapter.adapter_id,
            "adapter_available": self.adapter.available, "real_phone_adapter": False,
            "live_control": False, "private_data_access": "blocked",
            "sensitive_actions": "blocked", "device_count": 0,
            "audit_events": len(self._audit),
        }

    def execute(self, request: MobileActionRequest) -> MobileActionResult:
        if request.action_type not in SAFE_ACTIONS:
            result = self._blocked(request)
        elif not self.enabled or self.mode is MobileAutomationMode.OFF:
            result = MobileActionResult(request.request_id, request.action_type, MobileAutomationStatus.DISABLED, "Mobile Automation is disabled. No device was accessed.", "MOBILE_DISABLED")
        else:
            result = self.adapter.execute(request)
            if request.action_type is MobileActionType.CLOSE_SESSION:
                self.sessions.clear()
        self._record(request, result)
        return result

    def plan(self, objective: str, request_id: str | None = None) -> MobileActionResult:
        safe_objective = " ".join(objective.split())[:500]
        request = MobileActionRequest(request_id or str(uuid.uuid4()), MobileActionType.CONNECTION_PLAN, safe_objective, (MobilePermission.CONNECTION_PLAN_CREATE,))
        if _PRIVATE_TERMS.search(safe_objective):
            result = MobileActionResult(request.request_id, request.action_type, MobileAutomationStatus.BLOCKED_BY_POLICY, "This mobile task requires private data or live control, which is blocked by the current foundation. No phone action was performed.", "MOBILE_ACTION_BLOCKED", risk_level=MobileRiskLevel.HIGH, approval_required=True)
            self._record(request, result)
            return result
        return self.execute(request)

    def setup(self, request_id: str | None = None) -> MobileActionResult:
        return self.execute(MobileActionRequest(request_id or str(uuid.uuid4()), MobileActionType.SETUP_GUIDE, permissions=(MobilePermission.SETUP_GUIDE_READ,)))

    def capabilities(self, request_id: str | None = None) -> MobileActionResult:
        return self.execute(MobileActionRequest(request_id or str(uuid.uuid4()), MobileActionType.CAPABILITIES, permissions=(MobilePermission.STATUS_READ,)))

    def close(self, request_id: str | None = None) -> MobileActionResult:
        return self.execute(MobileActionRequest(request_id or str(uuid.uuid4()), MobileActionType.CLOSE_SESSION, permissions=(MobilePermission.STATUS_READ,)))

    def audit_events(self) -> tuple[MobileAuditEvent, ...]:
        return tuple(self._audit)

    def device_summaries(self) -> tuple[MobileDeviceSummary, ...]:
        return ()

    def _blocked(self, request: MobileActionRequest) -> MobileActionResult:
        code = "MOBILE_PRIVATE_DATA_BLOCKED" if request.action_type in {MobileActionType.READ_NOTIFICATIONS, MobileActionType.READ_MESSAGES, MobileActionType.READ_CONTACTS, MobileActionType.READ_PHOTOS} else "MOBILE_ACTION_BLOCKED"
        return MobileActionResult(request.request_id, request.action_type, MobileAutomationStatus.BLOCKED_BY_POLICY, "Sensitive mobile actions are blocked. No device or private data was accessed.", code, risk_level=MobileRiskLevel.HIGH, approval_required=True)

    def _record(self, request: MobileActionRequest, result: MobileActionResult) -> None:
        event = MobileAuditEvent(str(uuid.uuid4()), request.request_id, _now(), request.action_type.value, result.risk_level.value, "allowed" if result.status not in {MobileAutomationStatus.BLOCKED_BY_POLICY, MobileAutomationStatus.ACTION_BLOCKED} else "blocked", result.status.value, self.adapter.adapter_id, "mobile request evaluated; private content not retained", result.error_code)
        self._audit.append(event)
        self._audit = self._audit[-self.audit_retention:]
        self._persist_audit()

    def _load_audit(self) -> list[MobileAuditEvent]:
        try:
            data = json.loads(self.audit_path.read_text(encoding="utf-8"))
            return [MobileAuditEvent(**item) for item in data[-self.audit_retention:] if isinstance(item, dict)]
        except (OSError, ValueError, TypeError):
            return []

    def _persist_audit(self) -> None:
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            temporary = self.audit_path.with_suffix(".tmp")
            temporary.write_text(json.dumps([asdict(item) for item in self._audit], indent=2), encoding="utf-8")
            os.replace(temporary, self.audit_path)
        except OSError:
            self.logger.warning("mobile_audit_persistence_failed", extra={"event": "mobile_audit_persistence_failed"})
