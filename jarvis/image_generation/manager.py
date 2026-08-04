"""Manager for local-first image generation workflow planning."""

from __future__ import annotations

import re
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from .models import (
    ImageGenerationJobStatus,
    ImageGenerationRequest,
    ImageGenerationResult,
    ProviderAvailabilityStatus,
)
from .providers import ImageProviderRegistry, StubImageProvider, UnavailableImageProvider
from .safety import ImageGenerationSafetyPolicy
from .storage import ImageGenerationStorage


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


class ImageGenerationManager:
    """Safe command-facing foundation for governed image generation."""

    def __init__(self, storage_dir: Path, settings: object | None = None, provider_registry: ImageProviderRegistry | None = None) -> None:
        config = getattr(settings, "image_generation", None) or SimpleNamespace()
        self.enabled = _coerce_bool(getattr(config, "enabled", False), False)
        self.default_provider = str(getattr(config, "default_provider", "unavailable") or "unavailable")
        self.local_only = _coerce_bool(getattr(config, "local_only", True), True)
        self.max_prompt_chars = int(getattr(config, "max_prompt_chars", 600))
        self.max_negative_prompt_chars = int(getattr(config, "max_negative_prompt_chars", 300))
        self.save_metadata = _coerce_bool(getattr(config, "save_metadata", True), True)
        self.allow_overwrite = _coerce_bool(getattr(config, "allow_overwrite", False), False)
        self.safety_filter_enabled = _coerce_bool(getattr(config, "safety_filter_enabled", True), True)
        configured_output_dir = getattr(config, "output_dir", None)
        self.storage = ImageGenerationStorage(
            Path(configured_output_dir) if configured_output_dir else storage_dir,
            save_metadata=self.save_metadata,
            allow_overwrite=self.allow_overwrite,
        )
        self.safety_policy = ImageGenerationSafetyPolicy(
            max_prompt_chars=self.max_prompt_chars,
            max_negative_prompt_chars=self.max_negative_prompt_chars,
        )
        self.providers = provider_registry or ImageProviderRegistry(
            (UnavailableImageProvider(),)
        )
        self.initialized = True

    def status(self) -> dict[str, object]:
        selected = self.providers.select(self.default_provider).status()
        return {
            "enabled": self.enabled,
            "local_only": self.local_only,
            "default_provider": self.default_provider,
            "provider_status": selected.status.value,
            "provider_reason": selected.reason or "",
            "output_policy": self.storage.public_path(self.storage.root) or "data/image_generation",
            "allow_overwrite": self.allow_overwrite,
            "save_metadata": self.save_metadata,
            "safety_filter_enabled": self.safety_filter_enabled,
        }

    def list_providers(self) -> tuple[dict[str, object], ...]:
        return tuple(asdict(item) for item in self.providers.list_status())

    def evaluate_safety(self, prompt: str, negative_prompt: str = ""):
        if not self.safety_filter_enabled:
            return self.safety_policy.assess(prompt[: self.max_prompt_chars], negative_prompt[: self.max_negative_prompt_chars])
        return self.safety_policy.assess(prompt, negative_prompt)

    def plan(self, prompt: str, *, negative_prompt: str = "", provider: str | None = None, dry_run: bool = True) -> ImageGenerationResult:
        request = self._build_request(prompt, negative_prompt=negative_prompt, provider=provider, dry_run=dry_run)
        return self._execute(request, generate=False)

    def generate(self, prompt: str, *, negative_prompt: str = "", provider: str | None = None, dry_run: bool = False) -> ImageGenerationResult:
        request = self._build_request(prompt, negative_prompt=negative_prompt, provider=provider, dry_run=dry_run)
        return self._execute(request, generate=not dry_run)

    def history(self, limit: int = 5) -> tuple[dict[str, object], ...]:
        rows = []
        for item in self.storage.load_history(limit):
            rows.append(
                {
                    "job_id": item.get("job_id"),
                    "status": item.get("status"),
                    "provider": item.get("provider"),
                    "prompt_preview": item.get("prompt_preview"),
                    "created_at": item.get("created_at"),
                    "dry_run": bool(item.get("dry_run", False)),
                }
            )
        return tuple(rows)

    def show(self, job_id: str) -> dict[str, object] | None:
        record = self.storage.load_job(job_id)
        if record is None:
            return None
        return {
            "job_id": record.get("job_id"),
            "status": record.get("status"),
            "provider": record.get("provider"),
            "output_paths": tuple(record.get("output_paths", ())),
            "metadata_path": record.get("metadata_path"),
            "prompt_preview": record.get("prompt_preview"),
            "created_at": record.get("created_at"),
            "dry_run": bool(record.get("dry_run", False)),
            "safety_status": record.get("safety_status"),
        }

    def _build_request(self, prompt: str, *, negative_prompt: str = "", provider: str | None = None, dry_run: bool = False) -> ImageGenerationRequest:
        cleaned = " ".join(prompt.split())
        cleaned_negative = " ".join(negative_prompt.split())
        return ImageGenerationRequest(
            prompt=cleaned,
            negative_prompt=cleaned_negative,
            provider=provider or self.default_provider,
            dry_run=dry_run,
            local_only=self.local_only,
        )

    def _execute(self, request: ImageGenerationRequest, *, generate: bool) -> ImageGenerationResult:
        job_id = self._job_id(request.prompt)
        safety = self.evaluate_safety(request.prompt, request.negative_prompt)
        if not safety.allowed:
            return ImageGenerationResult(
                job_id=job_id,
                status=ImageGenerationJobStatus.BLOCKED,
                provider=request.provider or self.default_provider,
                safety_status=safety.category,
                message=safety.reason,
                prompt_preview=self._prompt_preview(request.prompt),
                warnings=((f"Try instead: {safety.safe_alternative}",) if safety.safe_alternative else ()),
                error="prompt_blocked",
                dry_run=request.dry_run,
                metadata={"severity": safety.severity},
            )
        if not self.enabled:
            return ImageGenerationResult(
                job_id=job_id,
                status=ImageGenerationJobStatus.DISABLED,
                provider=request.provider or self.default_provider,
                safety_status="allowed",
                message="Image generation is disabled in local configuration.",
                prompt_preview=self._prompt_preview(request.prompt),
                error="image_generation_disabled",
                dry_run=request.dry_run,
            )
        provider = self.providers.select(request.provider or self.default_provider)
        provider_status = provider.status()
        if request.local_only and not provider_status.local:
            return ImageGenerationResult(
                job_id=job_id,
                status=ImageGenerationJobStatus.BLOCKED,
                provider=provider_status.provider_name,
                safety_status="allowed",
                message="The selected provider is blocked by local-only policy.",
                prompt_preview=self._prompt_preview(request.prompt),
                error="local_only_blocked",
                dry_run=request.dry_run,
            )
        if request.dry_run or not generate:
            return ImageGenerationResult(
                job_id=job_id,
                status=ImageGenerationJobStatus.PLANNED if provider_status.status is ProviderAvailabilityStatus.READY else ImageGenerationJobStatus.UNAVAILABLE,
                provider=provider_status.provider_name,
                safety_status="allowed",
                message=self._plan_message(provider_status),
                prompt_preview=self._prompt_preview(request.prompt),
                dry_run=True,
                metadata={
                    "provider_status": provider_status.status.value,
                    "local_only": request.local_only,
                    "output_dir": self.storage.public_path(self.storage.root) or "data/image_generation",
                },
            )
        result = provider.generate(request, self.storage, job_id)
        return self._persist_result(result)

    def _persist_result(self, result: ImageGenerationResult) -> ImageGenerationResult:
        record = {
            "job_id": result.job_id,
            "status": result.status.value,
            "provider": result.provider,
            "output_paths": result.output_paths,
            "metadata_path": result.metadata_path,
            "prompt_preview": result.prompt_preview,
            "created_at": result.created_at,
            "dry_run": result.dry_run,
            "safety_status": result.safety_status,
        }
        metadata_path = self.storage.record(record)
        if metadata_path and result.metadata_path is None:
            return replace(result, metadata_path=metadata_path)
        return result

    @staticmethod
    def _plan_message(provider_status) -> str:
        if provider_status.status is ProviderAvailabilityStatus.READY:
            return "Dry run complete. The request is allowed and a local provider is ready."
        return provider_status.reason or "Dry run complete. No real local image provider is available."

    def _job_id(self, prompt: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        slug = re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")[:18] or "image"
        return f"img-{timestamp}-{slug}"

    @staticmethod
    def _prompt_preview(prompt: str) -> str:
        compact = " ".join(prompt.split())
        return compact[:120]
