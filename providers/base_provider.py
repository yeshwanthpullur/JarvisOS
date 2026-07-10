"""Base provider interface for all AI backends."""

from __future__ import annotations

from abc import ABC

from providers.provider_context import ProviderContext
from providers.provider_health import ProviderHealth
from providers.provider_metrics import ProviderMetrics
from providers.provider_types import (
    CostEstimate,
    ModelInfo,
    ProviderCapabilities,
    ProviderCapability,
    ProviderRequest,
    ProviderResponse,
    TokenEstimate,
)


class BaseProvider(ABC):
    """Base class every provider adapter must implement.

    The default methods intentionally avoid API calls. Concrete future provider
    implementations can override capability methods while keeping this contract.
    """

    def __init__(
        self,
        context: ProviderContext,
        capabilities: ProviderCapabilities | None = None,
    ) -> None:
        self.context = context
        self.provider_id = context.config.provider_id
        self.kind = context.config.kind
        self.enabled = context.config.enabled
        self.health = ProviderHealth()
        self.metrics = ProviderMetrics()
        self._capabilities = capabilities or ProviderCapabilities(capabilities=())
        self.initialized = False

    @property
    def provider_name(self) -> str:
        """Backward-compatible provider name alias."""
        return self.provider_id

    def initialize(self) -> None:
        """Initialize provider adapter state without network calls."""
        self.initialized = True
        self.context.logger.info("provider_initialized provider_id=%s", self.provider_id)

    def shutdown(self) -> None:
        """Shutdown provider adapter state."""
        self.initialized = False
        self.context.logger.info("provider_shutdown provider_id=%s", self.provider_id)

    def health_check(self) -> ProviderHealth:
        """Return provider health without performing network checks."""
        if self.enabled:
            self.health.mark_success()
        else:
            self.health.mark_failure("Provider is disabled.")
        return self.health

    def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        return self._capabilities

    def is_available(self) -> bool:
        """Return whether the provider is enabled and initialized."""
        return self.enabled and self.initialized and self.health_check().available

    def list_models(self) -> tuple[ModelInfo, ...]:
        """Return configured provider models."""
        return self._capabilities.models or self.context.config.models

    def estimate_cost(self, request: ProviderRequest) -> CostEstimate:
        """Estimate cost without calling a provider."""
        return CostEstimate()

    def estimate_tokens(self, text: str) -> TokenEstimate:
        """Estimate tokens with a conservative character heuristic."""
        prompt_tokens = max(1, len(text) // 4) if text else 0
        return TokenEstimate(prompt_tokens=prompt_tokens, total_tokens=prompt_tokens)

    def chat(self, request: ProviderRequest) -> ProviderResponse:
        """Future chat implementation."""
        raise NotImplementedError("Provider chat is not implemented yet.")

    def reason(self, request: ProviderRequest) -> ProviderResponse:
        """Future reasoning implementation."""
        raise NotImplementedError("Provider reasoning is not implemented yet.")

    def code(self, request: ProviderRequest) -> ProviderResponse:
        """Future coding implementation."""
        raise NotImplementedError("Provider coding is not implemented yet.")

    def vision(self, request: ProviderRequest) -> ProviderResponse:
        """Future vision implementation."""
        raise NotImplementedError("Provider vision is not implemented yet.")

    def embedding(self, request: ProviderRequest) -> ProviderResponse:
        """Future embedding implementation."""
        raise NotImplementedError("Provider embeddings are not implemented yet.")

    def speech(self, request: ProviderRequest) -> ProviderResponse:
        """Future speech implementation."""
        raise NotImplementedError("Provider speech is not implemented yet.")

    def transcription(self, request: ProviderRequest) -> ProviderResponse:
        """Future transcription implementation."""
        raise NotImplementedError("Provider transcription is not implemented yet.")

    def image_generation(self, request: ProviderRequest) -> ProviderResponse:
        """Future image generation implementation."""
        raise NotImplementedError("Provider image generation is not implemented yet.")

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        """Backward-compatible async execution placeholder."""
        raise NotImplementedError("Provider execution is not implemented yet.")


def capabilities_for(
    capabilities: tuple[ProviderCapability, ...],
    context_window: int = 0,
    max_tokens: int = 0,
) -> ProviderCapabilities:
    """Create a capability envelope."""
    return ProviderCapabilities(
        capabilities=capabilities,
        context_window=context_window,
        max_tokens=max_tokens,
    )
