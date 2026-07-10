"""Registry for Executive JARVIS components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class JarvisRegistryRecord:
    """Registered executive component."""

    key: str
    component: Any
    category: str
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class JarvisRegistry:
    """Registry for managers, engines, departments, tools, skills, and checks."""

    def __init__(self) -> None:
        self._records: dict[str, JarvisRegistryRecord] = {}
        self.initialized = True

    def register(self, key: str, component: Any, category: str, capabilities: tuple[str, ...] = ()) -> JarvisRegistryRecord:
        """Register a component."""
        record = JarvisRegistryRecord(key=key, component=component, category=category, capabilities=capabilities)
        self._records[key] = record
        return record

    def unregister(self, key: str) -> bool:
        """Remove a component."""
        return self._records.pop(key, None) is not None

    def lookup(self, key: str) -> Any | None:
        """Lookup a component by key."""
        record = self._records.get(key)
        return record.component if record else None

    def enumerate(self, category: str | None = None) -> tuple[JarvisRegistryRecord, ...]:
        """Enumerate records, optionally by category."""
        records = tuple(self._records.values())
        if category is None:
            return records
        return tuple(record for record in records if record.category == category)

    def capability_lookup(self, capability: str) -> tuple[JarvisRegistryRecord, ...]:
        """Find records by capability."""
        return tuple(record for record in self._records.values() if capability in record.capabilities)

    def validate(self) -> bool:
        """Return whether the registry is internally valid."""
        return all(record.key for record in self._records.values())

    def statistics(self) -> dict[str, int]:
        """Return registry statistics."""
        return {"records": len(self._records)}

