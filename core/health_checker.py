"""Reusable health checks for the JARVIS OS bootstrap."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Callable, Iterable, Mapping

from config.schema import AppSettings


class HealthStatus(StrEnum):
    """Possible health result states."""

    PASSING = "passing"
    WARNING = "warning"
    FAILING = "failing"


@dataclass(frozen=True, slots=True)
class HealthResult:
    """Structured result for a single health check."""

    name: str
    status: HealthStatus
    message: str
    details: Mapping[str, object] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recommendation: str | None = None


class HealthChecker:
    """Runs reusable health checks for bootstrapped modules."""

    def __init__(
        self,
        settings: AppSettings,
        required_directories: Iterable[Path],
        module_checks: Mapping[str, Callable[[], bool]],
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._required_directories = tuple(required_directories)
        self._module_checks = module_checks
        self._logger = logger or logging.getLogger(__name__)

    def run_all(self) -> tuple[HealthResult, ...]:
        """Run all bootstrap health checks."""
        checks = (
            self.check_configuration(),
            self.check_logging(),
            self.check_directories(),
            self.check_module("memory", "Memory"),
            self.check_module("brain", "Obsidian Brain"),
            self.check_module("knowledge", "Knowledge Engine"),
            self.check_module("tasks", "Task Engine"),
            self.check_module("providers", "Providers"),
            self.check_module("provider_execution_manager", "Provider Execution Manager"),
            self.check_module("provider_execution_context", "Provider Execution Context"),
            self.check_module("provider_execution_request", "Provider Execution Request"),
            self.check_module("provider_execution_response", "Provider Execution Response"),
            self.check_module("execution_strategy", "Execution Strategy"),
            self.check_module("provider_execution", "Provider Execution Framework"),
            self.check_module("provider_selector", "Provider Selector"),
            self.check_module("model_selector", "Model Selector"),
            self.check_module("provider_capabilities", "Provider Capabilities"),
            self.check_module("provider_metrics", "Provider Metrics"),
            self.check_module("provider_benchmark", "Provider Benchmark"),
            self.check_module("provider_execution_registry", "Provider Execution Registry"),
            self.check_module("provider_execution_history", "Provider Execution History"),
            self.check_module("provider_execution_cache", "Provider Execution Cache"),
            self.check_module("provider_recovery", "Provider Recovery"),
            self.check_module("provider_diagnostics", "Provider Diagnostics"),
            self.check_module("provider_validator", "Provider Validator"),
            self.check_module("workflow_engine", "Workflow Engine"),
            self.check_module("workflow_manager", "Workflow Manager"),
            self.check_module("workflow_registry", "Workflow Registry"),
            self.check_module("workflow_builder", "Workflow Builder"),
            self.check_module("workflow_executor", "Workflow Executor"),
            self.check_module("workflow_dispatcher", "Workflow Dispatcher"),
            self.check_module("workflow_scheduler", "Workflow Scheduler"),
            self.check_module("workflow_checkpoint", "Workflow Checkpoint"),
            self.check_module("workflow_recovery", "Workflow Recovery"),
            self.check_module("workflow_metrics", "Workflow Metrics"),
            self.check_module("workflow_diagnostics", "Workflow Diagnostics"),
            self.check_module("retrieval_manager", "Retrieval Manager"),
            self.check_module("retrieval_engine", "Retrieval Engine"),
            self.check_module("retrieval_selector", "Retrieval Selector"),
            self.check_module("retrieval_ranker", "Retrieval Ranker"),
            self.check_module("retrieval_cache", "Retrieval Cache"),
            self.check_module("retrieval_validator", "Retrieval Validator"),
            self.check_module("retrieval_metrics", "Retrieval Metrics"),
            self.check_module("retrieval_diagnostics", "Retrieval Diagnostics"),
            self.check_module("personal_intelligence", "Personal Intelligence"),
            self.check_module("personal_memory", "Personal Memory"),
            self.check_module("personal_retrieval", "Personal Retrieval"),
            self.check_module("context_intelligence", "Context Intelligence"),
            self.check_module("conversation_context", "Conversation Context"),
            self.check_module("context_retrieval", "Context Retrieval"),
            self.check_module("reference_resolution", "Reference Resolution"),
            self.check_module("continuation_readiness", "Continuation Readiness"),
            self.check_module("goal_intelligence", "Goal Intelligence"),
            self.check_module("goal_analysis", "Goal Analysis"),
            self.check_module("goal_decomposition", "Goal Decomposition"),
            self.check_module("goal_progress", "Goal Progress"),
            self.check_module("goal_reference_resolution", "Goal Reference Resolution"),
            self.check_module("task_intelligence", "Task Intelligence"),
            self.check_module("project_manager", "Project Manager"),
            self.check_module("goal_manager", "Goal Manager"),
            self.check_module("milestone_manager", "Milestone Manager"),
            self.check_module("priority_engine", "Priority Engine"),
            self.check_module("schedule_engine", "Schedule Engine"),
            self.check_module("dependency_manager", "Dependency Manager"),
            self.check_module("progress_tracker", "Progress Tracker"),
            self.check_module("task_dashboard", "Task Dashboard"),
            self.check_module("task_templates", "Task Templates"),
            self.check_module("task_metrics", "Task Metrics"),
            self.check_module("task_diagnostics", "Task Diagnostics"),
            self.check_module("research", "Research Engine"),
            self.check_module("research_engine", "Research Engine Core"),
            self.check_module("research_planner", "Research Planner"),
            self.check_module("research_summarizer", "Research Summarizer"),
            self.check_module("knowledge_builder", "Knowledge Builder"),
            self.check_module("learning_engine", "Learning Engine"),
            self.check_module("learning_planner", "Learning Planner"),
            self.check_module("research_validator", "Research Validator"),
            self.check_module("research_metrics", "Research Metrics"),
            self.check_module("research_diagnostics", "Research Diagnostics"),
            self.check_module("reasoning", "Reasoning Engine"),
            self.check_module("reasoning_engine", "Reasoning Engine Core"),
            self.check_module("decision_engine", "Decision Engine"),
            self.check_module("planning_engine", "Planning Engine"),
            self.check_module("goal_decomposer", "Goal Decomposer"),
            self.check_module("option_generator", "Option Generator"),
            self.check_module("evaluation_engine", "Evaluation Engine"),
            self.check_module("confidence_engine", "Confidence Engine"),
            self.check_module("reflection", "Reflection Engine"),
            self.check_module("reflection_engine", "Reflection Engine Core"),
            self.check_module("reflection_analyzer", "Reflection Analyzer"),
            self.check_module("reflection_learning", "Reflection Learning"),
            self.check_module("reflection_patterns", "Reflection Patterns"),
            self.check_module("reflection_confidence", "Reflection Confidence"),
            self.check_module("reflection_improvement", "Reflection Improvement"),
            self.check_module("reflection_registry", "Reflection Registry"),
            self.check_module("reflection_metrics", "Reflection Metrics"),
            self.check_module("reflection_diagnostics", "Reflection Diagnostics"),
            self.check_module("adaptive", "Adaptive Intelligence"),
            self.check_module("adaptive_engine", "Adaptive Engine"),
            self.check_module("adaptive_experience", "Adaptive Experience"),
            self.check_module("adaptive_policy", "Adaptive Policy"),
            self.check_module("adaptive_rules", "Adaptive Rules"),
            self.check_module("adaptive_learning_queue", "Adaptive Learning Queue"),
            self.check_module("adaptive_registry", "Adaptive Registry"),
            self.check_module("adaptive_metrics", "Adaptive Metrics"),
            self.check_module("adaptive_diagnostics", "Adaptive Diagnostics"),
            self.check_module("plugins", "Plugin Framework"),
            self.check_module("agent_framework", "Agent Framework"),
            self.check_module("agent_registry", "Agent Registry"),
            self.check_module("agent_manager", "Agent Manager"),
            self.check_module("agent_scheduler", "Agent Scheduler"),
            self.check_module("agent_router", "Agent Router"),
            self.check_module("agent_supervisor", "Agent Supervisor"),
            self.check_module("agent_orchestrator", "Agent Orchestrator"),
            self.check_module("agent_metrics", "Agent Metrics"),
            self.check_module("agent_health", "Agent Health"),
            self.check_module("agent_bus", "Agent Bus"),
            self.check_module("agent_creator", "Agent Creator"),
            self.check_module("blueprint_registry", "Blueprint Registry"),
            self.check_module("template_registry", "Template Registry"),
            self.check_module("template_loader", "Template Loader"),
            self.check_module("agent_generator", "Agent Generator"),
            self.check_module("agent_installer", "Agent Installer"),
            self.check_module("agent_validator", "Agent Validator"),
            self.check_module("agent_wizard", "Agent Wizard"),
            self.check_module("rollback_manager", "Rollback Manager"),
            self.check_module("catalog", "Catalog"),
            self.check_module("department_manager", "Department Manager"),
            self.check_module("department_registry", "Department Registry"),
            self.check_module("policy_engine", "Policy Engine"),
            self.check_module("audit_manager", "Audit Manager"),
            self.check_module("jarvis_runtime", "JARVIS Runtime"),
            self.check_module("jarvis_manager", "JARVIS Manager"),
            self.check_module("jarvis_controller", "JARVIS Controller"),
            self.check_module("jarvis_decision_engine", "JARVIS Decision Engine"),
            self.check_module("jarvis_intent_engine", "JARVIS Intent Engine"),
            self.check_module("jarvis_dispatcher", "JARVIS Dispatcher"),
            self.check_module("jarvis_planning", "JARVIS Planning"),
            self.check_module("jarvis_reasoning", "JARVIS Reasoning"),
            self.check_module("jarvis_providers", "JARVIS Providers"),
            self.check_module("jarvis_memory", "JARVIS Memory"),
            self.check_module("jarvis_knowledge", "JARVIS Knowledge"),
            self.check_module("jarvis_tasks", "JARVIS Tasks"),
            self.check_module("jarvis_plugins", "JARVIS Plugins"),
            self.check_module("jarvis_tools", "JARVIS Tools"),
            self.check_module("jarvis_skills", "JARVIS Skills"),
            self.check_module("jarvis_departments", "JARVIS Departments"),
            self.check_module("jarvis_validator", "JARVIS Validator"),
            self.check_module("jarvis_metrics", "JARVIS Metrics"),
            self.check_module("jarvis_diagnostics", "JARVIS Diagnostics"),
            self.check_module("jarvis_recovery", "JARVIS Recovery"),
            self.check_module("jarvis_health", "Overall Executive Health"),
            self.check_module("conversation_engine", "Conversation Engine"),
            self.check_module("command_engine", "Command Engine"),
            self.check_module("cli", "CLI"),
            self.check_module("request_builder", "Request Builder"),
            self.check_module("execution_planner", "Execution Planner"),
            self.check_module("response_pipeline", "Response Pipeline"),
            self.check_module("conversation_sessions", "Conversation Sessions"),
            self.check_module("command_registry", "Command Registry"),
            self.check_module("executive_conversation_health", "Overall Executive Conversation Health"),
        )
        for result in checks:
            self._logger.info(
                "health_check name=%s status=%s message=%s",
                result.name,
                result.status.value,
                result.message,
            )
        return checks

    def check_configuration(self) -> HealthResult:
        """Verify loaded configuration is structurally usable."""
        if not self._settings.app_name:
            return HealthResult(
                name="configuration",
                status=HealthStatus.FAILING,
                message="Application name is missing.",
            )
        return HealthResult(
            name="configuration",
            status=HealthStatus.PASSING,
            message="Configuration loaded.",
            details={
                "environment": self._settings.environment,
                "debug": self._settings.debug,
            },
        )

    def check_logging(self) -> HealthResult:
        """Verify logging directory and level are usable."""
        if not self._settings.logs_dir.exists():
            return HealthResult(
                name="logging",
                status=HealthStatus.FAILING,
                message="Logging directory does not exist.",
                details={"path": str(self._settings.logs_dir)},
            )
        return HealthResult(
            name="logging",
            status=HealthStatus.PASSING,
            message="Logging initialized.",
            details={
                "level": self._settings.log_level,
                "directory": str(self._settings.logs_dir),
            },
        )

    def check_directories(self) -> HealthResult:
        """Verify required directories exist."""
        missing = [
            str(path)
            for path in self._required_directories
            if not path.exists() or not path.is_dir()
        ]
        if missing:
            return HealthResult(
                name="directories",
                status=HealthStatus.FAILING,
                message="Required directories are missing.",
                details={"missing": tuple(missing)},
            )
        return HealthResult(
            name="directories",
            status=HealthStatus.PASSING,
            message="Required directories verified.",
            details={"count": len(self._required_directories)},
        )

    def check_module(self, module_key: str, display_name: str) -> HealthResult:
        """Verify a named bootstrap module reports itself as initialized."""
        check = self._module_checks.get(module_key)
        if check is None:
            return HealthResult(
                name=module_key,
                status=HealthStatus.WARNING,
                message=f"{display_name} check is not registered.",
            )

        if check():
            return HealthResult(
                name=module_key,
                status=HealthStatus.PASSING,
                message=f"{display_name} initialized.",
            )

        return HealthResult(
            name=module_key,
            status=HealthStatus.FAILING,
            message=f"{display_name} is not initialized.",
            recommendation=f"Initialize {display_name} during startup.",
        )
