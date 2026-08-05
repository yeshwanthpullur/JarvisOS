"""Provider abstractions for video editing workflow planning."""

from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from .models import (
    ProviderAvailabilityStatus,
    VideoEditingJobStatus,
    VideoEditingPlan,
    VideoEditingRequest,
    VideoProviderStatus,
)
from .storage import VideoEditingStorage


class VideoProvider(Protocol):
    provider_name: str
    local: bool

    def status(self) -> VideoProviderStatus: ...

    def plan(self, request: VideoEditingRequest, storage: VideoEditingStorage, plan_id: str) -> VideoEditingPlan: ...


class LocalVideoProvider:
    """Base contract for future local video-editing providers."""

    provider_name = "local"
    local = True

    def status(self) -> VideoProviderStatus:
        return VideoProviderStatus(
            provider_name=self.provider_name,
            status=ProviderAvailabilityStatus.NOT_CONFIGURED,
            local=True,
            model=None,
            reason="No local video editing provider is configured yet.",
        )

    def plan(self, request: VideoEditingRequest, storage: VideoEditingStorage, plan_id: str) -> VideoEditingPlan:
        return VideoEditingPlan(
            plan_id=plan_id,
            status=VideoEditingJobStatus.UNAVAILABLE,
            provider=self.provider_name,
            message="No real local video editing provider is configured.",
            prompt_preview=request.prompt[:120],
            source_media=request.source_media,
            error="provider_unavailable",
            dry_run=request.dry_run,
        )


class UnavailableVideoProvider(LocalVideoProvider):
    """Truthful default provider when no real local editor exists."""

    provider_name = "unavailable"

    def __init__(self, reason: str = "No local video editing provider is configured.") -> None:
        self.reason = reason

    def status(self) -> VideoProviderStatus:
        return VideoProviderStatus(
            provider_name=self.provider_name,
            status=ProviderAvailabilityStatus.UNAVAILABLE,
            local=True,
            model=None,
            reason=self.reason,
        )

    def plan(self, request: VideoEditingRequest, storage: VideoEditingStorage, plan_id: str) -> VideoEditingPlan:
        return VideoEditingPlan(
            plan_id=plan_id,
            status=VideoEditingJobStatus.UNAVAILABLE,
            provider=self.provider_name,
            message=self.reason,
            prompt_preview=request.prompt[:120],
            source_media=request.source_media,
            error="provider_unavailable",
            dry_run=request.dry_run,
        )


class StubVideoProvider(LocalVideoProvider):
    """Small local stub used only for bounded tests."""

    provider_name = "stub"

    def __init__(self, model: str = "stub-local-video-v1") -> None:
        self.model = model

    def status(self) -> VideoProviderStatus:
        return VideoProviderStatus(
            provider_name=self.provider_name,
            status=ProviderAvailabilityStatus.READY,
            local=True,
            model=self.model,
            reason="Stub video provider is ready for controlled tests.",
        )

    def plan(self, request: VideoEditingRequest, storage: VideoEditingStorage, plan_id: str) -> VideoEditingPlan:
        plan_path = storage.plan_path(plan_id)
        payload = {
            "plan_id": plan_id,
            "provider": self.provider_name,
            "status": VideoEditingJobStatus.PLANNED.value,
            "dry_run": bool(request.dry_run),
            "prompt_preview": request.prompt[:120],
            "source_media": request.source_media,
            "plan_steps": [
                "Trim the supplied clips into a reviewable sequence.",
                "Keep edits non-destructive and explicit.",
                "Add captions only if the user asked for them.",
            ],
            "deliverables": [
                "non_destructive_edit_plan",
            ],
        }
        plan_path.write_text(
            "\n".join((
                "# JARVIS video edit plan",
                f"plan_id: {plan_id}",
                f"provider: {self.provider_name}",
                f"prompt_preview: {request.prompt[:120]}",
                "",
                "Steps:",
                "1. Trim the supplied clips into a reviewable sequence.",
                "2. Keep edits non-destructive and explicit.",
                "3. Add captions only if the user asked for them.",
            )),
            encoding="utf-8",
        )
        metadata_path = storage.record(payload)
        return VideoEditingPlan(
            plan_id=plan_id,
            status=VideoEditingJobStatus.PLANNED,
            provider=self.provider_name,
            message="A bounded non-destructive video edit plan was prepared.",
            prompt_preview=request.prompt[:120],
            source_media=request.source_media,
            plan_steps=(
                "Trim the supplied clips into a reviewable sequence.",
                "Keep edits non-destructive and explicit.",
                "Add captions only if the user asked for them.",
            ),
            deliverables=("non_destructive_edit_plan",),
            dry_run=bool(request.dry_run),
            metadata={"provider_status": asdict(self.status()), "metadata_path": metadata_path, "plan_path": storage.public_path(plan_path)},
        )


class VideoProviderRegistry:
    """Bounded provider registry for local-first video editing."""

    def __init__(self, providers: tuple[VideoProvider, ...]) -> None:
        self._providers = {provider.provider_name: provider for provider in providers}

    def list_status(self) -> tuple[VideoProviderStatus, ...]:
        return tuple(provider.status() for provider in self._providers.values())

    def select(self, provider_name: str | None = None) -> VideoProvider:
        if provider_name and provider_name in self._providers:
            return self._providers[provider_name]
        if provider_name:
            return UnavailableVideoProvider(f"The configured video provider '{provider_name}' is not registered.")
        return next(iter(self._providers.values()), UnavailableVideoProvider())
