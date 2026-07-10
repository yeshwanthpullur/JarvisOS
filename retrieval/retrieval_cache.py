"""Retrieval cache."""

from __future__ import annotations

from typing import Any


class RetrievalCache:
    initialized = True

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {
            "recent_queries": {},
            "recent_results": {},
            "memory_references": {},
            "knowledge_references": {},
            "workflow_references": {},
            "conversation_references": {},
            "statistics": {},
            "metadata": {},
        }

    def create(self, namespace: str, key: str, value: Any) -> None:
        self._cache.setdefault(namespace, {})[key] = value

    def lookup(self, namespace: str, key: str, default: Any | None = None) -> Any:
        return self._cache.setdefault(namespace, {}).get(key, default)

    def refresh(self, namespace: str, key: str, value: Any) -> None:
        self.create(namespace, key, value)

    def expire(self, namespace: str, key: str) -> None:
        self._cache.setdefault(namespace, {}).pop(key, None)

    def invalidate(self, namespace: str | None = None) -> None:
        if namespace is None:
            for values in self._cache.values():
                values.clear()
            return
        self._cache.setdefault(namespace, {}).clear()

    def statistics(self) -> dict[str, int]:
        return {name: len(values) for name, values in self._cache.items()}
