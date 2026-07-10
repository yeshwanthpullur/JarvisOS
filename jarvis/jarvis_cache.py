"""Cache interfaces for Executive JARVIS."""

from __future__ import annotations

from typing import Any


class JarvisCache:
    """Namespaced in-memory cache for future runtime acceleration."""

    def __init__(self) -> None:
        self._values: dict[str, dict[str, Any]] = {}
        self.initialized = True

    def set(self, namespace: str, key: str, value: Any) -> None:
        """Set a cache value."""
        self._values.setdefault(namespace, {})[key] = value

    def get(self, namespace: str, key: str) -> Any | None:
        """Get a cache value."""
        return self._values.get(namespace, {}).get(key)

    def clear(self, namespace: str | None = None) -> None:
        """Clear cache values."""
        if namespace is None:
            self._values.clear()
        else:
            self._values.pop(namespace, None)

