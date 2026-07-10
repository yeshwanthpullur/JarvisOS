"""Provider capability model for execution-time selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from providers.provider_types import ModelInfo, ProviderCapability
from provider_execution.provider_health import ProviderExecutionHealth


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """Execution-focused capabilities for a provider."""

    models: tuple[ModelInfo, ...] = ()
    context_limits: dict[str, int] = field(default_factory=dict)
    streaming: bool = False
    reasoning: bool = False
    tool_calling: bool = False
    structured_output: bool = False
    vision: bool = False
    audio: bool = False
    embeddings: bool = False
    image_generation: bool = False
    batch_requests: bool = False
    parallel_requests: bool = False
    rate_limits: dict[str, int] = field(default_factory=dict)
    availability: bool = True
    health: ProviderExecutionHealth = field(default_factory=ProviderExecutionHealth)
    metadata: dict[str, Any] = field(default_factory=dict)

    def supports(self, capability: ProviderCapability) -> bool:
        """Return whether this capability envelope supports a provider feature."""
        mapping = {
            ProviderCapability.CHAT: True,
            ProviderCapability.REASONING: self.reasoning,
            ProviderCapability.CODING: True,
            ProviderCapability.VISION: self.vision,
            ProviderCapability.SPEECH: self.audio,
            ProviderCapability.EMBEDDING: self.embeddings,
            ProviderCapability.TRANSCRIPTION: self.audio,
            ProviderCapability.IMAGE_GENERATION: self.image_generation,
            ProviderCapability.FUNCTION_CALLING: self.tool_calling,
            ProviderCapability.STREAMING: self.streaming,
            ProviderCapability.JSON_MODE: self.structured_output,
        }
        return mapping.get(capability, False)

    @classmethod
    def from_router_capabilities(cls, capabilities: Any) -> "ProviderCapabilities":
        """Build execution capabilities from the existing provider router model."""
        provider_capabilities = tuple(getattr(capabilities, "capabilities", ()) or ())
        if not provider_capabilities and hasattr(capabilities, "reasoning"):
            return cls(
                models=tuple(getattr(capabilities, "models", ()) or ()),
                context_limits={"default": int(getattr(capabilities, "context_window", 0) or 0)},
                streaming=bool(getattr(capabilities, "streaming", False)),
                reasoning=bool(getattr(capabilities, "reasoning", False)),
                tool_calling=bool(getattr(capabilities, "tool_calling", False)),
                structured_output=bool(getattr(capabilities, "structured_output", False)),
                vision=bool(getattr(capabilities, "vision", False)),
                audio=bool(getattr(capabilities, "audio", False)),
                embeddings=bool(getattr(capabilities, "embeddings", False)),
                image_generation=bool(getattr(capabilities, "image_generation", False)),
                batch_requests=bool(getattr(capabilities, "batch_requests", False)),
                parallel_requests=bool(getattr(capabilities, "parallel_requests", False)),
                rate_limits=dict(getattr(capabilities, "rate_limits", {}) or {}),
                availability=bool(getattr(capabilities, "availability", True)),
                metadata=dict(getattr(capabilities, "metadata", {}) or {}),
            )
        return cls(
            models=tuple(getattr(capabilities, "models", ()) or ()),
            context_limits={"default": int(getattr(capabilities, "context_window", 0) or 0)},
            streaming=ProviderCapability.STREAMING in provider_capabilities,
            reasoning=ProviderCapability.REASONING in provider_capabilities,
            tool_calling=ProviderCapability.FUNCTION_CALLING in provider_capabilities,
            structured_output=ProviderCapability.JSON_MODE in provider_capabilities,
            vision=ProviderCapability.VISION in provider_capabilities,
            audio=ProviderCapability.SPEECH in provider_capabilities,
            embeddings=ProviderCapability.EMBEDDING in provider_capabilities,
            image_generation=ProviderCapability.IMAGE_GENERATION in provider_capabilities,
        )
