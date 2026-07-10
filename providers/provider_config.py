"""Provider configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from providers.provider_types import ModelInfo, ProviderKind


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Configuration for one AI provider."""

    provider_id: str
    kind: ProviderKind
    enabled: bool = True
    default_model: str | None = None
    fallback_model: str | None = None
    preferred_model: str | None = None
    base_url: str | None = None
    api_key_env: str | None = None
    timeout_seconds: int = 30
    max_retries: int = 2
    local_only: bool = False
    models: tuple[ModelInfo, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


def provider_config_from_mapping(
    provider_id: str,
    data: dict[str, Any],
) -> ProviderConfig:
    """Build provider config from config.yaml style mappings."""
    kind = _provider_kind(str(data.get("kind", provider_id)))
    return ProviderConfig(
        provider_id=provider_id,
        kind=kind,
        enabled=bool(data.get("enabled", True)),
        default_model=data.get("default_model"),
        fallback_model=data.get("fallback_model"),
        preferred_model=data.get("preferred_model"),
        base_url=data.get("base_url"),
        api_key_env=data.get("api_key_env"),
        timeout_seconds=int(data.get("timeout_seconds", 30)),
        max_retries=int(data.get("max_retries", 2)),
        local_only=bool(data.get("local_only", False)),
        metadata=dict(data.get("metadata", {})),
    )


def _provider_kind(value: str) -> ProviderKind:
    aliases = {
        "google": ProviderKind.GOOGLE_GEMINI,
        "gemini": ProviderKind.GOOGLE_GEMINI,
        "lmstudio": ProviderKind.LM_STUDIO,
        "lm-studio": ProviderKind.LM_STUDIO,
    }
    if value in aliases:
        return aliases[value]
    return ProviderKind(value)
