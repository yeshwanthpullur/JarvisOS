"""Dependency rules for task intelligence."""

from __future__ import annotations

import logging


class DependencyManager:
    """Track dependency relationships."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._dependencies: dict[str, set[str]] = {}
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("dependency_manager_initialized")

    def add_dependency(self, item_id: str, dependency_id: str) -> None:
        self._ensure_initialized()
        self._dependencies.setdefault(item_id, set()).add(dependency_id)
        self._logger.info("dependency_added item_id=%s dependency_id=%s", item_id, dependency_id)

    def statistics(self) -> dict[str, object]:
        self._ensure_initialized()
        return {"items": len(self._dependencies), "status": "ready"}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("DependencyManager must be initialized before use.")
