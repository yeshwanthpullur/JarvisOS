"""Least-context sharing with explicit scopes and provenance."""

from __future__ import annotations

from .models import ContextFragment, ContextScope


class ControlledContextStore:
    def __init__(self, max_fragments: int = 64, max_chars: int = 12_000) -> None:
        self.max_fragments = max(1, min(max_fragments, 256))
        self.max_chars = max(1000, min(max_chars, 100_000))
        self._fragments: dict[str, list[ContextFragment]] = {}

    def add(self, context_id: str, fragment: ContextFragment) -> None:
        values = self._fragments.setdefault(context_id, [])
        if len(values) >= self.max_fragments:
            raise ValueError("context_fragment_limit_exceeded")
        if sum(item.char_budget for item in values) + fragment.char_budget > self.max_chars:
            raise ValueError("context_character_budget_exceeded")
        values.append(fragment)

    def select(
        self,
        context_id: str,
        *,
        scopes: tuple[ContextScope, ...],
        allow_personal: bool = False,
        max_items: int = 16,
    ) -> tuple[ContextFragment, ...]:
        selected = []
        for fragment in self._fragments.get(context_id, ()): 
            if fragment.scope not in scopes:
                continue
            if fragment.contains_personal_data and not allow_personal:
                continue
            selected.append(fragment)
            if len(selected) >= max(1, min(max_items, 32)):
                break
        return tuple(selected)

    def summary(self, context_id: str) -> dict[str, int]:
        values = self._fragments.get(context_id, ())
        return {
            "fragments": len(values),
            "personal_refs": sum(item.contains_personal_data for item in values),
            "character_budget": sum(item.char_budget for item in values),
        }

