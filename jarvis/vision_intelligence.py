"""Local-first image validation and provider-neutral vision execution."""

from __future__ import annotations

import asyncio
import base64
import logging
import struct
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Protocol
from uuid import uuid4

from providers.provider_router import ProviderSelectionContext
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


class VisionAdapter(Protocol):
    def providers(self, local_only: bool = True) -> tuple[VisionProviderInfo, ...]: ...
    def execute(self, request: VisionRequest, image_bytes: bytes, metadata: Mapping[str, Any]) -> VisionResult: ...


class ProviderVisionAdapter:
    """Translate validated vision work into the existing Provider Router contract."""

    def __init__(self, provider_manager: Any) -> None:
        self.provider_manager = provider_manager

    def providers(self, local_only: bool = True) -> tuple[VisionProviderInfo, ...]:
        items: list[VisionProviderInfo] = []
        if self.provider_manager is None:
            return ()
        for record in self.provider_manager.registry.all():
            provider = record.provider
            if provider is None or not provider.enabled or not provider.initialized:
                continue
            local = bool(record.config.local_only)
            if local_only and not local:
                continue
            verified_input = provider.kind.value == "ollama" or bool(record.config.metadata.get("vision_input_supported", False))
            if not verified_input:
                continue
            models = tuple(model for model in provider.list_models() if ProviderCapability.VISION in model.capabilities)
            if provider.capabilities().supports(ProviderCapability.VISION) and models:
                for model in models:
                    items.append(VisionProviderInfo(provider.provider_id, model.model_id, local, provider.is_available(), tuple(cap.value for cap in model.capabilities)))
        return tuple(items)

    def execute(self, request: VisionRequest, image_bytes: bytes, metadata: Mapping[str, Any]) -> VisionResult:
        candidates = self.providers(request.local_only)
        if request.preferred_provider:
            candidates = tuple(item for item in candidates if item.provider_id == request.preferred_provider)
        if request.preferred_model:
            candidates = tuple(item for item in candidates if item.model_id == request.preferred_model)
        if not candidates:
            return VisionResult(request.request_id, VisionStatus.UNAVAILABLE, error="No permitted vision-capable provider is available.", metadata=metadata)
        selected = candidates[0]
        provider_request = ProviderRequest(
            prompt=request.prompt,
            task_type=ProviderTaskType.VISION,
            model=selected.model_id,
            request_id=request.request_id,
            preferred_provider=selected.provider_id,
            local_only=request.local_only,
            timeout_seconds=request.timeout_seconds,
            required_capabilities=(ProviderCapability.VISION,),
            metadata={"local_only": request.local_only, "execution_policy": "local_only" if request.local_only else "automatic", "allowed_provider_ids": (selected.provider_id,), "images": (base64.b64encode(image_bytes).decode("ascii"),), "image_metadata": dict(metadata)},
        )
        try:
            response = asyncio.run(self.provider_manager.router.execute_with_failover(provider_request))
        except LookupError:
            return VisionResult(request.request_id, VisionStatus.UNAVAILABLE, error="No permitted vision-capable provider is available.", metadata=metadata)
        except TimeoutError:
            return VisionResult(request.request_id, VisionStatus.TIMED_OUT, error="Vision analysis timed out.", metadata=metadata)
        except Exception:
            return VisionResult(request.request_id, VisionStatus.FAILED, error="Vision provider execution failed.", metadata=metadata)
        if response.error:
            return VisionResult(request.request_id, VisionStatus.FAILED, metadata=metadata, provider_id=response.provider_id, model_id=response.model, error=response.error)
        return VisionResult(request.request_id, VisionStatus.COMPLETED, response.content, metadata, response.provider_id, response.model)


class VisionIntelligence:
    """Validate images and delegate analysis without retaining image content."""

    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

    def __init__(self, settings: Any = None, provider_manager: Any = None, logger: logging.Logger | None = None) -> None:
        config = getattr(settings, "vision", None)
        self.settings = settings
        self.enabled = bool(getattr(config, "enabled", True))
        self.local_only = bool(getattr(config, "local_only", True))
        self.privacy_mode = str(getattr(config, "privacy_mode", "standard"))
        self.max_image_size = int(getattr(config, "max_image_size", 20_000_000))
        self.timeout_seconds = int(getattr(config, "timeout_seconds", 60))
        self.allowed_directories = tuple(Path(path).resolve() for path in (getattr(config, "allowed_directories", ()) or ()))
        self.base_dir = Path(getattr(settings, "base_dir", Path.cwd())).resolve()
        self.adapter = ProviderVisionAdapter(provider_manager)
        self.logger = logger or logging.getLogger("vision_intelligence")
        self.initialized = True

    def status(self, local_only: bool | None = None) -> dict[str, Any]:
        policy = self.local_only if local_only is None else local_only
        providers = self.adapter.providers(policy) if self.enabled else ()
        return {"enabled": self.enabled, "local_only": policy, "privacy_mode": self.privacy_mode, "available": bool(providers), "providers": providers, "max_image_size": self.max_image_size, "raw_image_persistence": False}

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
        try:
            metadata = self.validate_image(path_text)
        except ValueError as exc:
            return VisionResult(request_id, VisionStatus.INVALID_INPUT, error=str(exc))
        policy = self.local_only if local_only is None else local_only
        if not self.enabled:
            return VisionResult(request_id, VisionStatus.UNAVAILABLE, metadata=self._public_metadata(metadata), error="Vision Intelligence is disabled.")
        if not question.strip():
            return VisionResult(request_id, VisionStatus.INVALID_INPUT, metadata=self._public_metadata(metadata), error="A vision question is required.")
        permitted = self.adapter.providers(policy)
        if policy and not permitted and self.adapter.providers(False):
            return VisionResult(request_id, VisionStatus.BLOCKED_BY_POLICY, metadata=self._public_metadata(metadata), error="Available vision providers are blocked by local-only policy.")
        if not permitted:
            return VisionResult(request_id, VisionStatus.UNAVAILABLE, metadata=self._public_metadata(metadata), error="No permitted vision-capable provider or model is available.")
        request = VisionRequest(request_id, str(metadata["path"]), question.strip(), policy, preferred_provider, preferred_model, self.privacy_mode, self.timeout_seconds)
        result = self.adapter.execute(request, Path(metadata["path"]).read_bytes(), self._public_metadata(metadata))
        self.logger.info("vision_analysis_completed request_id=%s status=%s provider_id=%s model_id=%s", request_id, result.status.value, result.provider_id, result.model_id)
        return result

    @staticmethod
    def _public_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in metadata.items() if key != "path"}

    @staticmethod
    def _valid_signature(data: bytes, extension: str) -> bool:
        if extension == ".png": return data[:8] == b"\x89PNG\r\n\x1a\n"
        if extension in {".jpg", ".jpeg"}: return data[:2] == b"\xff\xd8"
        if extension == ".bmp": return data[:2] == b"BM"
        if extension == ".webp": return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
        return False

    @staticmethod
    def _dimensions(data: bytes, extension: str) -> tuple[int | None, int | None]:
        try:
            if extension == ".png" and data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
                return struct.unpack(">II", data[16:24])
            if extension == ".bmp" and data[:2] == b"BM" and len(data) >= 26:
                return struct.unpack("<ii", data[18:26])
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
