"""Agent Creator permission metadata."""

from __future__ import annotations

from enum import StrEnum

from agents import AgentPermission


class CreatorPermission(StrEnum):
    """Declarative permissions available to generated agents."""

    FILESYSTEM = "filesystem"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TASKS = "tasks"
    PLUGINS = "plugins"
    PROVIDERS = "providers"
    CONFIGURATION = "configuration"
    LOGGING = "logging"
    NOTIFICATIONS = "notifications"
    DOCUMENTS = "documents"
    DOWNLOADS = "downloads"
    DESKTOP = "desktop"
    CLIPBOARD = "clipboard"
    CAMERA = "camera"
    MICROPHONE = "microphone"
    NETWORK = "network"
    VOICE = "voice"
    VISION = "vision"
    ROBOTICS = "robotics"
    CUSTOM = "custom"


def to_agent_permission(permission: CreatorPermission) -> AgentPermission:
    """Map creator permissions to Agent Framework permissions when possible."""
    mapping = {
        CreatorPermission.FILESYSTEM: AgentPermission.FILESYSTEM,
        CreatorPermission.MEMORY: AgentPermission.MEMORY,
        CreatorPermission.KNOWLEDGE: AgentPermission.KNOWLEDGE,
        CreatorPermission.TASKS: AgentPermission.TASKS,
        CreatorPermission.PLUGINS: AgentPermission.PLUGINS,
        CreatorPermission.PROVIDERS: AgentPermission.PROVIDERS,
        CreatorPermission.CONFIGURATION: AgentPermission.CONFIGURATION,
        CreatorPermission.NOTIFICATIONS: AgentPermission.NOTIFICATIONS,
        CreatorPermission.DOCUMENTS: AgentPermission.DOCUMENTS,
        CreatorPermission.DOWNLOADS: AgentPermission.DOWNLOADS,
        CreatorPermission.DESKTOP: AgentPermission.DESKTOP,
        CreatorPermission.CLIPBOARD: AgentPermission.CLIPBOARD,
        CreatorPermission.CAMERA: AgentPermission.CAMERA,
        CreatorPermission.MICROPHONE: AgentPermission.MICROPHONE,
        CreatorPermission.VOICE: AgentPermission.VOICE,
        CreatorPermission.VISION: AgentPermission.VISION,
    }
    return mapping.get(permission, AgentPermission.FUTURE_EXTENSIONS)

