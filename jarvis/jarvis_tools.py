"""Tool registry architecture for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class JarvisToolRecord:
    """Tool metadata record."""

    tool_id: str
    name: str
    capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


class JarvisTools:
    """Tool discovery and lookup architecture."""

    def __init__(self) -> None:
        self._tools: dict[str, JarvisToolRecord] = {}
        self.initialized = True

    def register(self, record: JarvisToolRecord) -> None:
        """Register a tool record."""
        self._tools[record.tool_id] = record

    def lookup(self, tool_id: str) -> JarvisToolRecord | None:
        """Lookup a tool."""
        return self._tools.get(tool_id)

    def statistics(self) -> dict[str, int]:
        """Return tool statistics."""
        return {"tools": len(self._tools)}

