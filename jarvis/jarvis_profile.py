"""Executive profile models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jarvis.jarvis_capabilities import JarvisCapability
from jarvis.jarvis_constants import EXECUTIVE_NAME, JARVIS_CORE_VERSION
from jarvis.jarvis_permissions import JarvisPermission


@dataclass(frozen=True, slots=True)
class JarvisProfile:
    """Profile for the permanent Executive JARVIS Core."""

    name: str = EXECUTIVE_NAME
    version: str = JARVIS_CORE_VERSION
    description: str = "Executive Intelligence layer for JARVIS OS."
    capabilities: tuple[JarvisCapability, ...] = (
        JarvisCapability.CONVERSATION,
        JarvisCapability.DECISION_MAKING,
        JarvisCapability.PLANNING,
        JarvisCapability.COORDINATION,
        JarvisCapability.DELEGATION,
        JarvisCapability.RESPONSE_COMPOSITION,
    )
    permissions: tuple[JarvisPermission, ...] = (
        JarvisPermission.MEMORY,
        JarvisPermission.KNOWLEDGE,
        JarvisPermission.TASKS,
        JarvisPermission.PLUGINS,
        JarvisPermission.PROVIDERS,
        JarvisPermission.AGENTS,
        JarvisPermission.AGENT_CREATOR,
    )
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UserProfile:
    """User profile metadata passed through context."""

    user_id: str = "local-user"
    display_name: str = "User"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkspaceProfile:
    """Workspace profile metadata."""

    workspace_id: str = "local-workspace"
    name: str = "Local Workspace"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SystemProfile:
    """System profile metadata."""

    system_id: str = "jarvis-os"
    name: str = "JARVIS OS"
    metadata: dict[str, Any] = field(default_factory=dict)

