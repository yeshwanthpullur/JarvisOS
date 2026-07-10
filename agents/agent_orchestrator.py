"""Agent orchestration interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.agent_goal import AgentGoal
from agents.agent_result import AgentResult
from agents.agent_task import AgentTask


@dataclass(frozen=True, slots=True)
class AgentOrchestrationPlan:
    """Future orchestration plan."""

    goal: AgentGoal
    tasks: tuple[AgentTask, ...] = ()
    dependencies: dict[str, tuple[str, ...]] = field(default_factory=dict)


class AgentOrchestrator:
    """Coordinates future multi-agent work without planning logic."""

    def __init__(self) -> None:
        self.initialized = True

    def receive_objective(self, goal: AgentGoal) -> AgentOrchestrationPlan:
        """Receive an objective and return an empty plan shell."""
        return AgentOrchestrationPlan(goal=goal)

    def assign_tasks(self, plan: AgentOrchestrationPlan) -> tuple[AgentTask, ...]:
        """Return plan tasks for future assignment."""
        return plan.tasks

    def collect_results(self, results: tuple[AgentResult, ...]) -> tuple[AgentResult, ...]:
        """Collect results without merging logic."""
        return results
