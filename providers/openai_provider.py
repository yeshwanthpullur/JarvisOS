"""OpenAI provider interface placeholder."""

from __future__ import annotations

from providers.base_provider import BaseProvider, capabilities_for
from providers.provider_context import ProviderContext
from providers.provider_types import ProviderCapability


class OpenAIProvider(BaseProvider):
    """Provider contract for future OpenAI integration."""

    def __init__(self, context: ProviderContext) -> None:
        super().__init__(
            context,
            capabilities_for(
                (
                    ProviderCapability.CHAT,
                    ProviderCapability.REASONING,
                    ProviderCapability.CODING,
                    ProviderCapability.VISION,
                    ProviderCapability.EMBEDDING,
                    ProviderCapability.SPEECH,
                    ProviderCapability.TRANSCRIPTION,
                    ProviderCapability.IMAGE_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                    ProviderCapability.STREAMING,
                    ProviderCapability.JSON_MODE,
                )
            ),
        )
