"""Supervisor for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass

from jarvis.jarvis_health import JarvisHealth


@dataclass(frozen=True, slots=True)
class JarvisSupervisorReport:
    """Supervisor report metadata."""

    health_status: str
    recovery_required: bool = False


class JarvisSupervisor:
    """Monitors executive health metadata."""

    initialized = True

    def report(self, health: JarvisHealth) -> JarvisSupervisorReport:
        """Create a supervisor report."""
        return JarvisSupervisorReport(health_status=health.status.value)

