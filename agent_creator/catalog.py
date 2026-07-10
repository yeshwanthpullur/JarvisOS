"""Agent catalog for generated agent inventory."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_creator.manifest import AgentManifest
from agent_creator.utils import utc_now


@dataclass(slots=True)
class CatalogEntry:
    """Catalog metadata for a generated agent."""

    manifest: AgentManifest
    template_id: str
    blueprint_id: str
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    installed_at: str | None = None
    update_history: list[str] = field(default_factory=list)


class AgentCatalog:
    """Official inventory of generated JARVIS OS agents."""

    def __init__(self) -> None:
        self._entries: dict[str, CatalogEntry] = {}
        self.initialized = True

    def add(self, entry: CatalogEntry) -> None:
        """Add or replace a catalog entry."""
        self._entries[entry.manifest.agent_id] = entry

    def get(self, agent_id: str) -> CatalogEntry | None:
        """Return a catalog entry."""
        return self._entries.get(agent_id)

    def list_entries(self) -> tuple[CatalogEntry, ...]:
        """List catalog entries."""
        return tuple(self._entries.values())

    def search(self, text: str) -> tuple[CatalogEntry, ...]:
        """Search catalog entries."""
        needle = text.lower()
        return tuple(
            entry
            for entry in self._entries.values()
            if needle in entry.manifest.name.lower() or needle in entry.manifest.category.lower()
        )

