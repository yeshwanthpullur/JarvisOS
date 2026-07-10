"""Generated agent registry models."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_creator.manifest import AgentManifest
from agent_creator.state import DynamicAgentState


@dataclass(slots=True)
class GeneratedAgentRecord:
    """Registry record for a generated or installed agent."""

    manifest: AgentManifest
    package_name: str
    installed: bool = False
    enabled: bool = False
    state: DynamicAgentState = DynamicAgentState.GENERATED
    history: list[str] = field(default_factory=list)


class DynamicAgentRegistry:
    """Inventory for non-core generated agents."""

    def __init__(self) -> None:
        self._records: dict[str, GeneratedAgentRecord] = {}
        self.initialized = True

    def register(self, record: GeneratedAgentRecord) -> None:
        """Register a generated agent record."""
        self._records[record.manifest.agent_id] = record

    def get(self, agent_id: str) -> GeneratedAgentRecord | None:
        """Return a generated agent record."""
        return self._records.get(agent_id)

    def list_agents(self) -> tuple[GeneratedAgentRecord, ...]:
        """List generated agent records."""
        return tuple(self._records.values())

    def enable(self, agent_id: str) -> None:
        """Enable a dynamic agent record."""
        record = self._records[agent_id]
        record.enabled = True
        record.state = DynamicAgentState.ENABLED

    def disable(self, agent_id: str) -> None:
        """Disable a dynamic agent record."""
        record = self._records[agent_id]
        record.enabled = False
        record.state = DynamicAgentState.DISABLED

    def archive(self, agent_id: str) -> None:
        """Archive a dynamic agent record."""
        self._records[agent_id].state = DynamicAgentState.ARCHIVED

    def search(self, text: str) -> tuple[GeneratedAgentRecord, ...]:
        """Search generated agents."""
        needle = text.lower()
        return tuple(
            record
            for record in self._records.values()
            if needle in record.manifest.name.lower()
            or needle in record.manifest.description.lower()
            or needle in record.manifest.category.lower()
        )

