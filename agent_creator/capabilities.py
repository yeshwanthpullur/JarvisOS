"""Agent Creator capability metadata."""

from __future__ import annotations

from enum import StrEnum

from agents import AgentCapability


class CreatorCapability(StrEnum):
    """Capabilities a blueprint or generated agent can declare."""

    CONVERSATION = "conversation"
    PLANNING = "planning"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    CODING = "coding"
    FILESYSTEM = "filesystem"
    BROWSER = "browser"
    VISION = "vision"
    PHONE = "phone"
    AUTOMATION = "automation"
    MONITORING = "monitoring"
    REPORTING = "reporting"
    SCHEDULING = "scheduling"
    COORDINATION = "coordination"
    TOOL_EXECUTION = "tool_execution"
    PLUGIN_INTEGRATION = "plugin_integration"
    PROVIDER_ACCESS = "provider_access"
    CUSTOM = "custom"


def to_agent_capability(capability: CreatorCapability) -> AgentCapability:
    """Map creator capabilities to Agent Framework capabilities when possible."""
    mapping = {
        CreatorCapability.CONVERSATION: AgentCapability.CONVERSATION,
        CreatorCapability.PLANNING: AgentCapability.PLANNING,
        CreatorCapability.MEMORY: AgentCapability.MEMORY,
        CreatorCapability.KNOWLEDGE: AgentCapability.KNOWLEDGE,
        CreatorCapability.RESEARCH: AgentCapability.RETRIEVAL,
        CreatorCapability.CODING: AgentCapability.CODING,
        CreatorCapability.FILESYSTEM: AgentCapability.FILESYSTEM,
        CreatorCapability.BROWSER: AgentCapability.BROWSER,
        CreatorCapability.VISION: AgentCapability.VISION,
        CreatorCapability.PHONE: AgentCapability.PHONE,
        CreatorCapability.AUTOMATION: AgentCapability.AUTOMATION,
        CreatorCapability.MONITORING: AgentCapability.MONITORING,
        CreatorCapability.REPORTING: AgentCapability.REPORTING,
        CreatorCapability.COORDINATION: AgentCapability.COORDINATION,
        CreatorCapability.PLUGIN_INTEGRATION: AgentCapability.PLUGINS,
        CreatorCapability.PROVIDER_ACCESS: AgentCapability.PROVIDERS,
    }
    return mapping.get(capability, AgentCapability.CUSTOM)

