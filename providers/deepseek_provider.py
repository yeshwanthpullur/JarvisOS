"""DeepSeek provider interface."""

from __future__ import annotations

from providers.cloud_provider_base import CloudProviderBase
from providers.provider_context import ProviderContext


class DeepSeekProvider(CloudProviderBase):
    """Provider contract for DeepSeek."""

    api_key_envs = ("DEEPSEEK_API_KEY",)
    default_base_url = "https://api.deepseek.com"
