"""Runtime for the Executive JARVIS Core."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.jarvis_health import JarvisHealth
from jarvis.jarvis_metrics import JarvisMetrics
from jarvis.jarvis_state import JarvisState, validate_jarvis_transition


@dataclass(slots=True)
class JarvisRuntime:
    """Runtime state and lifecycle operations."""

    state: JarvisState = JarvisState.CREATED
    metrics: JarvisMetrics = field(default_factory=JarvisMetrics)
    health: JarvisHealth = field(default_factory=JarvisHealth)

    def initialize(self) -> None:
        """Initialize runtime."""
        self._transition(JarvisState.INITIALIZED)

    def start(self) -> None:
        """Start runtime."""
        if self.state is JarvisState.INITIALIZED:
            self._transition(JarvisState.STARTING)
        self._transition(JarvisState.READY)
        self._transition(JarvisState.IDLE)
        self.metrics.startup_count += 1

    def pause(self) -> None:
        """Pause runtime."""
        self._transition(JarvisState.PAUSED)

    def resume(self) -> None:
        """Resume runtime."""
        self._transition(JarvisState.READY)

    def stop(self) -> None:
        """Stop runtime."""
        self._transition(JarvisState.STOPPING)

    def restart(self) -> None:
        """Restart runtime metadata."""
        self.state = JarvisState.RESTARTING
        self.state = JarvisState.READY

    def shutdown(self) -> None:
        """Shutdown runtime."""
        if self.state not in {JarvisState.SHUTDOWN, JarvisState.STOPPING}:
            self.state = JarvisState.STOPPING
        self._transition(JarvisState.SHUTDOWN)

    def heartbeat(self) -> None:
        """Record heartbeat."""
        self.health.heartbeat()

    def checkpoint(self) -> dict[str, object]:
        """Create checkpoint metadata."""
        return {"state": self.state.value}

    def restore(self, checkpoint: dict[str, object]) -> None:
        """Restore checkpoint metadata."""
        self.state = JarvisState(str(checkpoint["state"]))

    def recover(self) -> None:
        """Move into recovery state."""
        self.state = JarvisState.RECOVERING

    def cleanup(self) -> None:
        """Runtime cleanup hook."""

    def monitor(self) -> dict[str, object]:
        """Return runtime monitor data."""
        return {"state": self.state.value, "health": self.health.status.value}

    def report(self) -> dict[str, object]:
        """Return runtime report data."""
        return self.monitor()

    def _transition(self, state: JarvisState) -> None:
        validate_jarvis_transition(self.state, state)
        self.state = state

