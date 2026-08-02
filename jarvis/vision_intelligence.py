"""Local-first image validation and provider-neutral vision execution."""

from __future__ import annotations

import asyncio
import base64
import ipaddress
import json
import logging
import os
import struct
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse
from uuid import uuid4

from providers.provider_types import ProviderCapability, ProviderRequest, ProviderTaskType


class VisionStatus(StrEnum):
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
    INVALID_INPUT = "invalid_input"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, slots=True)
class VisionProviderInfo:
    provider_id: str
    model_id: str | None
    local: bool
    available: bool
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VisionRequest:
    request_id: str
    image_path: str
    prompt: str
    local_only: bool = True
    preferred_provider: str | None = None
    preferred_model: str | None = None
    privacy_mode: str = "standard"
    timeout_seconds: int = 60


@dataclass(frozen=True, slots=True)
class VisionResult:
    request_id: str
    status: VisionStatus
    content: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    provider_id: str | None = None
    model_id: str | None = None
    error: str | None = None
    warnings: tuple[str, ...] = ()
    latency_ms: float = 0.0
    availability_status: str = "unknown"
    prompt_used: str = ""

    @property
    def success(self) -> bool:
        return self.status is VisionStatus.COMPLETED

    @property
    def response_text(self) -> str:
        return self.content


@dataclass(frozen=True, slots=True)
class VisionAuditEvent:
    audit_id: str
    request_id: str
    timestamp: str
    action: str
    status: str
    provider_id: str | None
    model_id: str | None
    image_name: str | None
    image_size: int
    prompt_category: str
    latency_ms: float
    error_code: str | None


class VisionAdapter(Protocol):
    def providers(self, local_only: bool = True) -> tuple[VisionProviderInfo, ...]: ...
    def execute(self, request: VisionRequest, image_bytes: bytes, metadata: Mapping[str, Any]) -> VisionResult: ...


class OllamaVisionAdapter:
    """Use the registered local Ollama provider through Provider Router."""

    def __init__(self, provider_manager: Any, configured_model: str = "llava", configured_host: str = "http://127.0.0.1:11434") -> None:
        self.provider_manager = provider_manager
        self.configured_model = configured_model.strip() or "llava"
        self.configured_host = configured_host.rstrip("/")

    @staticmethod
    def _model_matches(configured: str, installed: str) -> bool:
        return configured == installed or (":" not in configured and installed.split(":", 1)[0] == configured)

    @staticmethod
    def _local_endpoint(url: str) -> tuple[str, int] | None:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
            return None
        try:
            loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host == "localhost"
        if not loopback:
            return None
        return parsed.scheme, parsed.port or (443 if parsed.scheme == "https" else 80)

    def diagnostics(self) -> dict[str, Any]:
        base = {
            "provider": "ollama",
            "configured_model": self.configured_model,
            "ollama_available": False,
            "model_available": False,
            "availability_status": "ollama_not_configured",
            "installed_models": (),
            "vision_models": (),
            "providers": (),
        }
        if self.provider_manager is None:
            return base
        records = tuple(
            record for record in self.provider_manager.registry.all()
            if record.provider is not None and record.provider.kind.value == "ollama" and record.config.local_only
        )
        if not records:
            return base
        record = records[0]
        provider = record.provider
        provider_host = str(record.config.base_url or "").rstrip("/")
        configured_endpoint = self._local_endpoint(self.configured_host)
        if configured_endpoint is None or configured_endpoint != self._local_endpoint(provider_host):
            return {**base, "availability_status": "ollama_host_mismatch"}
        try:
            health = provider.health_check()
            models = tuple(provider.capabilities().models)
        except Exception:
            return {**base, "availability_status": "ollama_unavailable"}
        if not health.available:
            return {**base, "availability_status": "ollama_unavailable"}
        installed = tuple(item.model_id for item in models)
        vision = tuple(item.model_id for item in models if ProviderCapability.VISION in item.capabilities)
        selected = next((item for item in vision if self._model_matches(self.configured_model, item)), None)
        infos = () if selected is None else (
            VisionProviderInfo(provider.provider_id, selected, True, True, (ProviderCapability.VISION.value,)),
        )
        return {
            **base,
            "ollama_available": True,
            "model_available": selected is not None,
            "availability_status": "ready" if selected else "model_missing",
            "installed_models": installed,
            "vision_models": vision,
            "providers": infos,
        }

    def providers(self, local_only: bool = True) -> tuple[VisionProviderInfo, ...]:
        return tuple(self.diagnostics()["providers"])

    def execute(self, request: VisionRequest, image_bytes: bytes, metadata: Mapping[str, Any]) -> VisionResult:
        started = time.perf_counter()
        candidates = self.providers(request.local_only)
        if request.preferred_provider:
            candidates = tuple(item for item in candidates if item.provider_id == request.preferred_provider)
        if request.preferred_model:
            candidates = tuple(item for item in candidates if item.model_id and self._model_matches(request.preferred_model, item.model_id))
        if not candidates:
            state = self.diagnostics()["availability_status"]
            return VisionResult(request.request_id, VisionStatus.UNAVAILABLE, error="No permitted local Ollama vision model is available.", metadata=metadata, availability_status=state, prompt_used=request.prompt)
        selected = candidates[0]
        provider_request = ProviderRequest(
            prompt=request.prompt,
            task_type=ProviderTaskType.VISION,
            model=selected.model_id,
            request_id=request.request_id,
            preferred_provider=selected.provider_id,
            local_only=request.local_only,
            timeout_seconds=request.timeout_seconds,
            system_instructions="Describe only visible, non-sensitive content. Do not identify real people, infer sensitive traits, provide medical diagnoses, or claim legal or forensic certainty.",
            max_output_tokens=512,
            required_capabilities=(ProviderCapability.VISION,),
            metadata={"local_only": request.local_only, "execution_policy": "local_only" if request.local_only else "automatic", "allowed_provider_ids": (selected.provider_id,), "images": (base64.b64encode(image_bytes).decode("ascii"),), "image_metadata": dict(metadata)},
        )
        try:
            response = asyncio.run(self.provider_manager.router.execute_with_failover(provider_request))
        except LookupError:
            return VisionResult(request.request_id, VisionStatus.UNAVAILABLE, error="No permitted local Ollama vision model is available.", metadata=metadata, availability_status="unavailable", prompt_used=request.prompt)
        except TimeoutError:
            return VisionResult(request.request_id, VisionStatus.TIMED_OUT, error="Vision analysis timed out.", metadata=metadata, latency_ms=(time.perf_counter() - started) * 1000, availability_status="timed_out", prompt_used=request.prompt)
        except Exception:
            return VisionResult(request.request_id, VisionStatus.FAILED, error="Vision provider execution failed.", metadata=metadata, latency_ms=(time.perf_counter() - started) * 1000, availability_status="failed", prompt_used=request.prompt)
        if response.error:
            lowered = response.error.lower()
            status = VisionStatus.TIMED_OUT if "timed out" in lowered or "timeout" in lowered else VisionStatus.UNAVAILABLE if "model missing" in lowered or "unavailable" in lowered or "connection" in lowered else VisionStatus.FAILED
            safe_error = "Vision analysis timed out." if status is VisionStatus.TIMED_OUT else "The configured local Ollama vision model or service is unavailable." if status is VisionStatus.UNAVAILABLE else "Local Ollama vision analysis failed."
            return VisionResult(request.request_id, status, metadata=metadata, provider_id=response.provider_id, model_id=response.model, error=safe_error, latency_ms=(time.perf_counter() - started) * 1000, availability_status=status.value, prompt_used=request.prompt)
        if not response.content.strip():
            return VisionResult(request.request_id, VisionStatus.FAILED, metadata=metadata, provider_id=response.provider_id, model_id=response.model, error="Vision model returned no response content.", latency_ms=(time.perf_counter() - started) * 1000, availability_status="failed", prompt_used=request.prompt)
        return VisionResult(request.request_id, VisionStatus.COMPLETED, response.content, metadata, response.provider_id, response.model, warnings=("Local model output is probabilistic; verify important details.",), latency_ms=(time.perf_counter() - started) * 1000, availability_status="ready", prompt_used=request.prompt)


class VisionIntelligence:
    """Validate images and delegate analysis without retaining image content."""

    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}

    _blocked_question_markers = {
        "face recognition": "identity_recognition_blocked",
        "identify this person": "identity_recognition_blocked",
        "who is this person": "identity_recognition_blocked",
        "diagnose": "medical_diagnosis_blocked",
        "medical diagnosis": "medical_diagnosis_blocked",
        "forensic certainty": "forensic_certainty_blocked",
        "legal certainty": "legal_certainty_blocked",
        "infer their race": "sensitive_trait_inference_blocked",
        "infer their religion": "sensitive_trait_inference_blocked",
        "infer their sexuality": "sensitive_trait_inference_blocked",
    }

    def __init__(self, settings: Any = None, provider_manager: Any = None, logger: logging.Logger | None = None, storage_dir: str | Path | None = None) -> None:
        config = getattr(settings, "vision", None)
        self.settings = settings
        self.enabled = bool(getattr(config, "enabled", True))
        self.local_only = bool(getattr(config, "local_only", True))
        self.privacy_mode = str(getattr(config, "privacy_mode", "standard"))
        self.max_image_size = int(getattr(config, "max_image_size", 20_000_000))
        self.timeout_seconds = int(getattr(config, "timeout_seconds", 60))
        self.provider = str(getattr(config, "provider", "ollama"))
        self.model = str(getattr(config, "model", "llava"))
        self.ollama_host = str(getattr(config, "ollama_host", "http://127.0.0.1:11434"))
        self.audit_enabled = bool(getattr(config, "audit_enabled", True))
        self.audit_retention = min(200, max(1, int(getattr(config, "audit_retention", 100))))
        self.store_image_content = bool(getattr(config, "store_image_content", False))
        self.allowed_directories = tuple(Path(path).resolve() for path in (getattr(config, "allowed_directories", ()) or ()))
        self.base_dir = Path(getattr(settings, "base_dir", Path.cwd())).resolve()
        self.adapter = OllamaVisionAdapter(provider_manager, self.model, self.ollama_host)
        self.logger = logger or logging.getLogger("vision_intelligence")
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.audit_path = self.storage_dir / "audit.json" if self.storage_dir else None
        self._audit = self._load_audit()
        self.initialized = True

    def status(self, local_only: bool | None = None) -> dict[str, Any]:
        policy = self.local_only if local_only is None else local_only
        diagnostics = self.adapter.diagnostics() if self.enabled and hasattr(self.adapter, "diagnostics") else {}
        providers = tuple(diagnostics.get("providers", self.adapter.providers(policy) if self.enabled else ()))
        return {"enabled": self.enabled, "local_only": policy, "privacy_mode": self.privacy_mode, "available": bool(providers), "providers": providers, "provider": self.provider, "configured_model": self.model, "ollama_available": bool(diagnostics.get("ollama_available", False)), "model_available": bool(diagnostics.get("model_available", False)), "availability_status": diagnostics.get("availability_status", "ready" if providers else "unavailable"), "installed_models": tuple(diagnostics.get("installed_models", ())), "vision_models": tuple(diagnostics.get("vision_models", ())), "max_image_size": self.max_image_size, "raw_image_persistence": False, "store_image_content": False, "audit_events": len(self._audit)}

    def models(self) -> dict[str, Any]:
        status = self.status(True)
        return {key: status[key] for key in ("provider", "configured_model", "ollama_available", "model_available", "availability_status", "installed_models", "vision_models")}

    def validate_image(self, path_text: str) -> dict[str, Any]:
        path = Path(path_text).expanduser().resolve()
        roots = self.allowed_directories or (self.base_dir,)
        if not any(path == root or root in path.parents for root in roots):
            raise ValueError("image_path_outside_allowed_scope")
        if not path.exists() or not path.is_file():
            raise ValueError("image_not_found")
        if path.suffix.lower() not in self.allowed_extensions:
            raise ValueError("unsupported_image_format")
        size = path.stat().st_size
        if size <= 0:
            raise ValueError("empty_image")
        if size > self.max_image_size:
            raise ValueError("image_too_large")
        data = path.read_bytes()
        if not self._valid_signature(data, path.suffix.lower()):
            raise ValueError("invalid_image_signature")
        width, height = self._dimensions(data, path.suffix.lower())
        return {"file_name": path.name, "extension": path.suffix.lower().lstrip("."), "file_size": size, "modified_at": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(), "width": width, "height": height, "path": path}

    def analyze(self, path_text: str, question: str = "Describe this image.", *, local_only: bool | None = None, preferred_provider: str | None = None, preferred_model: str | None = None) -> VisionResult:
        request_id = str(uuid4())
        started = time.perf_counter()
        try:
            metadata = self.validate_image(path_text)
        except ValueError as exc:
            result = VisionResult(request_id, VisionStatus.INVALID_INPUT, error=str(exc), availability_status="invalid_input")
            self._record("analyze", result, Path(path_text).name, 0, "validation", started)
            return result
        policy = self.local_only if local_only is None else local_only
        if not self.enabled:
            result = VisionResult(request_id, VisionStatus.UNAVAILABLE, metadata=self._public_metadata(metadata), error="Vision Intelligence is disabled.", availability_status="disabled")
            self._record("analyze", result, metadata["file_name"], metadata["file_size"], "general", started)
            return result
        if not question.strip():
            result = VisionResult(request_id, VisionStatus.INVALID_INPUT, metadata=self._public_metadata(metadata), error="A vision question is required.", availability_status="invalid_input")
            self._record("ask", result, metadata["file_name"], metadata["file_size"], "empty", started)
            return result
        if len(question.strip()) > 2_000:
            result = VisionResult(request_id, VisionStatus.INVALID_INPUT, metadata=self._public_metadata(metadata), error="vision_question_too_long", availability_status="invalid_input")
            self._record("ask", result, metadata["file_name"], metadata["file_size"], "validation", started)
            return result
        blocked_reason = self._blocked_question(question)
        if blocked_reason:
            result = VisionResult(request_id, VisionStatus.BLOCKED_BY_POLICY, metadata=self._public_metadata(metadata), error=blocked_reason, availability_status="blocked_by_policy")
            self._record("ask", result, metadata["file_name"], metadata["file_size"], "blocked", started)
            return result
        permitted = self.adapter.providers(policy)
        if policy and not permitted and self.adapter.providers(False):
            result = VisionResult(request_id, VisionStatus.BLOCKED_BY_POLICY, metadata=self._public_metadata(metadata), error="Available vision providers are blocked by local-only policy.", availability_status="blocked_by_policy")
            self._record("analyze", result, metadata["file_name"], metadata["file_size"], "general", started)
            return result
        if not permitted:
            diagnostics = self.adapter.diagnostics() if hasattr(self.adapter, "diagnostics") else {}
            state = str(diagnostics.get("availability_status", "unavailable"))
            result = VisionResult(request_id, VisionStatus.UNAVAILABLE, metadata=self._public_metadata(metadata), error="No permitted local Ollama vision model is available.", availability_status=state)
            self._record("analyze", result, metadata["file_name"], metadata["file_size"], "general", started)
            return result
        request = VisionRequest(request_id, str(metadata["path"]), question.strip(), policy, preferred_provider or "ollama", preferred_model or self.model, self.privacy_mode, self.timeout_seconds)
        result = self.adapter.execute(request, Path(metadata["path"]).read_bytes(), self._public_metadata(metadata))
        self._record("ask" if question.strip() != "Describe this image." else "describe", result, metadata["file_name"], metadata["file_size"], "general", started)
        self.logger.info("vision_analysis_completed request_id=%s status=%s provider_id=%s model_id=%s", request_id, result.status.value, result.provider_id, result.model_id)
        return result

    def audit_events(self) -> tuple[VisionAuditEvent, ...]:
        return tuple(self._audit)

    def cleanup(self) -> dict[str, int]:
        removed = len(self._audit)
        self._audit.clear()
        if self.audit_path and self.audit_path.exists():
            try:
                self.audit_path.unlink()
            except OSError:
                return {"removed": 0, "remaining": removed, "failed": 1}
        return {"removed": removed, "remaining": 0, "failed": 0}

    def _record(self, action: str, result: VisionResult, image_name: str | None, image_size: int, prompt_category: str, started: float) -> None:
        if not self.audit_enabled:
            return
        event = VisionAuditEvent(str(uuid4()), result.request_id, datetime.now(UTC).isoformat(), action, result.status.value, result.provider_id, result.model_id, image_name, image_size, prompt_category, round(result.latency_ms or (time.perf_counter() - started) * 1000, 3), self._error_code(result))
        self._audit.append(event)
        self._audit = self._audit[-self.audit_retention:]
        self._save_audit()

    def _load_audit(self) -> list[VisionAuditEvent]:
        if not self.audit_path or not self.audit_path.exists():
            return []
        try:
            payload = json.loads(self.audit_path.read_text(encoding="utf-8"))
            return [VisionAuditEvent(**item) for item in payload.get("events", [])][-self.audit_retention:]
        except (OSError, ValueError, TypeError):
            return []

    def _save_audit(self) -> None:
        if not self.audit_path:
            return
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.audit_path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump({"schema_version": 1, "events": [asdict(item) for item in self._audit]}, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.audit_path)

    @classmethod
    def _blocked_question(cls, question: str) -> str | None:
        lowered = " ".join(question.lower().split())
        return next((reason for marker, reason in cls._blocked_question_markers.items() if marker in lowered), None)

    @staticmethod
    def _error_code(result: VisionResult) -> str | None:
        if not result.error:
            return None
        normalized = result.error.strip().upper()
        if normalized.replace("_", "").isalnum() and len(normalized) <= 64:
            return normalized
        if result.status is VisionStatus.TIMED_OUT:
            return "VISION_TIMEOUT"
        if result.status is VisionStatus.BLOCKED_BY_POLICY:
            return "VISION_POLICY_BLOCKED"
        if result.status is VisionStatus.UNAVAILABLE:
            return "VISION_UNAVAILABLE"
        if result.status is VisionStatus.INVALID_INPUT:
            return "VISION_INVALID_INPUT"
        return "VISION_FAILED"

    @staticmethod
    def _public_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in metadata.items() if key != "path"}

    @staticmethod
    def _valid_signature(data: bytes, extension: str) -> bool:
        if extension == ".png": return data[:8] == b"\x89PNG\r\n\x1a\n"
        if extension in {".jpg", ".jpeg"}: return data[:2] == b"\xff\xd8"
        if extension == ".webp": return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
        return False

    @staticmethod
    def _dimensions(data: bytes, extension: str) -> tuple[int | None, int | None]:
        try:
            if extension == ".png" and data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
                return struct.unpack(">II", data[16:24])
            if extension == ".webp" and data[:4] == b"RIFF" and data[8:12] == b"WEBP" and data[12:16] == b"VP8X" and len(data) >= 30:
                return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
            if extension in {".jpg", ".jpeg"} and data[:2] == b"\xff\xd8":
                index = 2
                while index + 9 < len(data):
                    if data[index] != 0xFF: index += 1; continue
                    marker = data[index + 1]; length = int.from_bytes(data[index + 2:index + 4], "big")
                    if marker in range(0xC0, 0xC4): return int.from_bytes(data[index + 7:index + 9], "big"), int.from_bytes(data[index + 5:index + 7], "big")
                    index += max(2, length + 2)
        except (IndexError, struct.error, ValueError):
            pass
        return None, None
