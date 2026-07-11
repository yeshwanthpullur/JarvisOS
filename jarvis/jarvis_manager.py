"""Manager for the Executive JARVIS Core."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from jarvis.jarvis_cache import JarvisCache
from jarvis.jarvis_context import JarvisContext
from jarvis.jarvis_controller import JarvisController
from jarvis.jarvis_department_registry import JarvisDepartmentRegistry
from jarvis.jarvis_diagnostics import JarvisDiagnostics
from jarvis.jarvis_event_bus import JarvisEventBus
from jarvis.jarvis_goal_manager import JarvisGoalManager
from jarvis.jarvis_health import JarvisHealth
from jarvis.jarvis_history import JarvisHistory
from jarvis.jarvis_knowledge import JarvisKnowledge
from jarvis.jarvis_logger import JarvisLogger
from jarvis.jarvis_memory import JarvisMemory
from jarvis.jarvis_metrics import JarvisMetrics
from jarvis.jarvis_plugins import JarvisPlugins
from jarvis.jarvis_profile import JarvisProfile
from jarvis.jarvis_providers import JarvisProviders
from jarvis.jarvis_recovery_manager import JarvisRecoveryManager
from jarvis.jarvis_registry import JarvisRegistry
from jarvis.jarvis_request import JarvisRequest
from jarvis.jarvis_response import JarvisResponse
from jarvis.jarvis_runtime import JarvisRuntime
from jarvis.jarvis_skills import JarvisSkills
from jarvis.jarvis_tasks import JarvisTasks
from jarvis.jarvis_tools import JarvisTools
from jarvis.jarvis_validator import JarvisValidator
from reasoning import ReasoningManager
from reflection import ReflectionManager
from adaptive import AdaptiveManager
from personal_intelligence import PersonalIntelligenceManager
from retrieval import RetrievalManager
from workflow import WorkflowManager


@dataclass(frozen=True, slots=True)
class JarvisExecutiveStatistics:
    """Startup and runtime statistics for Executive JARVIS."""

    runtime_status: str
    manager_status: str
    controller_status: str
    decision_engine_status: str
    intent_engine_status: str
    dispatcher_status: str
    planning_status: str
    reasoning_status: str
    reflection_status: str
    adaptive_status: str
    personal_intelligence_status: str
    providers_status: str
    memory_status: str
    knowledge_status: str
    tasks_status: str
    plugins_status: str
    tools_status: str
    skills_status: str
    workflow_status: str
    retrieval_status: str
    departments: int
    requests: int
    health_status: str


class JarvisManager:
    """Composes Executive JARVIS components and handles requests."""

    def __init__(
        self,
        context: JarvisContext | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.base_context = context
        self.profile = JarvisProfile()
        self.runtime = JarvisRuntime()
        self.registry = JarvisRegistry()
        self.event_bus = JarvisEventBus(self.logger)
        reasoning_manager = context.metadata.get("reasoning_manager") if context else None
        self.reasoning = reasoning_manager if isinstance(reasoning_manager, ReasoningManager) else ReasoningManager()
        reflection_manager = context.metadata.get("reflection_manager") if context else None
        self.reflection = reflection_manager if isinstance(reflection_manager, ReflectionManager) else ReflectionManager()
        adaptive_manager = context.metadata.get("adaptive_manager") if context else None
        self.adaptive = adaptive_manager if isinstance(adaptive_manager, AdaptiveManager) else AdaptiveManager()
        personal_manager = context.metadata.get("personal_intelligence_manager") if context else None
        self.personal_intelligence = (
            personal_manager if isinstance(personal_manager, PersonalIntelligenceManager) else None
        )
        self.controller = JarvisController(reasoning_manager=self.reasoning)
        self.memory = JarvisMemory(context.memory_manager if context else None)
        self.knowledge = JarvisKnowledge(
            context.knowledge_manager if context else None,
            context.brain_manager if context else None,
        )
        self.tasks = JarvisTasks(context.task_manager if context else None)
        self.plugins = JarvisPlugins(context.plugin_manager if context else None)
        self.providers = JarvisProviders(
            context.provider_router if context else None,
            context.metadata.get("provider_manager") if context else None,
            context.metadata.get("provider_execution_manager") if context else None,
        )
        self.tools = JarvisTools()
        self.skills = JarvisSkills()
        self.workflow = WorkflowManager()
        self.retrieval = RetrievalManager()
        self.department_registry = JarvisDepartmentRegistry()
        self.metrics = JarvisMetrics()
        self.health = JarvisHealth()
        self.logger_factory = JarvisLogger()
        self.validator = JarvisValidator()
        self.cache = JarvisCache()
        self.history = JarvisHistory()
        self.goals = JarvisGoalManager()
        self.recovery = JarvisRecoveryManager()
        self.diagnostics = JarvisDiagnostics()
        self.initialized = False

    def initialize(self) -> JarvisExecutiveStatistics:
        """Initialize Executive JARVIS."""
        self.runtime.initialize()
        self.runtime.start()
        if not self.reasoning.initialized:
            self.reasoning.initialize()
        if not self.reflection.initialized:
            self.reflection.initialize()
        if not self.adaptive.initialized:
            self.adaptive.initialize()
        self.department_registry.load_defaults()
        self.metrics.startup_count += 1
        self.health.heartbeat()
        self.initialized = True
        for key, component in {
            "runtime": self.runtime,
            "controller": self.controller,
            "memory": self.memory,
            "knowledge": self.knowledge,
            "tasks": self.tasks,
            "plugins": self.plugins,
            "providers": self.providers,
            "tools": self.tools,
            "skills": self.skills,
            "workflow": self.workflow,
            "retrieval": self.retrieval,
            "reasoning": self.reasoning,
            "reflection": self.reflection,
            "adaptive": self.adaptive,
            "personal_intelligence": self.personal_intelligence,
            "departments": self.department_registry,
        }.items():
            self.registry.register(key, component, "executive")
        self.logger.info("jarvis_executive_initialized departments=%s", len(self.department_registry.list_departments()))
        return self.statistics()

    def handle_request(self, request: JarvisRequest) -> JarvisResponse:
        """Handle a request through the Executive Core."""
        self.metrics.requests += 1
        context = self._context_for_request(request)
        response = self.controller.handle(request, context)
        self.history.add(response)
        return response

    def shutdown(self) -> None:
        """Shutdown Executive JARVIS."""
        if self.runtime.state.value != "shutdown":
            self.runtime.shutdown()
        self.initialized = False

    def statistics(self) -> JarvisExecutiveStatistics:
        """Return Executive statistics."""
        return JarvisExecutiveStatistics(
            runtime_status=self.runtime.state.value,
            manager_status="ready" if self.initialized else "unavailable",
            controller_status="ready" if self.controller.initialized else "unavailable",
            decision_engine_status="ready" if self.controller.decision_engine.initialized else "unavailable",
            intent_engine_status="ready" if self.controller.intent_engine.initialized else "unavailable",
            dispatcher_status="ready" if self.controller.dispatcher.initialized else "unavailable",
            planning_status="ready" if self.controller.planning.initialized else "unavailable",
            reasoning_status="ready" if self.reasoning.initialized else "unavailable",
            reflection_status="ready" if self.reflection.initialized else "unavailable",
            adaptive_status="ready" if self.adaptive.initialized else "unavailable",
            personal_intelligence_status="ready" if self.personal_intelligence and self.personal_intelligence.initialized else "unavailable",
            providers_status="ready" if self.providers.initialized else "unavailable",
            memory_status="ready" if self.memory.initialized else "unavailable",
            knowledge_status="ready" if self.knowledge.initialized else "unavailable",
            tasks_status="ready" if self.tasks.initialized else "unavailable",
            plugins_status="ready" if self.plugins.initialized else "unavailable",
            tools_status="ready" if self.tools.initialized else "unavailable",
            skills_status="ready" if self.skills.initialized else "unavailable",
            workflow_status="ready" if self.workflow.initialized else "unavailable",
            retrieval_status="ready" if self.retrieval.initialized else "unavailable",
            departments=len(self.department_registry.list_departments()),
            requests=self.metrics.requests,
            health_status=self.health.status.value,
        )

    def _context_for_request(self, request: JarvisRequest) -> JarvisContext:
        base = self.base_context
        return JarvisContext(
            request_id=request.request_id,
            conversation_id=request.conversation_id,
            settings=base.settings if base else None,
            memory_manager=base.memory_manager if base else None,
            knowledge_manager=base.knowledge_manager if base else None,
            brain_manager=base.brain_manager if base else None,
            task_manager=base.task_manager if base else None,
            plugin_manager=base.plugin_manager if base else None,
            provider_router=base.provider_router if base else None,
            agent_manager=base.agent_manager if base else None,
            agent_creator=base.agent_creator if base else None,
            logger=self.logger,
        )
