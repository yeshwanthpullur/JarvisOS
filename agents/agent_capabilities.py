"""Agent capability metadata."""

from __future__ import annotations

from enum import StrEnum


class AgentCapability(StrEnum):
    """Declarative capabilities an agent may advertise."""

    REASONING = "reasoning"
    PLANNING = "planning"
    CONVERSATION = "conversation"
    CODING = "coding"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    RETRIEVAL = "retrieval"
    FILESYSTEM = "filesystem"
    BROWSER = "browser"
    VISION = "vision"
    SPEECH = "speech"
    PHONE = "phone"
    ROBOTICS = "robotics"
    AUTOMATION = "automation"
    PLUGINS = "plugins"
    PROVIDERS = "providers"
    TASKS = "tasks"
    LEARNING = "learning"
    REFLECTION = "reflection"
    COORDINATION = "coordination"
    MONITORING = "monitoring"
    REPORTING = "reporting"
    SUMMARIZATION = "summarization"
    EMBEDDINGS = "embeddings"
    IMAGE_GENERATION = "image_generation"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    CUSTOM = "custom"
