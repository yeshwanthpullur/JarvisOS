"""Base class for all JARVIS OS agents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.agent_checkpoint import AgentCheckpoint
from agents.agent_context import AgentContext
from agents.agent_health import AgentHealth
from agents.agent_message import AgentMessage
from agents.agent_metrics import AgentMetrics
from agents.agent_profile import AgentProfile
from agents.agent_result import AgentResult
from agents.agent_state import AgentState, validate_transition
from agents.agent_status import AgentStatus


class BaseAgent:
    """Base implementation every future agent must inherit."""

    profile: AgentProfile

    def __init__(self, profile: AgentProfile, context: AgentContext | None = None) -> None:
        self.profile = profile
        self.context = context or AgentContext()
        self.state = AgentState.CREATED
        self.status = AgentStatus.IDLE
        self.metrics = context.metrics if context and context.metrics else AgentMetrics()
        self.health_state = context.health if context and context.health else AgentHealth()
        self.logger = context.logger if context and context.logger else None
        self.task_queue: list[Any] = []
        self.session = context.current_session if context else None
        self.checkpoint_data: AgentCheckpoint | None = None
        self.created_at = datetime.now(timezone.utc)
        self.last_started: datetime | None = None
        self.last_stopped: datetime | None = None
        self.last_heartbeat: datetime | None = None
        self.last_error: str | None = None
        self.recovery_count = 0
        self.execution_count = 0
        self.failure_count = 0
        self.memory_usage = 0.0
        self.cpu_usage = 0.0
        self.execution_time = 0.0

    @property
    def agent_id(self) -> str:
        """Return unique agent ID."""
        return self.profile.agent_id

    def transition_to(self, state: AgentState) -> None:
        """Validate and apply a lifecycle transition."""
        validate_transition(self.state, state)
        self.state = state

    def initialize(self) -> None:
        """Initialize the agent interface."""
        self.transition_to(AgentState.INITIALIZED)
        self.status = AgentStatus.INITIALIZING

    def configure(self, configuration: dict[str, Any] | None = None) -> None:
        """Attach configuration values to the profile-compatible runtime."""
        if configuration:
            self.profile.configuration.update(configuration)  # type: ignore[attr-defined]

    def start(self) -> None:
        """Start the agent without executing work."""
        if self.state is AgentState.INITIALIZED:
            self.transition_to(AgentState.READY)
        self.transition_to(AgentState.RUNNING)
        self.status = AgentStatus.RUNNING
        self.last_started = datetime.now(timezone.utc)

    def pause(self) -> None:
        """Pause the agent."""
        self.transition_to(AgentState.PAUSED)
        self.status = AgentStatus.PAUSED

    def resume(self) -> None:
        """Resume the agent."""
        self.transition_to(AgentState.RUNNING)
        self.status = AgentStatus.RUNNING

    def stop(self) -> None:
        """Stop the agent."""
        self.transition_to(AgentState.STOPPED)
        self.status = AgentStatus.STOPPED
        self.last_stopped = datetime.now(timezone.utc)

    def shutdown(self) -> None:
        """Shutdown the agent."""
        self.transition_to(AgentState.SHUTDOWN)
        self.status = AgentStatus.STOPPED

    def restart(self) -> None:
        """Restart the agent lifecycle."""
        self.transition_to(AgentState.RESTARTING)
        self.metrics.restart_count += 1
        self.transition_to(AgentState.READY)

    def heartbeat(self) -> None:
        """Record heartbeat."""
        self.health_state.heartbeat()
        self.last_heartbeat = self.health_state.last_heartbeat

    def health(self) -> AgentHealth:
        """Return health state."""
        return self.health_state

    def checkpoint(self) -> AgentCheckpoint:
        """Create a checkpoint."""
        checkpoint = AgentCheckpoint(agent_id=self.agent_id, state=self.state.value)
        self.checkpoint_data = checkpoint
        if self.context.checkpoint_store is not None:
            self.context.checkpoint_store.save(checkpoint)
        return checkpoint

    def restore(self, checkpoint: AgentCheckpoint) -> None:
        """Restore checkpoint metadata only."""
        self.checkpoint_data = checkpoint
        self.state = AgentState(checkpoint.state)

    def cleanup(self) -> None:
        """Cleanup runtime placeholders."""
        self.task_queue.clear()

    def execute(self, payload: dict[str, Any] | None = None) -> AgentResult:
        """Future execution interface; no work is performed."""
        self.execution_count += 1
        self.metrics.execution_count += 1
        return AgentResult(agent_id=self.agent_id, success=True, output=payload or {})

    def validate(self) -> bool:
        """Validate basic agent metadata."""
        return bool(self.profile.agent_id and self.profile.name)

    def load(self) -> None:
        """Load agent placeholder."""

    def unload(self) -> None:
        """Unload agent placeholder."""

    def sleep(self) -> None:
        """Put the agent to sleep."""
        self.transition_to(AgentState.SLEEPING)

    def wake(self) -> None:
        """Wake a sleeping agent."""
        self.transition_to(AgentState.READY)

    def on_event(self, event: Any) -> None:
        """Receive an event."""

    def on_message(self, message: AgentMessage) -> None:
        """Receive a message."""
        self.metrics.messages_received += 1
