"""Manager for local-first video editing workflow planning."""

from __future__ import annotations

import re
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from .models import (
    ProviderAvailabilityStatus,
    VideoEditingJobStatus,
    VideoEditingRequest,
    VideoEditingResult,
)
from .providers import StubVideoProvider, UnavailableVideoProvider, VideoProviderRegistry
from .safety import VideoEditingSafetyPolicy
from .storage import VideoEditingStorage


def _coerce_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


class VideoEditingManager:
    """Safe command-facing foundation for governed video editing."""

    def __init__(self, storage_dir: Path, settings: object | None = None, provider_registry: VideoProviderRegistry | None = None) -> None:
        config = getattr(settings, "video_editing", None) or SimpleNamespace()
        self.enabled = _coerce_bool(getattr(config, "enabled", False), False)
        self.default_provider = str(getattr(config, "default_provider", "unavailable") or "unavailable")
        self.local_only = _coerce_bool(getattr(config, "local_only", True), True)
        self.max_prompt_chars = int(getattr(config, "max_prompt_chars", 600))
        self.max_source_media_items = int(getattr(config, "max_source_media_items", 12))
        self.save_metadata = _coerce_bool(getattr(config, "save_metadata", True), True)
        self.allow_overwrite = _coerce_bool(getattr(config, "allow_overwrite", False), False)
        self.safety_filter_enabled = _coerce_bool(getattr(config, "safety_filter_enabled", True), True)
        configured_output_dir = getattr(config, "output_dir", None)
        self.storage = VideoEditingStorage(
            Path(configured_output_dir) if configured_output_dir else storage_dir,
            save_metadata=self.save_metadata,
            allow_overwrite=self.allow_overwrite,
        )
        self.safety_policy = VideoEditingSafetyPolicy(
            max_prompt_chars=self.max_prompt_chars,
            max_source_media_items=self.max_source_media_items,
        )
        self.providers = provider_registry or VideoProviderRegistry((UnavailableVideoProvider(),))
        self.initialized = True

    def status(self) -> dict[str, object]:
        selected = self.providers.select(self.default_provider).status()
        return {
            "enabled": self.enabled,
            "local_only": self.local_only,
            "default_provider": self.default_provider,
            "provider_status": selected.status.value,
            "provider_reason": selected.reason or "",
            "output_policy": "data/video_editing",
            "allow_overwrite": self.allow_overwrite,
            "save_metadata": self.save_metadata,
            "safety_filter_enabled": self.safety_filter_enabled,
        }

    def list_providers(self) -> tuple[dict[str, object], ...]:
        return tuple(asdict(item) for item in self.providers.list_status())

    def evaluate_safety(self, prompt: str, source_media: tuple[str, ...] = ()) -> object:
        if not self.safety_filter_enabled:
            return self.safety_policy.assess(prompt[: self.max_prompt_chars], source_media[: self.max_source_media_items])
        return self.safety_policy.assess(prompt, source_media)

    def plan(self, prompt: str, *, source_media: tuple[str, ...] = (), provider: str | None = None, dry_run: bool = True) -> VideoEditingResult:
        request = self._build_request(prompt, source_media=source_media, provider=provider, dry_run=dry_run)
        return self._execute(request)

    def history(self, limit: int = 5) -> tuple[dict[str, object], ...]:
        rows = []
        for item in self.storage.load_history(limit):
            rows.append(
                {
                    "plan_id": item.get("plan_id"),
                    "status": item.get("status"),
                    "provider": item.get("provider"),
                    "prompt_preview": item.get("prompt_preview"),
                    "created_at": item.get("created_at"),
                    "dry_run": bool(item.get("dry_run", False)),
                }
            )
        return tuple(rows)

    def show(self, plan_id: str) -> dict[str, object] | None:
        record = self.storage.load_plan(plan_id)
        if record is None:
            return None
        return {
            "plan_id": record.get("plan_id"),
            "status": record.get("status"),
            "provider": record.get("provider"),
            "source_media": tuple(record.get("source_media", ())),
            "plan_steps": tuple(record.get("plan_steps", ())),
            "deliverables": tuple(record.get("deliverables", ())),
            "prompt_preview": record.get("prompt_preview"),
            "created_at": record.get("created_at"),
            "dry_run": bool(record.get("dry_run", False)),
            "safety_status": record.get("safety_status"),
        }

    def _build_request(self, prompt: str, *, source_media: tuple[str, ...] = (), provider: str | None = None, dry_run: bool = True) -> VideoEditingRequest:
        cleaned = " ".join(prompt.split())
        return VideoEditingRequest(
            prompt=cleaned,
            source_media=tuple(" ".join(item.split()) for item in source_media),
            provider=provider or self.default_provider,
            dry_run=dry_run,
            local_only=self.local_only,
        )

    def _execute(self, request: VideoEditingRequest) -> VideoEditingResult:
        plan_id = self._plan_id(request.prompt)
        safety = self.evaluate_safety(request.prompt, request.source_media)
        if not safety.allowed:
            return VideoEditingResult(
                plan_id=plan_id,
                status=VideoEditingJobStatus.BLOCKED,
                provider=request.provider or self.default_provider,
                message=safety.reason,
                prompt_preview=self._prompt_preview(request.prompt),
                source_media=request.source_media,
                warnings=((f"Try instead: {safety.safe_alternative}",) if safety.safe_alternative else ()),
                error="prompt_blocked",
                dry_run=request.dry_run,
                metadata={"severity": safety.severity},
            )
        if not self.enabled:
            return VideoEditingResult(
                plan_id=plan_id,
                status=VideoEditingJobStatus.DISABLED,
                provider=request.provider or self.default_provider,
                message="Video editing is disabled in local configuration.",
                prompt_preview=self._prompt_preview(request.prompt),
                source_media=request.source_media,
                error="video_editing_disabled",
                dry_run=request.dry_run,
            )
        provider = self.providers.select(request.provider or self.default_provider)
        provider_status = provider.status()
        if request.local_only and not provider_status.local:
            return VideoEditingResult(
                plan_id=plan_id,
                status=VideoEditingJobStatus.BLOCKED,
                provider=provider_status.provider_name,
                message="The selected provider is blocked by local-only policy.",
                prompt_preview=self._prompt_preview(request.prompt),
                source_media=request.source_media,
                error="local_only_blocked",
                dry_run=request.dry_run,
            )
        if provider_status.status is not ProviderAvailabilityStatus.READY:
            return VideoEditingResult(
                plan_id=plan_id,
                status=VideoEditingJobStatus.UNAVAILABLE,
                provider=provider_status.provider_name,
                message=provider_status.reason or "No real local video editing provider is available.",
                prompt_preview=self._prompt_preview(request.prompt),
                source_media=request.source_media,
                error="provider_unavailable",
                dry_run=request.dry_run,
                metadata={
                    "provider_status": provider_status.status.value,
                    "local_only": request.local_only,
                    "output_dir": "data/video_editing",
                },
            )
        planned = provider.plan(request, self.storage, plan_id)
        return self._persist_result(
            VideoEditingResult(
                plan_id=planned.plan_id,
                status=planned.status,
                provider=planned.provider,
                message=planned.message,
                prompt_preview=planned.prompt_preview,
                source_media=planned.source_media,
                plan_steps=planned.plan_steps,
                deliverables=planned.deliverables,
                warnings=planned.warnings,
                error=planned.error,
                dry_run=planned.dry_run,
                metadata=planned.metadata,
                created_at=planned.created_at,
            )
        )

    def _persist_result(self, result: VideoEditingResult) -> VideoEditingResult:
        record = {
            "plan_id": result.plan_id,
            "status": result.status.value,
            "provider": result.provider,
            "source_media": result.source_media,
            "plan_steps": result.plan_steps,
            "deliverables": result.deliverables,
            "prompt_preview": result.prompt_preview,
            "created_at": result.created_at,
            "dry_run": result.dry_run,
            "safety_status": result.metadata.get("safety_status", "allowed"),
        }
        metadata_path = self.storage.record(record)
        if metadata_path and result.metadata.get("metadata_path") is None:
            return replace(result, metadata_path=metadata_path)
        return result

    @staticmethod
    def _plan_id(prompt: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        slug = re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")[:18] or "video"
        return f"vid-{timestamp}-{slug}"

    @staticmethod
    def _prompt_preview(prompt: str) -> str:
        compact = " ".join(prompt.split())
        return compact[:120]
