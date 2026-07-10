"""Provider discovery from central configuration."""

from __future__ import annotations

import logging

from config.schema import ProvidersConfig
from providers.provider_config import ProviderConfig, provider_config_from_mapping
from providers.provider_types import ProviderKind


DEFAULT_PROVIDER_KINDS: tuple[ProviderKind, ...] = (
    ProviderKind.OPENAI,
    ProviderKind.ANTHROPIC,
    ProviderKind.GOOGLE_GEMINI,
    ProviderKind.LOCAL,
    ProviderKind.OLLAMA,
    ProviderKind.DEEPSEEK,
    ProviderKind.MISTRAL,
    ProviderKind.GROQ,
    ProviderKind.OPENROUTER,
    ProviderKind.LM_STUDIO,
    ProviderKind.CUSTOM,
    ProviderKind.FUTURE,
)


class ProviderLoader:
    """Discovers provider configurations without secrets or API calls."""

    def __init__(
        self,
        config: ProvidersConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or logging.getLogger(__name__)

    def discover(self) -> tuple[ProviderConfig, ...]:
        """Discover configured providers or return built-in disabled interfaces."""
        discovered: list[ProviderConfig] = []
        definitions = dict(self._config.definitions)
        if definitions:
            for provider_id, raw in definitions.items():
                discovered.append(provider_config_from_mapping(provider_id, dict(raw)))
        else:
            enabled = set(self._config.enabled_providers)
            for kind in DEFAULT_PROVIDER_KINDS:
                discovered.append(
                    ProviderConfig(
                        provider_id=kind.value,
                        kind=kind,
                        enabled=kind.value in enabled,
                        local_only=kind in {ProviderKind.LOCAL, ProviderKind.OLLAMA, ProviderKind.LM_STUDIO},
                        default_model=self._config.default_provider
                        if self._config.default_provider == kind.value
                        else None,
                    )
                )
        for config in discovered:
            self._logger.info("provider_discovered provider_id=%s kind=%s enabled=%s", config.provider_id, config.kind.value, config.enabled)
        return tuple(discovered)
