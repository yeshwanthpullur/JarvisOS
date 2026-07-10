"""Retrieval ranking."""

from __future__ import annotations

from typing import Any


class RetrievalRanker:
    initialized = True

    def rank(self, items: tuple[dict[str, Any], ...], context: object | None = None) -> tuple[dict[str, Any], ...]:
        return tuple(sorted(items, key=lambda item: item.get("priority", 0), reverse=True))
