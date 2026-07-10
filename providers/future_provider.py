"""Future provider interface placeholder."""

from __future__ import annotations

from providers.base_provider import BaseProvider
from providers.provider_context import ProviderContext


class FutureProvider(BaseProvider):
    """Provider contract for providers that do not exist yet."""

    def __init__(self, context: ProviderContext) -> None:
        super().__init__(context)
