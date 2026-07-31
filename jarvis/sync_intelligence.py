"""Governed, local-first synchronization foundation for JARVIS OS."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Protocol


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SyncMode(StrEnum):
    OFF = "off"
    LOCAL_QUEUE_ONLY = "local_queue_only"
    MANUAL = "manual"
    FUTURE_AUTOMATIC = "future_automatic"


class SyncStatus(StrEnum):
    DISABLED = "disabled"
    READY = "ready"
    QUEUED = "queued"
    SYNCING = "syncing"
    SYNCED = "synced"
    UNAVAILABLE = "unavailable"
    OFFLINE = "offline"
    FAILED = "failed"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    INVALID = "invalid"
    CONFLICT = "conflict"
    CANCELLED = "cancelled"


class SyncDirection(StrEnum):
    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"


class SyncItemType(StrEnum):
    PROJECT_STATUS = "project_status"
    PROJECT_HEALTH = "project_health"
    RELEASE_METADATA = "release_metadata"
    TASK_SUMMARY = "task_summary"
    GOAL_SUMMARY = "goal_summary"
    MEMORY_SUMMARY = "memory_summary"
    PREFERENCE_SUMMARY = "preference_summary"
    SYNC_CHECKPOINT = "sync_checkpoint"


class SyncConflictStrategy(StrEnum):
    MANUAL = "manual"
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    NEWEST_WINS = "newest_wins"
    MERGE_SUMMARY = "merge_summary"


class SyncPermission(StrEnum):
    STATUS_READ = "sync_status_read"
    QUEUE_READ = "sync_queue_read"
    QUEUE_ADD = "sync_queue_add"
    QUEUE_CANCEL = "sync_queue_cancel"
    QUEUE_CLEAR = "sync_queue_clear"
    MANUAL_START = "manual_sync_start"
    RETRY = "sync_retry"
    REMOTE_DOWNLOAD = "remote_download"
    CONFLICT_RESOLVE = "conflict_resolution"
    POLICY_UPDATE = "sync_policy_update"
    AUDIT_READ = "sync_audit_read"


@dataclass(frozen=True, slots=True)
class SyncLimits:
    maximum_item_size: int = 8192
    maximum_queue_items: int = 100
    maximum_batch_size: int = 10
    maximum_attempts: int = 3
    completed_retention_count: int = 25
    audit_retention_count: int = 100
    maximum_nested_depth: int = 4
    maximum_string_length: int = 1000


@dataclass(slots=True)
class SyncItem:
    sync_item_id: str
    item_type: str
    schema_version: int
    direction: str
    status: str
    sanitized_payload: dict[str, Any]
    payload_hash: str
    source_device_id: str
    created_at: str
    updated_at: str
    attempt_count: int = 0
    maximum_attempts: int = 3
    next_retry_at: str | None = None
    provider_id: str | None = None
    last_error_code: str | None = None
    conflict_metadata: dict[str, Any] = field(default_factory=dict)
    audit_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SyncResult:
    status: SyncStatus
    message: str
    sync_item_id: str | None = None
    error_code: str | None = None
    retryable: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SyncBatchResult:
    status: SyncStatus
    processed: int
    synced: int
    failed: int
    conflicts: int
    results: tuple[SyncResult, ...] = ()


@dataclass(frozen=True, slots=True)
class SyncProviderInfo:
    provider_id: str
    available: bool
    remote: bool
    encrypted_transport: bool
    message: str


@dataclass(frozen=True, slots=True)
class SyncPolicyDecision:
    allowed: bool
    sanitized_payload: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class SyncConflict:
    conflict_id: str
    sync_item_id: str
    local_hash: str
    remote_hash: str
    local_version: int
    remote_version: int
    strategy: str
    status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SyncAuditEvent:
    event_id: str
    event_type: str
    sync_item_id: str | None
    status: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SyncAdapter(Protocol):
    provider_info: SyncProviderInfo

    def upload(self, item: SyncItem, timeout_seconds: int = 15) -> SyncResult: ...


class LocalQueueAdapter:
    """Identifies the working local queue; it never performs remote upload."""

    provider_info = SyncProviderInfo("local-queue", True, False, False, "Local queue is ready.")

    def upload(self, item: SyncItem, timeout_seconds: int = 15) -> SyncResult:
        return SyncResult(SyncStatus.UNAVAILABLE, "Local queue adapter is not a remote sync backend.", item.sync_item_id, "remote_unavailable")


class UnavailableRemoteSyncAdapter:
    """Truthful placeholder until an encrypted authenticated backend exists."""

    provider_info = SyncProviderInfo("unavailable-remote", False, True, False, "No encrypted remote sync backend is configured.")

    def upload(self, item: SyncItem, timeout_seconds: int = 15) -> SyncResult:
        return SyncResult(SyncStatus.UNAVAILABLE, "Remote sync is unavailable; the item remains queued locally.", item.sync_item_id, "remote_unavailable", True)


_SCHEMAS: dict[str, frozenset[str]] = {
    "project_status": frozenset({"release", "commit", "primary_mode", "overall_mvp_readiness", "working_categories", "partial_categories", "experimental_categories", "next_milestone", "updated_at"}),
    "project_health": frozenset({"release", "commit", "overall_mvp_readiness", "categories", "updated_at"}),
    "release_metadata": frozenset({"release", "commit", "title", "published_at"}),
    "task_summary": frozenset({"id", "title", "status", "progress", "updated_at"}),
    "goal_summary": frozenset({"id", "title", "status", "progress", "updated_at"}),
    "memory_summary": frozenset({"summary", "topics", "updated_at"}),
    "preference_summary": frozenset({"key", "value", "updated_at"}),
    "sync_checkpoint": frozenset({"cursor", "version", "updated_at"}),
}
_SECRET_KEY = re.compile(r"(?i)(api.?key|access.?token|authorization|password|secret|cookie|credential)")
_SECRET_VALUE = re.compile(r"(?i)(bearer\s+[a-z0-9._-]{8,}|sk-[a-z0-9]{12,}|-----BEGIN [A-Z ]+PRIVATE KEY-----)")
_BASE64_BLOB = re.compile(r"^[A-Za-z0-9+/]{256,}={0,2}$")


class SyncIntelligence:
    """Owns governed queueing and remote-adapter coordination, not local records."""

    def __init__(self, storage_dir: Path, settings: object | None = None, logger: logging.Logger | None = None) -> None:
        self.storage_dir = Path(storage_dir)
        self.queue_path = self.storage_dir / "queue.json"
        self.installation_path = self.storage_dir / "installation.json"
        sync_config = getattr(settings, "sync", None)
        self.limits = SyncLimits(**{name: int(getattr(sync_config, name, getattr(SyncLimits(), name))) for name in SyncLimits.__slots__}) if sync_config else SyncLimits()
        configured_mode = getattr(sync_config, "mode", "off")
        self.mode = SyncMode.OFF if isinstance(configured_mode, bool) else SyncMode(str(configured_mode))
        self.conflict_strategy = SyncConflictStrategy(str(getattr(sync_config, "conflict_strategy", "manual")))
        self.selected_adapter = str(getattr(sync_config, "adapter", "local-queue"))
        self.logger = logger or logging.getLogger(__name__)
        self.adapters: dict[str, SyncAdapter] = {
            "local-queue": LocalQueueAdapter(),
            "unavailable-remote": UnavailableRemoteSyncAdapter(),
        }
        self._store: dict[str, Any] = {}
        self.installation_id = ""
        self.initialized = False
        self.initialize()

    def initialize(self) -> dict[str, Any]:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.installation_id = self._load_installation_id()
        self._store = self._load_store()
        stored_mode = self._store.get("mode")
        if stored_mode in {item.value for item in SyncMode}:
            self.mode = SyncMode(stored_mode)
        self.initialized = True
        return self.status()

    def register_adapter(self, adapter: SyncAdapter) -> None:
        self.adapters[adapter.provider_info.provider_id] = adapter

    def enable_manual(self) -> SyncResult:
        self.mode = SyncMode.MANUAL
        self._store["mode"] = self.mode.value
        self._audit("sync_mode_changed", None, "ready", {"mode": self.mode.value})
        self._save()
        return SyncResult(SyncStatus.READY, "Sync manual/local queue mode enabled. No automatic upload or remote backend was enabled.")

    def disable(self) -> SyncResult:
        self.mode = SyncMode.OFF
        self._store["mode"] = self.mode.value
        self._audit("sync_mode_changed", None, "disabled", {"mode": self.mode.value})
        self._save()
        return SyncResult(SyncStatus.DISABLED, "Sync disabled. Existing queue items were preserved.")

    def status(self) -> dict[str, Any]:
        counts = self.summary()
        remote = self._remote_adapter()
        return {
            "mode": self.mode.value,
            "enabled": self.mode is not SyncMode.OFF,
            "adapter": self.selected_adapter,
            "remote_available": bool(remote and remote.provider_info.available and remote.provider_info.encrypted_transport),
            "queue_count": counts["queued"],
            "failed_count": counts["failed"],
            "conflict_count": counts["conflicts"],
            "last_successful_sync": self._store.get("last_successful_sync"),
            "policy": "allowlisted summaries only; secrets/raw files blocked",
            "deployment_status_only": True,
        }

    def evaluate_policy(self, item_type: str, payload: object) -> SyncPolicyDecision:
        if item_type not in _SCHEMAS:
            return SyncPolicyDecision(False, reason="Unsupported sync item type.", error_code="unsupported_item_type")
        if not isinstance(payload, dict):
            return SyncPolicyDecision(False, reason="Sync payload must be a structured object.", error_code="invalid_payload")
        unknown = set(payload) - _SCHEMAS[item_type]
        if unknown:
            return SyncPolicyDecision(False, reason="Payload contains fields outside the approved schema.", error_code="unknown_fields")
        if item_type == SyncItemType.PROJECT_HEALTH.value and "categories" in payload:
            categories = payload["categories"]
            category_fields = {"name", "status", "confidence", "evidence", "next_action"}
            if not isinstance(categories, list) or any(not isinstance(item, dict) or set(item) - category_fields for item in categories):
                return SyncPolicyDecision(False, reason="Project health categories contain fields outside the approved schema.", error_code="unknown_fields")
        try:
            sanitized = self._sanitize(payload, depth=0)
            encoded = json.dumps(sanitized, sort_keys=True, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as exc:
            return SyncPolicyDecision(False, reason=str(exc), error_code="policy_rejected")
        if len(encoded) > self.limits.maximum_item_size:
            return SyncPolicyDecision(False, reason="Payload exceeds the sync item size limit.", error_code="item_too_large")
        return SyncPolicyDecision(True, sanitized_payload=sanitized)

    def enqueue(self, item_type: str | SyncItemType, payload: dict[str, Any], direction: SyncDirection = SyncDirection.UPLOAD) -> SyncResult:
        item_type_value = item_type.value if isinstance(item_type, SyncItemType) else str(item_type)
        decision = self.evaluate_policy(item_type_value, payload)
        if not decision.allowed:
            self._audit("sync_enqueue_rejected", None, "blocked_by_policy", {"error_code": decision.error_code})
            self._save()
            return SyncResult(SyncStatus.BLOCKED_BY_POLICY, decision.reason, error_code=decision.error_code)
        active = [item for item in self._items() if item.status in {SyncStatus.QUEUED.value, SyncStatus.FAILED.value, SyncStatus.CONFLICT.value}]
        if len(active) >= self.limits.maximum_queue_items:
            return SyncResult(SyncStatus.FAILED, "Sync queue capacity reached.", error_code="queue_full")
        canonical = json.dumps(decision.sanitized_payload, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        duplicate = next((item for item in active if item.item_type == item_type_value and item.payload_hash == payload_hash), None)
        if duplicate:
            return SyncResult(SyncStatus.QUEUED, "An identical sanitized item is already queued.", duplicate.sync_item_id, "duplicate_item")
        timestamp = _now()
        item = SyncItem(
            sync_item_id=str(uuid.uuid4()), item_type=item_type_value, schema_version=1,
            direction=direction.value, status=SyncStatus.QUEUED.value,
            sanitized_payload=decision.sanitized_payload, payload_hash=payload_hash,
            source_device_id=self.installation_id, created_at=timestamp, updated_at=timestamp,
            maximum_attempts=self.limits.maximum_attempts,
            audit_metadata={"source": "local_command", "sanitized": True},
        )
        self._store["items"].append(asdict(item))
        self._audit("sync_item_queued", item.sync_item_id, item.status, {"item_type": item.item_type})
        self._save()
        return SyncResult(SyncStatus.QUEUED, "Sanitized summary queued locally.", item.sync_item_id)

    def list_items(self) -> tuple[SyncItem, ...]:
        return tuple(self._items())

    def inspect(self, sync_item_id: str) -> SyncItem | None:
        return next((item for item in self._items() if item.sync_item_id == sync_item_id), None)

    def cancel(self, sync_item_id: str) -> SyncResult:
        item = self.inspect(sync_item_id)
        if item is None:
            return SyncResult(SyncStatus.INVALID, "Sync item was not found.", sync_item_id, "missing_item")
        if item.status not in {SyncStatus.QUEUED.value, SyncStatus.FAILED.value}:
            return SyncResult(SyncStatus.INVALID, "Only queued or failed items can be cancelled.", sync_item_id, "invalid_state")
        self._update_item(item.sync_item_id, status=SyncStatus.CANCELLED.value, updated_at=_now())
        self._audit("sync_item_cancelled", item.sync_item_id, "cancelled")
        self._save()
        return SyncResult(SyncStatus.CANCELLED, "Sync item cancelled locally.", sync_item_id)

    def retry(self, sync_item_id: str) -> SyncResult:
        item = self.inspect(sync_item_id)
        if item is None:
            return SyncResult(SyncStatus.INVALID, "Sync item was not found.", sync_item_id, "missing_item")
        if item.status != SyncStatus.FAILED.value or item.attempt_count >= item.maximum_attempts:
            return SyncResult(SyncStatus.INVALID, "Item is not eligible for retry.", sync_item_id, "retry_not_allowed")
        self._update_item(sync_item_id, status=SyncStatus.QUEUED.value, next_retry_at=None, updated_at=_now())
        self._audit("sync_item_retry_queued", sync_item_id, "queued")
        self._save()
        return SyncResult(SyncStatus.QUEUED, "Sync item queued for a bounded retry.", sync_item_id)

    def run(self) -> SyncBatchResult:
        if self.mode is SyncMode.OFF:
            return SyncBatchResult(SyncStatus.DISABLED, 0, 0, 0, 0, (SyncResult(SyncStatus.DISABLED, "Sync is disabled."),))
        adapter = self._remote_adapter()
        if adapter is None or not adapter.provider_info.available or not adapter.provider_info.encrypted_transport:
            result = SyncResult(SyncStatus.UNAVAILABLE, "No authenticated encrypted remote sync backend is configured. Queue items remain local.", error_code="remote_unavailable", retryable=True)
            self._audit("sync_run_unavailable", None, "unavailable", {"queued": self.summary()["queued"]})
            self._save()
            return SyncBatchResult(SyncStatus.UNAVAILABLE, 0, 0, 0, self.summary()["conflicts"], (result,))
        eligible = [item for item in self._items() if item.status == SyncStatus.QUEUED.value][: self.limits.maximum_batch_size]
        results: list[SyncResult] = []
        synced = failed = conflicts = 0
        for item in eligible:
            second_check = self.evaluate_policy(item.item_type, item.sanitized_payload)
            if not second_check.allowed:
                self._update_item(item.sync_item_id, status=SyncStatus.BLOCKED_BY_POLICY.value, last_error_code=second_check.error_code, updated_at=_now())
                results.append(SyncResult(SyncStatus.BLOCKED_BY_POLICY, second_check.reason, item.sync_item_id, second_check.error_code))
                failed += 1
                continue
            try:
                result = adapter.upload(item)
            except TimeoutError:
                result = SyncResult(SyncStatus.FAILED, "Remote sync timed out; the item remains local.", item.sync_item_id, "timeout", True)
            except Exception:
                result = SyncResult(SyncStatus.FAILED, "Remote sync failed safely; the item remains local.", item.sync_item_id, "adapter_failure", False)
            results.append(result)
            if result.status is SyncStatus.SYNCED:
                self._update_item(item.sync_item_id, status=SyncStatus.SYNCED.value, provider_id=adapter.provider_info.provider_id, updated_at=_now())
                self._store["last_successful_sync"] = _now()
                synced += 1
            elif result.status is SyncStatus.CONFLICT:
                conflicts += 1
            else:
                attempts = item.attempt_count + 1
                retry_at = (_now_dt() + timedelta(seconds=min(300, 2 ** attempts * 5))).isoformat() if attempts < item.maximum_attempts and result.retryable else None
                self._update_item(item.sync_item_id, status=SyncStatus.FAILED.value, attempt_count=attempts, next_retry_at=retry_at, last_error_code=result.error_code, updated_at=_now())
                failed += 1
        self._audit("sync_run_completed", None, "synced" if synced and not failed else "failed", {"processed": len(eligible), "synced": synced, "failed": failed})
        self._save()
        status = SyncStatus.SYNCED if synced and not failed else SyncStatus.FAILED
        return SyncBatchResult(status, len(eligible), synced, failed, conflicts, tuple(results))

    def detect_conflict(self, sync_item_id: str, remote_hash: str, remote_version: int) -> SyncConflict | None:
        item = self.inspect(sync_item_id)
        if item is None or (item.payload_hash == remote_hash and item.schema_version == remote_version):
            return None
        conflict = SyncConflict(str(uuid.uuid4()), sync_item_id, item.payload_hash, remote_hash, item.schema_version, remote_version, self.conflict_strategy.value, "unresolved", _now())
        self._store["conflicts"].append(asdict(conflict))
        self._update_item(sync_item_id, status=SyncStatus.CONFLICT.value, conflict_metadata={"conflict_id": conflict.conflict_id}, updated_at=_now())
        self._audit("sync_conflict_detected", sync_item_id, "conflict", {"conflict_id": conflict.conflict_id})
        self._save()
        return conflict

    def conflicts(self) -> tuple[SyncConflict, ...]:
        return tuple(SyncConflict(**item) for item in self._store.get("conflicts", ()))

    def cleanup(self) -> dict[str, int]:
        terminal = {SyncStatus.SYNCED.value, SyncStatus.CANCELLED.value, SyncStatus.BLOCKED_BY_POLICY.value}
        items = self._items()
        completed = [item for item in items if item.status in terminal]
        retained_completed = completed[-self.limits.completed_retention_count :] if self.limits.completed_retention_count else []
        keep_ids = {item.sync_item_id for item in retained_completed}
        kept = [asdict(item) for item in items if item.status not in terminal or item.sync_item_id in keep_ids]
        removed = len(items) - len(kept)
        self._store["items"] = kept
        self._store["audit"] = self._store.get("audit", [])[-self.limits.audit_retention_count :]
        self._save()
        return {"removed": removed, "remaining": len(kept), "audit_events": len(self._store["audit"])}

    def summary(self) -> dict[str, int]:
        items = self._items() if self._store else []
        return {
            "total": len(items),
            "queued": sum(item.status == SyncStatus.QUEUED.value for item in items),
            "failed": sum(item.status == SyncStatus.FAILED.value for item in items),
            "synced": sum(item.status == SyncStatus.SYNCED.value for item in items),
            "cancelled": sum(item.status == SyncStatus.CANCELLED.value for item in items),
            "conflicts": len(self._store.get("conflicts", ())) if self._store else 0,
        }

    def audit_events(self) -> tuple[SyncAuditEvent, ...]:
        return tuple(SyncAuditEvent(**event) for event in self._store.get("audit", ()))

    def _sanitize(self, value: Any, depth: int) -> Any:
        if depth > self.limits.maximum_nested_depth:
            raise ValueError("Payload nesting exceeds the sync policy limit.")
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, bytes):
            raise ValueError("Binary data is not allowed in sync payloads.")
        if isinstance(value, str):
            if len(value) > self.limits.maximum_string_length:
                raise ValueError("A payload string exceeds the sync policy limit.")
            if _SECRET_VALUE.search(value) or _BASE64_BLOB.fullmatch(value):
                raise ValueError("Secret-shaped or encoded raw data is not allowed.")
            if Path(value).is_absolute() or PureWindowsPath(value).is_absolute():
                raise ValueError("Absolute local paths are not allowed in sync payloads.")
            return value.strip()
        if isinstance(value, list):
            return [self._sanitize(item, depth + 1) for item in value]
        if isinstance(value, dict):
            clean: dict[str, Any] = {}
            for key, item in value.items():
                if not isinstance(key, str) or _SECRET_KEY.search(key):
                    raise ValueError("Credential-like or invalid fields are not allowed.")
                clean[key] = self._sanitize(item, depth + 1)
            return clean
        raise ValueError("Only JSON-compatible structured values may be synchronized.")

    def _items(self) -> list[SyncItem]:
        return [SyncItem(**item) for item in self._store.get("items", ())]

    def _update_item(self, sync_item_id: str, **changes: Any) -> None:
        for item in self._store.get("items", []):
            if item.get("sync_item_id") == sync_item_id:
                item.update(changes)
                return

    def _remote_adapter(self) -> SyncAdapter | None:
        selected = self.adapters.get(self.selected_adapter)
        if selected and selected.provider_info.remote:
            return selected
        return self.adapters.get("unavailable-remote")

    def _audit(self, event_type: str, sync_item_id: str | None, status: str, metadata: dict[str, Any] | None = None) -> None:
        event = SyncAuditEvent(str(uuid.uuid4()), event_type, sync_item_id, status, _now(), metadata or {})
        self._store.setdefault("audit", []).append(asdict(event))
        self._store["audit"] = self._store["audit"][-self.limits.audit_retention_count :]
        self.logger.info("sync_event event_type=%s sync_item_id=%s status=%s", event_type, sync_item_id or "none", status)

    def _load_store(self) -> dict[str, Any]:
        default = {"schema_version": 1, "mode": self.mode.value, "items": [], "conflicts": [], "audit": [], "last_successful_sync": None}
        if not self.queue_path.exists():
            return default
        try:
            value = json.loads(self.queue_path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or not all(isinstance(value.get(key), list) for key in ("items", "conflicts", "audit")):
                raise ValueError("invalid queue schema")
            return {**default, **value}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            quarantine = self.storage_dir / f"queue.corrupt-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.json"
            try:
                self.queue_path.replace(quarantine)
            except OSError:
                pass
            return default

    def _load_installation_id(self) -> str:
        if self.installation_path.exists():
            try:
                value = json.loads(self.installation_path.read_text(encoding="utf-8"))["installation_id"]
                return str(uuid.UUID(value))
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                pass
        identifier = str(uuid.uuid4())
        self._atomic_write(self.installation_path, {"installation_id": identifier})
        return identifier

    def _save(self) -> None:
        self._store["mode"] = self.mode.value
        self._store["items"] = self._store.get("items", [])[-self.limits.maximum_queue_items :]
        self._atomic_write(self.queue_path, self._store)

    @staticmethod
    def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)


def _now_dt() -> datetime:
    return datetime.now(UTC)
