"""Central runtime status model for JARVIS OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


APP_VERSION = "0.1.0"


class SystemState(StrEnum):
    """Runtime lifecycle states for the application skeleton."""

    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(slots=True)
class SystemStatus:
    """Mutable runtime status shared by bootstrap components."""

    application_version: str = APP_VERSION
    startup_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    loaded_modules: list[str] = field(default_factory=list)
    state: SystemState = SystemState.STARTING

    @property
    def running_time_seconds(self) -> float:
        """Return elapsed runtime in seconds."""
        return (datetime.now(timezone.utc) - self.startup_time).total_seconds()

    def mark_module_loaded(self, module_name: str) -> None:
        """Record a successfully initialized module once."""
        if module_name not in self.loaded_modules:
            self.loaded_modules.append(module_name)

    def set_state(self, state: SystemState) -> None:
        """Update the current system state."""
        self.state = state

    def summary(self) -> dict[str, object]:
        """Return a structured summary suitable for logs or status output."""
        return {
            "application_version": self.application_version,
            "startup_time": self.startup_time.isoformat(),
            "running_time_seconds": round(self.running_time_seconds, 2),
            "loaded_modules": tuple(self.loaded_modules),
            "system_state": self.state.value,
        }

