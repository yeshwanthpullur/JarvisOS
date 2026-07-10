"""Registry for adaptive intelligence artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptiveRegistryItem:
    item_id: str
    item_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AdaptiveRegistry:
    def __init__(self) -> None:
        self.sessions: dict[str, Any] = {}
        self.experience_registry: dict[str, AdaptiveRegistryItem] = {}
        self.learning_queue: dict[str, Any] = {}
        self.policy_registry: dict[str, Any] = {}
        self.rule_registry: dict[str, Any] = {}
        self.history: list[Any] = []
        self.executive_decisions: list[Any] = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def register(self, item: AdaptiveRegistryItem) -> None:
        self._ensure_initialized()
        self.experience_registry[item.item_id] = item

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveRegistry must be initialized before use.")
