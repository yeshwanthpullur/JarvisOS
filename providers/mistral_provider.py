"""Mistral provider interface."""

from __future__ import annotations

from providers.cloud_provider_base import CloudProviderBase
from providers.provider_context import ProviderContext


class MistralProvider(CloudProviderBase):
    """Provider contract for Mistral."""

    api_key_envs = ("MISTRAL_API_KEY",)
    default_base_url = "https://api.mistral.ai"
