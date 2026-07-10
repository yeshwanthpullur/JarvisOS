"""Provider execution metadata cache."""

from __future__ import annotations

from typing import Any


class ProviderCache:
    """Namespaced cache for provider execution metadata."""

    initialized = True

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {
            "capabilities": {},
            "model_lists": {},
            "health": {},
            "benchmarks": {},
            "metadata": {},
            "statistics": {},
            "configuration": {},
            "history": {},
        }

    def get(self, namespace: str, key: str, default: Any | None = None) -> Any:
        """Return a cached value."""
        return self._cache.setdefault(namespace, {}).get(key, default)

    def set(self, namespace: str, key: str, value: Any) -> None:
        """Store a cached value."""
        self._cache.setdefault(namespace, {})[key] = value

    def clear(self, namespace: str | None = None) -> None:
        """Clear one namespace or the entire cache."""
        if namespace is None:
            for values in self._cache.values():
                values.clear()
            return
        self._cache.setdefault(namespace, {}).clear()

    def statistics(self) -> dict[str, int]:
        """Return cache size statistics by namespace."""
        return {namespace: len(values) for namespace, values in self._cache.items()}
