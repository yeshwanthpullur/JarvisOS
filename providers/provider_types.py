"""Provider-neutral types for the JARVIS OS AI gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping


class ProviderCapability(StrEnum):
    """Capabilities advertised by AI providers."""

    CHAT = "chat"
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    SPEECH = "speech"
    EMBEDDING = "embedding"
    TRANSCRIPTION = "transcription"
    IMAGE_GENERATION = "image_generation"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"


class ProviderKind(StrEnum):
    """Supported provider families."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"
    LOCAL = "local"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    LM_STUDIO = "lm_studio"
    CUSTOM = "custom"
    FUTURE = "future"


class ProviderStatus(StrEnum):
    """Provider lifecycle status."""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNHEALTHY = "unhealthy"
    REMOVED = "removed"


class ProviderTaskType(StrEnum):
    """Routing task classes."""

    CHAT = "chat"
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    SPEECH = "speech"
    EMBEDDING = "embedding"
    TRANSCRIPTION = "transcription"
    IMAGE_GENERATION = "image_generation"


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """Provider-neutral model metadata."""

    model_id: str
    display_name: str
    capabilities: tuple[ProviderCapability, ...]
    context_window: int = 0
    max_tokens: int = 0
    preferred_for: tuple[ProviderTaskType, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """Complete capability envelope for one provider."""

    capabilities: tuple[ProviderCapability, ...]
    models: tuple[ModelInfo, ...] = ()
    context_window: int = 0
    max_tokens: int = 0

    def supports(self, capability: ProviderCapability) -> bool:
        """Return whether the provider supports a capability."""
        return capability in self.capabilities


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    """Provider-neutral request envelope."""

    prompt: str
    goal: str = ""
    task_type: ProviderTaskType = ProviderTaskType.CHAT
    model: str | None = None
    required_capabilities: tuple[ProviderCapability, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    """Usage reported by future provider responses."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    currency: str = "USD"


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    """Provider-neutral response envelope."""

    provider_id: str
    model: str
    content: str
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CostEstimate:
    """Estimated request cost."""

    amount: float = 0.0
    currency: str = "USD"
    confidence: float = 0.0


@dataclass(frozen=True, slots=True)
class TokenEstimate:
    """Estimated token count."""

    prompt_tokens: int
    max_completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True, slots=True)
class ProviderSelection:
    """Selected provider and model for a request."""

    provider_id: str
    model: str | None
    reason: str


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)
