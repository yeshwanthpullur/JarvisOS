"""OpenRouter provider interface."""

from __future__ import annotations

from providers.cloud_provider_base import CloudProviderBase
from providers.provider_context import ProviderContext


class OpenRouterProvider(CloudProviderBase):
    """Provider contract for OpenRouter."""

    api_key_envs = ("OPENROUTER_API_KEY",)
    default_base_url = "https://openrouter.ai/api"
