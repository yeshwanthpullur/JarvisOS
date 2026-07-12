"""ZenMux provider interface."""

from __future__ import annotations

from providers.cloud_provider_base import CloudProviderBase


class ZenMuxProvider(CloudProviderBase):
    """Provider contract for ZenMux."""

    api_key_envs = ("ZENMUX_API_KEY",)
    default_base_url = "https://api.zenmux.ai"
    supports_embeddings = False
    supports_vision = True
    supports_streaming = True
    supports_json_mode = True
