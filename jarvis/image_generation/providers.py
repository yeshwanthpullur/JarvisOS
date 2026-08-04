"""Provider abstractions for image generation."""

from __future__ import annotations

import base64
from dataclasses import asdict
from pathlib import Path
from typing import Protocol

from .models import (
    ImageGenerationJobStatus,
    ImageGenerationRequest,
    ImageGenerationResult,
    ImageProviderStatus,
    ProviderAvailabilityStatus,
)
from .storage import ImageGenerationStorage


class ImageProvider(Protocol):
    provider_name: str
    local: bool

    def status(self) -> ImageProviderStatus: ...
    def generate(self, request: ImageGenerationRequest, storage: ImageGenerationStorage, job_id: str) -> ImageGenerationResult: ...


class LocalImageProvider:
    """Base contract for future local image model providers."""

    provider_name = "local"
    local = True

    def status(self) -> ImageProviderStatus:
        return ImageProviderStatus(
            provider_name=self.provider_name,
            status=ProviderAvailabilityStatus.NOT_CONFIGURED,
            local=True,
            model=None,
            reason="No local image model provider is configured yet.",
        )

    def generate(self, request: ImageGenerationRequest, storage: ImageGenerationStorage, job_id: str) -> ImageGenerationResult:
        return ImageGenerationResult(
            job_id=job_id,
            status=ImageGenerationJobStatus.UNAVAILABLE,
            provider=self.provider_name,
            safety_status="allowed",
            message="No real local image generation provider is configured.",
            prompt_preview=request.prompt[:120],
            error="provider_unavailable",
            dry_run=request.dry_run,
        )


class UnavailableImageProvider(LocalImageProvider):
    """Truthful default provider when no real local generator exists."""

    provider_name = "unavailable"

    def __init__(self, reason: str = "No local image generation model is configured.") -> None:
        self.reason = reason

    def status(self) -> ImageProviderStatus:
        return ImageProviderStatus(
            provider_name=self.provider_name,
            status=ProviderAvailabilityStatus.UNAVAILABLE,
            local=True,
            model=None,
            reason=self.reason,
        )

    def generate(self, request: ImageGenerationRequest, storage: ImageGenerationStorage, job_id: str) -> ImageGenerationResult:
        return ImageGenerationResult(
            job_id=job_id,
            status=ImageGenerationJobStatus.UNAVAILABLE,
            provider=self.provider_name,
            safety_status="allowed",
            message=self.reason,
            prompt_preview=request.prompt[:120],
            error="provider_unavailable",
            dry_run=request.dry_run,
        )


class StubImageProvider(LocalImageProvider):
    """Small local stub used only for bounded tests."""

    provider_name = "stub"

    _png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9pFVLQAAAABJRU5ErkJggg=="
    )

    def __init__(self, model: str = "stub-local-image-v1") -> None:
        self.model = model

    def status(self) -> ImageProviderStatus:
        return ImageProviderStatus(
            provider_name=self.provider_name,
            status=ProviderAvailabilityStatus.READY,
            local=True,
            model=self.model,
            reason="Stub image provider is ready for controlled tests.",
        )

    def generate(self, request: ImageGenerationRequest, storage: ImageGenerationStorage, job_id: str) -> ImageGenerationResult:
        output_path = storage.output_path(job_id, ".png")
        output_path.write_bytes(self._png_bytes)
        metadata = {
            "job_id": job_id,
            "provider": self.provider_name,
            "status": ImageGenerationJobStatus.COMPLETED.value,
            "dry_run": False,
            "output_paths": (storage.public_path(output_path),),
            "prompt_preview": request.prompt[:120],
        }
        metadata_path = storage.record(metadata)
        return ImageGenerationResult(
            job_id=job_id,
            status=ImageGenerationJobStatus.COMPLETED,
            provider=self.provider_name,
            output_paths=(storage.public_path(output_path) or output_path.name,),
            metadata_path=metadata_path,
            safety_status="allowed",
            message="A bounded local test image was generated.",
            prompt_preview=request.prompt[:120],
            dry_run=False,
            metadata={"provider_status": asdict(self.status())},
        )


class ImageProviderRegistry:
    """Bounded provider registry for local-first image generation."""

    def __init__(self, providers: tuple[ImageProvider, ...]) -> None:
        self._providers = {provider.provider_name: provider for provider in providers}

    def list_status(self) -> tuple[ImageProviderStatus, ...]:
        return tuple(provider.status() for provider in self._providers.values())

    def select(self, provider_name: str | None = None) -> ImageProvider:
        if provider_name and provider_name in self._providers:
            return self._providers[provider_name]
        if provider_name:
            return UnavailableImageProvider(f"The configured image provider '{provider_name}' is not registered.")
        return next(iter(self._providers.values()), UnavailableImageProvider())
