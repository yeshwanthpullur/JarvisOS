"""Registry for reflection learning assets."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionRegistryItem:
    item_id: str
    item_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflectionRegistry:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.items: dict[str, ReflectionRegistryItem] = {}
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_registry_initialized")

    def register(self, item: ReflectionRegistryItem) -> None:
        self._ensure_initialized()
        self.items[item.item_id] = item

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionRegistry must be initialized before use.")
