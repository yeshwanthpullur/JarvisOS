"""Rules for adaptive intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptiveRuleRecord:
    rule_id: str
    rule_type: str
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class AdaptiveRules:
    def __init__(self) -> None:
        self.records: dict[str, AdaptiveRuleRecord] = {}
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def register(self, record: AdaptiveRuleRecord) -> None:
        self._ensure_initialized()
        self.records[record.rule_id] = record

    def update(self, record: AdaptiveRuleRecord) -> None:
        self.register(record)

    def enable(self, rule_id: str) -> None:
        self._ensure_initialized()
        if rule_id in self.records:
            self.records[rule_id].enabled = True

    def disable(self, rule_id: str) -> None:
        self._ensure_initialized()
        if rule_id in self.records:
            self.records[rule_id].enabled = False

    def validate(self, record: AdaptiveRuleRecord) -> bool:
        self._ensure_initialized()
        return bool(record.rule_id and record.rule_type)

    def lookup(self, rule_id: str) -> AdaptiveRuleRecord | None:
        self._ensure_initialized()
        return self.records.get(rule_id)

    def search(self, rule_type: str) -> tuple[AdaptiveRuleRecord, ...]:
        self._ensure_initialized()
        return tuple(record for record in self.records.values() if record.rule_type == rule_type)

    def statistics(self) -> dict[str, int]:
        self._ensure_initialized()
        return {"rules": len(self.records)}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveRules must be initialized before use.")
