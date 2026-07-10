"""Provider factory for built-in provider interface adapters."""

from __future__ import annotations

import logging

from config.schema import AppSettings
from providers.anthropic_provider import AnthropicProvider
from providers.base_provider import BaseProvider
from providers.custom_provider import CustomProvider
from providers.deepseek_provider import DeepSeekProvider
from providers.future_provider import FutureProvider
from providers.google_provider import GoogleProvider
from providers.groq_provider import GroqProvider
from providers.lm_studio_provider import LMStudioProvider
from providers.local_provider import LocalProvider
from providers.mistral_provider import MistralProvider
from providers.ollama_provider import OllamaProvider
from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.provider_config import ProviderConfig
from providers.provider_context import ProviderContext
from providers.provider_permissions import ProviderPermission, ProviderPermissionSet
from providers.provider_types import ProviderKind


PROVIDER_CLASSES: dict[ProviderKind, type[BaseProvider]] = {
    ProviderKind.OPENAI: OpenAIProvider,
    ProviderKind.ANTHROPIC: AnthropicProvider,
    ProviderKind.GOOGLE_GEMINI: GoogleProvider,
    ProviderKind.LOCAL: LocalProvider,
    ProviderKind.OLLAMA: OllamaProvider,
    ProviderKind.DEEPSEEK: DeepSeekProvider,
    ProviderKind.MISTRAL: MistralProvider,
    ProviderKind.GROQ: GroqProvider,
    ProviderKind.OPENROUTER: OpenRouterProvider,
    ProviderKind.LM_STUDIO: LMStudioProvider,
    ProviderKind.CUSTOM: CustomProvider,
    ProviderKind.FUTURE: FutureProvider,
}


class ProviderFactory:
    """Creates provider interface adapters from provider configuration."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._logger = logger or logging.getLogger(__name__)

    def create(self, config: ProviderConfig) -> BaseProvider:
        """Create a provider adapter without external API calls."""
        provider_class = PROVIDER_CLASSES.get(config.kind, CustomProvider)
        permissions = self._permissions_for(config)
        context = ProviderContext(
            config=config,
            settings=self._settings,
            permissions=permissions,
            logger=logging.getLogger(f"providers.{config.provider_id}"),
        )
        provider = provider_class(context)
        self._logger.info("provider_created provider_id=%s kind=%s", config.provider_id, config.kind.value)
        return provider

    def _permissions_for(self, config: ProviderConfig) -> ProviderPermissionSet:
        permissions: list[ProviderPermission] = []
        if config.local_only or config.kind in {ProviderKind.LOCAL, ProviderKind.OLLAMA, ProviderKind.LM_STUDIO}:
            permissions.append(ProviderPermission.LOCAL_MODEL)
        else:
            permissions.append(ProviderPermission.INTERNET)
        if config.api_key_env:
            permissions.append(ProviderPermission.API_KEY)
        return ProviderPermissionSet(tuple(permissions))
