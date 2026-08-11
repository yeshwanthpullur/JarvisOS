"""Manager for the Executive JARVIS Core."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from jarvis.jarvis_cache import JarvisCache
from jarvis.jarvis_context import JarvisContext
from jarvis.agents import AgentRegistry, PrimeAgent, register_specialist_agents
from jarvis.models import ModelRouter, build_default_model_registry
from jarvis.skills import build_default_skill_registry
from jarvis.research import ResearchAgent, ResearchEvidenceCollector, ResearchHistoryStore, ResearchPlanner
from jarvis.knowledge import InMemoryKnowledgeIndex
from jarvis.coding import CodingAgent, CodingHistoryStore, CodingPlanner, DiffReviewer, RepoInspector
from jarvis.integrations import ExternalIntegrationControlPlane
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
from jarvis.jarvis_tools import JarvisTools, ToolLimits
from jarvis.autonomous_planning import AutonomousPlanning, PlanningLimits
from jarvis.voice_intelligence import VoiceIntelligence
from jarvis.vision_intelligence import VisionIntelligence
from jarvis.image_generation import ImageGenerationManager
from jarvis.video_editing import VideoEditingManager
from jarvis.sync_intelligence import SyncIntelligence
from jarvis.web_automation import WebAutomationManager
from jarvis.mobile_automation import MobileAutomationManager
from jarvis.jarvis_validator import JarvisValidator
from reasoning import ReasoningManager
from reflection import ReflectionManager
from adaptive import AdaptiveManager
from personal_intelligence import PersonalIntelligenceManager
from goal_intelligence import GoalIntelligenceManager
from context_intelligence import ContextIntelligenceManager
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
    context_intelligence_status: str
    goal_intelligence_status: str
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
        context_manager = context.metadata.get("context_intelligence_manager") if context else None
        self.context_intelligence = (
            context_manager if isinstance(context_manager, ContextIntelligenceManager) else None
        )
        goal_manager = context.metadata.get("goal_intelligence_manager") if context else None
        self.goal_intelligence = goal_manager if isinstance(goal_manager, GoalIntelligenceManager) else None
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
        self.tools = JarvisTools(
            storage_dir=(context.settings.data_dir / "tool-intelligence") if context and context.settings else None,
            logger=self.logger,
            limits=ToolLimits(**{key: getattr(context.settings.tools, key) for key in context.settings.tools.__slots__}) if context and context.settings else None,
        )
        self.autonomous_planning = AutonomousPlanning(
            storage_dir=(context.settings.data_dir / "autonomous-planning") if context and context.settings else None,
            tool_manager=self.tools,
            agent_manager=context.agent_manager if context else None,
            logger=self.logger,
            limits=PlanningLimits(**{key:getattr(context.settings.planning,key) for key in context.settings.planning.__slots__}) if context and context.settings else None,
        )
        self.voice_intelligence = VoiceIntelligence(context.settings if context else None,(context.settings.data_dir / "voice") if context and context.settings else None,self.logger)
        self.vision_intelligence = VisionIntelligence(
            context.settings if context else None,
            context.metadata.get("provider_manager") if context else None,
            self.logger,
            (context.settings.data_dir / "vision") if context and context.settings else None,
        )
        self.image_generation = ImageGenerationManager(
            (context.settings.data_dir / "image_generation") if context and context.settings else Path("data/image_generation"),
            context.settings if context else None,
        )
        self.video_editing = VideoEditingManager(
            (context.settings.data_dir / "video_editing") if context and context.settings else Path("data/video_editing"),
            context.settings if context else None,
        )
        self.sync_intelligence = SyncIntelligence((context.settings.data_dir / "sync") if context and context.settings else Path("data/sync"), context.settings if context else None, self.logger)
        self.web_automation = WebAutomationManager((context.settings.data_dir / "web-automation") if context and context.settings else Path("data/web-automation"), context.settings if context else None, logger=self.logger)
        self.mobile_automation = MobileAutomationManager((context.settings.data_dir / "mobile-automation") if context and context.settings else Path("data/mobile-automation"), context.settings if context else None, logger=self.logger)
        research_config = getattr(context.settings, "research", None) if context else None
        research_enabled = getattr(research_config, "enabled", True)
        web_config = getattr(context.settings, "web_automation", None) if context else None
        research_web_available = bool(
            research_enabled
            and getattr(research_config, "allow_web_read_only", True)
            and getattr(web_config, "enabled", True)
            and getattr(web_config, "mode", "read_only") == "read_only"
        )
        research_documents_available = bool(context and (context.knowledge_manager or context.memory_manager))
        self.research_agent = ResearchAgent(
            enabled=research_enabled,
            web_available=research_web_available,
            documents_available=research_documents_available,
            planner=ResearchPlanner(
                max_steps=getattr(research_config, "max_plan_steps", 5),
                max_evidence_items=getattr(research_config, "max_evidence_items", 5),
                max_snippet_chars=getattr(research_config, "max_snippet_chars", 320),
                max_summary_chars=getattr(research_config, "max_summary_chars", 1200),
                save_history=getattr(research_config, "save_history", True),
                web_available=research_web_available,
                documents_available=research_documents_available,
            ),
            evidence_collector=ResearchEvidenceCollector(getattr(research_config, "max_snippet_chars", 320)),
            history_store=ResearchHistoryStore((context.settings.data_dir / "research") if context and context.settings else Path("data/research")),
            local_only=getattr(research_config, "local_only", True),
            external_search_api_enabled=getattr(research_config, "allow_external_search_api", False),
            require_citations_for_web_claims=getattr(research_config, "require_citations_for_web_claims", True),
            default_depth=getattr(research_config, "default_depth", "standard"),
        )
        self.research_agent.runtime.allow_external_search = getattr(research_config, "allow_external_search", False)
        self.research_agent.runtime.allow_browser_retrieval = getattr(research_config, "allow_browser_retrieval", True)
        self.research_agent.runtime.allow_github = getattr(research_config, "allow_github", True)
        self.research_agent.runtime.allow_mcp = getattr(research_config, "allow_mcp", True)
        self.research_agent.runtime.allow_plugins = getattr(research_config, "allow_plugins", True)
        knowledge_config = getattr(context.settings, "knowledge_index", None) if context else None
        self.knowledge_index = InMemoryKnowledgeIndex(max_chunk_chars=getattr(knowledge_config,"max_chunk_chars",800),overlap_chars=getattr(knowledge_config,"chunk_overlap_chars",80),max_chunks_per_record=getattr(knowledge_config,"max_chunks_per_record",50))
        coding_config = getattr(context.settings, "coding", None) if context else None
        coding_root = context.settings.base_dir if context and context.settings else Path.cwd()
        coding_max_files = getattr(coding_config, "max_files_listed", 20)
        self.coding_agent = CodingAgent(
            repo_inspector=RepoInspector(coding_root, coding_max_files),
            diff_reviewer=DiffReviewer(coding_root, coding_max_files, getattr(coding_config, "max_diff_chars", 4000)),
            planner=CodingPlanner(getattr(coding_config, "max_plan_steps", 6), coding_max_files),
            history_store=CodingHistoryStore((context.settings.data_dir / "coding") if context and context.settings else Path("data/coding"), getattr(coding_config, "max_history_items", 25)),
            enabled=getattr(coding_config, "enabled", True),
            default_mode=getattr(coding_config, "default_mode", "plan_only"),
            allow_write_operations=getattr(coding_config, "allow_write_operations", False),
            allow_command_execution=getattr(coding_config, "allow_command_execution", False),
            require_approval_for_write=getattr(coding_config, "require_approval_for_write", True),
            require_approval_for_push=getattr(coding_config, "require_approval_for_push", True),
            block_secrets_access=getattr(coding_config, "block_secrets_access", True),
            max_history_items=getattr(coding_config, "max_history_items", 25),
        )
        agent_limit = getattr(getattr(context.settings, "agents", None), "max_agents", 64) if context else 64
        self.agent_registry = AgentRegistry(max_agents=agent_limit)
        provider_manager = context.metadata.get("provider_manager") if context else None
        ollama_record = getattr(getattr(provider_manager, "registry", None), "get", lambda _name: None)("ollama")
        ollama_ready = bool(ollama_record and ollama_record.health and ollama_record.health.available)
        stored_models = tuple(
            getattr(item, "model_id", "")
            for item in getattr(getattr(ollama_record, "provider", None), "_models", ())
            if getattr(item, "model_id", "")
        )
        vision_ready = any("llava" in model.lower() for model in stored_models)
        self.model_registry = build_default_model_registry(ollama_ready=ollama_ready, ollama_models=stored_models, vision_ready=vision_ready)
        model_config = getattr(context.settings, "models", None) if context else None
        self.model_router = ModelRouter(
            self.model_registry,
            local_only_default=getattr(model_config, "local_only_default", True),
            allow_cloud_providers=getattr(model_config, "allow_cloud_providers", False),
        )
        self.skill_registry = build_default_skill_registry()
        self.external_integrations = ExternalIntegrationControlPlane()
        from jarvis.integrations.telegram import TelegramPolicy, TelegramRuntime
        telegram_config=getattr(context.settings,"telegram",None) if context else None
        self.telegram_runtime=TelegramRuntime(policy=TelegramPolicy(**{name:getattr(telegram_config,name) for name in TelegramPolicy.__dataclass_fields__}) if telegram_config else TelegramPolicy())
        register_specialist_agents(self.agent_registry, vision_ready=vision_ready)
        prime_config = getattr(context.settings, "prime", None) if context else None
        self.prime_agent = PrimeAgent(
            self.agent_registry,
            model_router=self.model_router,
            skill_registry=self.skill_registry,
            enabled=getattr(prime_config, "enabled", True),
            max_plan_steps=getattr(prime_config, "max_plan_steps", 8),
            block_critical_risk=getattr(prime_config, "block_critical_risk", True),
        )
        self.skills = JarvisSkills()
        workflow_config = getattr(context.settings, "workflow", None) if context else None
        from workflow import WorkflowLimits
        self.workflow = WorkflowManager(limits=WorkflowLimits(
            max_active=getattr(workflow_config, "max_active", 4),
            max_parallel_steps=getattr(workflow_config, "max_parallel_steps", 2),
            max_pending=getattr(workflow_config, "max_pending", 25),
            default_timeout_seconds=getattr(workflow_config, "default_timeout_seconds", 300),
            max_retry_count=getattr(workflow_config, "max_retry_count", 2),
            default_checkpoint_interval=getattr(workflow_config, "default_checkpoint_interval", 1),
            max_event_history=getattr(workflow_config, "max_event_history", 200),
            max_checkpoint_history=getattr(workflow_config, "max_checkpoint_history", 50),
            max_artifacts=getattr(workflow_config, "max_artifacts", 50),
            max_runtime_hours=getattr(workflow_config, "max_runtime_hours", 4),
        ))
        self.prime_agent.workflow_runtime = self.workflow.runtime
        coordinating_manager = context.agent_manager if context else None
        coordinating_orchestrator = getattr(coordinating_manager, "orchestrator", None)
        if coordinating_orchestrator is not None:
            coordinating_orchestrator.workflow_runtime = self.workflow.runtime
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
            "autonomous_planning": self.autonomous_planning,
            "voice_intelligence": self.voice_intelligence,
            "vision_intelligence": self.vision_intelligence,
            "image_generation": self.image_generation,
            "video_editing": self.video_editing,
            "sync_intelligence": self.sync_intelligence,
            "web_automation": self.web_automation,
            "research_agent": self.research_agent,
            "knowledge_index": self.knowledge_index,
            "coding_agent": self.coding_agent,
            "mobile_automation": self.mobile_automation,
            "agent_registry": self.agent_registry,
            "prime_agent": self.prime_agent,
            "model_registry": self.model_registry,
            "model_router": self.model_router,
            "skill_registry": self.skill_registry,
            "external_integrations": self.external_integrations,
            "telegram_runtime": self.telegram_runtime,
            "skills": self.skills,
            "workflow": self.workflow,
            "retrieval": self.retrieval,
            "reasoning": self.reasoning,
            "reflection": self.reflection,
            "adaptive": self.adaptive,
            "personal_intelligence": self.personal_intelligence,
            "context_intelligence": self.context_intelligence,
            "goal_intelligence": self.goal_intelligence,
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
        self.voice_intelligence.shutdown()
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
            context_intelligence_status="ready" if self.context_intelligence and self.context_intelligence.initialized else "unavailable",
            goal_intelligence_status="ready" if self.goal_intelligence and self.goal_intelligence.initialized else "unavailable",
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
            provider_execution_manager=base.metadata.get("provider_execution_manager") if base else None,
            provider_router=base.provider_router if base else None,
            agent_manager=base.agent_manager if base else None,
            agent_creator=base.agent_creator if base else None,
            agent_registry=self.agent_registry,
            prime_agent=self.prime_agent,
            model_registry=self.model_registry,
            model_router=self.model_router,
            skill_registry=self.skill_registry,
            research_agent=self.research_agent,
            coding_agent=self.coding_agent,
            tool_manager=self.tools,
            autonomous_planning=self.autonomous_planning,
            voice_intelligence=self.voice_intelligence,
            vision_intelligence=self.vision_intelligence,
            image_generation=self.image_generation,
            video_editing=self.video_editing,
            sync_intelligence=self.sync_intelligence,
            web_automation=self.web_automation,
            mobile_automation=self.mobile_automation,
            logger=self.logger,
            metadata={**(base.metadata if base else {}), "external_integrations": self.external_integrations, "telegram_runtime": self.telegram_runtime, "workflow_runtime": self.workflow.runtime, **request.metadata},
        )
