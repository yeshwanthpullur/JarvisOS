"""Execution context for the Executive JARVIS request pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from jarvis.jarvis_capabilities import JarvisCapability
from jarvis.jarvis_permissions import JarvisPermission
from jarvis.jarvis_profile import SystemProfile, UserProfile, WorkspaceProfile
from jarvis.jarvis_state import JarvisState
from jarvis.jarvis_types import ExecutionStrategy


@dataclass(slots=True)
class JarvisContext:
    """Context object shared across Executive subsystems."""

    request_id: str
    conversation_id: str | None = None
    session_id: str | None = None
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    goal_id: str | None = None
    workflow_id: str | None = None
    user: UserProfile = field(default_factory=UserProfile)
    workspace: WorkspaceProfile = field(default_factory=WorkspaceProfile)
    system: SystemProfile = field(default_factory=SystemProfile)
    current_state: JarvisState = JarvisState.CREATED
    current_agent: str | None = None
    current_department: str | None = None
    current_provider: str | None = None
    execution_strategy: ExecutionStrategy = ExecutionStrategy.DIRECT
    memory_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    task_references: tuple[str, ...] = ()
    plugin_references: tuple[str, ...] = ()
    tool_references: tuple[str, ...] = ()
    skill_references: tuple[str, ...] = ()
    capabilities: tuple[JarvisCapability, ...] = ()
    permissions: tuple[JarvisPermission, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    settings: Any | None = None
    memory_manager: Any | None = None
    knowledge_manager: Any | None = None
    brain_manager: Any | None = None
    task_manager: Any | None = None
    plugin_manager: Any | None = None
    provider_router: Any | None = None
    agent_manager: Any | None = None
    agent_creator: Any | None = None
    logger: logging.Logger | None = None

