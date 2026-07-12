"""Groq provider interface."""

from __future__ import annotations

from providers.cloud_provider_base import CloudProviderBase
from providers.provider_context import ProviderContext


class GroqProvider(CloudProviderBase):
    """Provider contract for Groq."""

    api_key_envs = ("GROQ_API_KEY",)
    default_base_url = "https://api.groq.com"
