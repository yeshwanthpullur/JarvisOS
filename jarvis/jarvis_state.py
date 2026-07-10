"""Runtime states for the Executive JARVIS Core."""

from __future__ import annotations

from enum import StrEnum


class JarvisState(StrEnum):
    """Lifecycle states for the Executive runtime."""

    CREATED = "created"
    INITIALIZED = "initialized"
    STARTING = "starting"
    READY = "ready"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    PLANNING = "planning"
    DELEGATING = "delegating"
    EXECUTING = "executing"
    WAITING = "waiting"
    RESPONDING = "responding"
    PAUSED = "paused"
    RECOVERING = "recovering"
    RESTARTING = "restarting"
    STOPPING = "stopping"
    SHUTDOWN = "shutdown"
    FAILED = "failed"


VALID_JARVIS_TRANSITIONS: dict[JarvisState, frozenset[JarvisState]] = {
    JarvisState.CREATED: frozenset({JarvisState.INITIALIZED, JarvisState.FAILED}),
    JarvisState.INITIALIZED: frozenset({JarvisState.STARTING, JarvisState.SHUTDOWN, JarvisState.FAILED}),
    JarvisState.STARTING: frozenset({JarvisState.READY, JarvisState.FAILED}),
    JarvisState.READY: frozenset({JarvisState.IDLE, JarvisState.LISTENING, JarvisState.PAUSED, JarvisState.STOPPING}),
    JarvisState.IDLE: frozenset({JarvisState.LISTENING, JarvisState.THINKING, JarvisState.PAUSED, JarvisState.STOPPING}),
    JarvisState.LISTENING: frozenset({JarvisState.THINKING, JarvisState.IDLE, JarvisState.PAUSED}),
    JarvisState.THINKING: frozenset({JarvisState.PLANNING, JarvisState.DELEGATING, JarvisState.RESPONDING, JarvisState.FAILED}),
    JarvisState.PLANNING: frozenset({JarvisState.DELEGATING, JarvisState.EXECUTING, JarvisState.RESPONDING, JarvisState.FAILED}),
    JarvisState.DELEGATING: frozenset({JarvisState.EXECUTING, JarvisState.WAITING, JarvisState.RESPONDING, JarvisState.FAILED}),
    JarvisState.EXECUTING: frozenset({JarvisState.WAITING, JarvisState.RESPONDING, JarvisState.FAILED}),
    JarvisState.WAITING: frozenset({JarvisState.RESPONDING, JarvisState.FAILED}),
    JarvisState.RESPONDING: frozenset({JarvisState.IDLE, JarvisState.LISTENING, JarvisState.FAILED}),
    JarvisState.PAUSED: frozenset({JarvisState.READY, JarvisState.STOPPING}),
    JarvisState.RECOVERING: frozenset({JarvisState.READY, JarvisState.FAILED}),
    JarvisState.RESTARTING: frozenset({JarvisState.READY, JarvisState.FAILED}),
    JarvisState.STOPPING: frozenset({JarvisState.SHUTDOWN}),
    JarvisState.SHUTDOWN: frozenset(),
    JarvisState.FAILED: frozenset({JarvisState.RECOVERING, JarvisState.SHUTDOWN}),
}


def validate_jarvis_transition(current: JarvisState, target: JarvisState) -> None:
    """Raise when a runtime transition is not allowed."""
    if current == target:
        return
    if target not in VALID_JARVIS_TRANSITIONS[current]:
        raise ValueError(f"Invalid JARVIS transition: {current.value} -> {target.value}")

