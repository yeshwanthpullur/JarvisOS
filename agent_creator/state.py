"""Lifecycle state machines for Agent Creator entities."""

from __future__ import annotations

from enum import StrEnum


class BlueprintState(StrEnum):
    """Lifecycle for blueprints."""

    CREATED = "created"
    REGISTERED = "registered"
    VALIDATED = "validated"
    APPROVED = "approved"
    GENERATED = "generated"
    INSTALLED = "installed"
    LOADED = "loaded"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    REMOVED = "removed"


class DynamicAgentState(StrEnum):
    """Lifecycle for dynamic agents."""

    REQUESTED = "requested"
    PLANNED = "planned"
    GENERATED = "generated"
    VALIDATED = "validated"
    INSTALLED = "installed"
    REGISTERED = "registered"
    LOADED = "loaded"
    ENABLED = "enabled"
    RUNNING = "running"
    PAUSED = "paused"
    DISABLED = "disabled"
    ARCHIVED = "archived"
    EXPORTED = "exported"
    IMPORTED = "imported"
    REMOVED = "removed"
    DESTROYED = "destroyed"


class DepartmentState(StrEnum):
    """Lifecycle for departments."""

    CREATED = "created"
    REGISTERED = "registered"
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"
    REMOVED = "removed"


BLUEPRINT_TRANSITIONS: dict[BlueprintState, frozenset[BlueprintState]] = {
    BlueprintState.CREATED: frozenset({BlueprintState.REGISTERED, BlueprintState.REMOVED}),
    BlueprintState.REGISTERED: frozenset({BlueprintState.VALIDATED, BlueprintState.DEPRECATED, BlueprintState.REMOVED}),
    BlueprintState.VALIDATED: frozenset({BlueprintState.APPROVED, BlueprintState.DEPRECATED}),
    BlueprintState.APPROVED: frozenset({BlueprintState.GENERATED, BlueprintState.DEPRECATED}),
    BlueprintState.GENERATED: frozenset({BlueprintState.INSTALLED, BlueprintState.ARCHIVED}),
    BlueprintState.INSTALLED: frozenset({BlueprintState.LOADED, BlueprintState.ARCHIVED}),
    BlueprintState.LOADED: frozenset({BlueprintState.DEPRECATED, BlueprintState.ARCHIVED}),
    BlueprintState.DEPRECATED: frozenset({BlueprintState.ARCHIVED, BlueprintState.REMOVED}),
    BlueprintState.ARCHIVED: frozenset({BlueprintState.REMOVED}),
    BlueprintState.REMOVED: frozenset(),
}


def validate_blueprint_transition(current: BlueprintState, target: BlueprintState) -> None:
    """Raise when a blueprint lifecycle transition is invalid."""
    if current == target:
        return
    if target not in BLUEPRINT_TRANSITIONS[current]:
        raise ValueError(f"Invalid blueprint transition: {current.value} -> {target.value}")

