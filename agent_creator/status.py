"""Status definitions for the Agent Creator Framework."""

from __future__ import annotations

from enum import StrEnum


class CreatorStatus(StrEnum):
    """Operational status values for Agent Creator components."""

    READY = "ready"
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"


class ValidationStatus(StrEnum):
    """Validation state for requests and generated artifacts."""

    NOT_VALIDATED = "not_validated"
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"


class InstallationStatus(StrEnum):
    """Installation state for generated agents."""

    NOT_INSTALLED = "not_installed"
    PLANNED = "planned"
    INSTALLED = "installed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

