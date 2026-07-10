"""Agent lifecycle state machine definitions."""

from __future__ import annotations

from enum import StrEnum


class AgentState(StrEnum):
    """Lifecycle states supported by every agent."""

    CREATED = "created"
    INITIALIZED = "initialized"
    READY = "ready"
    RUNNING = "running"
    BUSY = "busy"
    WAITING = "waiting"
    SLEEPING = "sleeping"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"
    RECOVERING = "recovering"
    DISABLED = "disabled"
    SHUTDOWN = "shutdown"
    RESTARTING = "restarting"
    DESTROYED = "destroyed"


VALID_AGENT_TRANSITIONS: dict[AgentState, frozenset[AgentState]] = {
    AgentState.CREATED: frozenset({AgentState.INITIALIZED, AgentState.DISABLED, AgentState.SHUTDOWN, AgentState.DESTROYED}),
    AgentState.INITIALIZED: frozenset({AgentState.READY, AgentState.DISABLED, AgentState.FAILED, AgentState.SHUTDOWN}),
    AgentState.READY: frozenset({AgentState.RUNNING, AgentState.SLEEPING, AgentState.DISABLED, AgentState.SHUTDOWN}),
    AgentState.RUNNING: frozenset({AgentState.BUSY, AgentState.WAITING, AgentState.SLEEPING, AgentState.PAUSED, AgentState.STOPPED, AgentState.FAILED, AgentState.SHUTDOWN}),
    AgentState.BUSY: frozenset({AgentState.RUNNING, AgentState.WAITING, AgentState.FAILED, AgentState.PAUSED}),
    AgentState.WAITING: frozenset({AgentState.RUNNING, AgentState.SLEEPING, AgentState.PAUSED, AgentState.STOPPED}),
    AgentState.SLEEPING: frozenset({AgentState.READY, AgentState.RUNNING, AgentState.SHUTDOWN}),
    AgentState.PAUSED: frozenset({AgentState.RUNNING, AgentState.STOPPED, AgentState.SHUTDOWN}),
    AgentState.STOPPED: frozenset({AgentState.READY, AgentState.RESTARTING, AgentState.SHUTDOWN, AgentState.DESTROYED}),
    AgentState.FAILED: frozenset({AgentState.RECOVERING, AgentState.RESTARTING, AgentState.SHUTDOWN}),
    AgentState.RECOVERING: frozenset({AgentState.READY, AgentState.FAILED, AgentState.SHUTDOWN}),
    AgentState.DISABLED: frozenset({AgentState.READY, AgentState.DESTROYED}),
    AgentState.RESTARTING: frozenset({AgentState.READY, AgentState.FAILED, AgentState.SHUTDOWN}),
    AgentState.SHUTDOWN: frozenset({AgentState.DESTROYED}),
    AgentState.DESTROYED: frozenset(),
}


def validate_transition(current: AgentState, target: AgentState) -> None:
    """Raise when a lifecycle transition is not allowed."""
    if target == current:
        return
    if target not in VALID_AGENT_TRANSITIONS[current]:
        raise ValueError(f"Invalid agent state transition: {current.value} -> {target.value}")
