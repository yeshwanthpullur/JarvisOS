"""Exceptions for the Executive JARVIS Core."""

from __future__ import annotations


class JarvisError(Exception):
    """Base error for Executive JARVIS failures."""


class JarvisValidationError(JarvisError):
    """Raised when an executive request or response is invalid."""


class JarvisLifecycleError(JarvisError):
    """Raised when lifecycle operations cannot be completed."""


class JarvisRoutingError(JarvisError):
    """Raised when a request cannot be routed."""

