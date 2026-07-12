"""OpenAI provider interface."""

from __future__ import annotations

from providers.cloud_provider_base import CloudProviderBase
from providers.provider_context import ProviderContext


class OpenAIProvider(CloudProviderBase):
    """Provider contract for OpenAI."""

    api_key_envs = ("OPENAI_API_KEY",)
    default_base_url = "https://api.openai.com"
    supports_embeddings = True
    supports_vision = True
    supports_streaming = True
    supports_json_mode = True
