"""Custom provider interface placeholder."""

from __future__ import annotations

from providers.base_provider import BaseProvider
from providers.provider_context import ProviderContext


class CustomProvider(BaseProvider):
    """Provider contract for user-defined future providers."""

    def __init__(self, context: ProviderContext) -> None:
        super().__init__(context)
