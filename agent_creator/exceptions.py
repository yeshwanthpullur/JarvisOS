"""Exceptions raised by the Agent Creator Framework."""

from __future__ import annotations


class AgentCreatorError(Exception):
    """Base exception for Agent Creator failures."""


class ValidationError(AgentCreatorError):
    """Raised when a blueprint, template, manifest, or request is invalid."""


class RegistryError(AgentCreatorError):
    """Raised when a registry operation fails."""


class InstallationError(AgentCreatorError):
    """Raised when an installation operation cannot complete."""


class RollbackError(AgentCreatorError):
    """Raised when rollback metadata cannot be prepared."""

