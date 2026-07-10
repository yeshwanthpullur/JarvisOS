"""Serializable agent profile metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_status import AgentStatus


class AgentType(StrEnum):
    """Supported agent types with custom extension support."""

    PLANNER = "planner"
    RESEARCH = "research"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    CONVERSATION = "conversation"
    CODING = "coding"
    BROWSER = "browser"
    VISION = "vision"
    PHONE = "phone"
    TASK = "task"
    AUTOMATION = "automation"
    SYSTEM = "system"
    SUPERVISOR = "supervisor"
    COORDINATOR = "coordinator"
    EXECUTOR = "executor"
    WORKER = "worker"
    MONITOR = "monitor"
    OBSERVER = "observer"
    UTILITY = "utility"
    CUSTOM = "custom"


class TrustLevel(StrEnum):
    """Configurable trust level labels."""

    SYSTEM = "system"
    CORE = "core"
    TRUSTED = "trusted"
    VERIFIED = "verified"
    PLUGIN = "plugin"
    THIRD_PARTY = "third_party"
    EXPERIMENTAL = "experimental"
    UNTRUSTED = "untrusted"


@dataclass(frozen=True, slots=True)
class AgentProfile:
    """Metadata profile for an agent."""

    agent_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Unnamed Agent"
    description: str = ""
    version: str = "0.1.0"
    author: str = "JARVIS OS"
    agent_type: AgentType = AgentType.CUSTOM
    capabilities: tuple[AgentCapability, ...] = ()
    permissions: tuple[AgentPermission, ...] = ()
    dependencies: tuple[str, ...] = ()
    priority: int = 100
    trust_level: TrustLevel = TrustLevel.CORE
    supported_platforms: tuple[str, ...] = ("windows", "linux", "darwin")
    required_providers: tuple[str, ...] = ()
    required_plugins: tuple[str, ...] = ()
    configuration: dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.IDLE
    plugin_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable profile dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "agent_type": self.agent_type.value,
            "capabilities": [item.value for item in self.capabilities],
            "permissions": [item.value for item in self.permissions],
            "dependencies": list(self.dependencies),
            "priority": self.priority,
            "trust_level": self.trust_level.value,
            "supported_platforms": list(self.supported_platforms),
            "required_providers": list(self.required_providers),
            "required_plugins": list(self.required_plugins),
            "configuration": self.configuration,
            "status": self.status.value,
            "plugin_source": self.plugin_source,
        }
