"""Application startup orchestration and command loop."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from agents import AgentContext, AgentFrameworkStatistics, AgentManager
from agent_creator import AgentCreator, AgentCreatorContext, AgentCreatorStatistics
from brain import BrainManager, BrainStatistics
from config import configure_logging, load_settings
from conversation import ConversationManager, ConversationStatistics
from config.schema import AppSettings
from core.banner import display_banner
from core.health_checker import HealthChecker, HealthResult, HealthStatus
from core.system_status import APP_VERSION, SystemState, SystemStatus
from knowledge import KnowledgeManager, KnowledgeStatistics
from jarvis import JarvisContext, JarvisCore, JarvisExecutiveStatistics
from memory import MemoryManager, MemoryStatistics
from plugins import PluginFrameworkStatistics, PluginManager
from provider_execution import ExecutionManager, ProviderExecutionContext, ProviderExecutionStatistics
from providers import ProviderManager, ProviderRouter, ProviderRouterStatistics
from retrieval import RetrievalManager, RetrievalStatistics
from research import ResearchManager, ResearchStatistics
from reasoning import ReasoningManager, ReasoningStatistics
from reflection import ReflectionManager, ReflectionStatistics
from adaptive import AdaptiveManager, AdaptiveStatistics
from workflow import WorkflowManager, WorkflowStatistics
from task_intelligence import TaskIntelligenceManager, TaskIntelligenceStatistics
from tasks import TaskEngineStatistics, TaskManager


LOGGER = logging.getLogger(__name__)


class StartupManager:
    """Coordinates application boot, health checks, command loop, and shutdown."""

    def __init__(self) -> None:
        self.status = SystemStatus()
        self.settings: AppSettings | None = None
        self.memory_manager: MemoryManager | None = None
        self.brain_manager: BrainManager | None = None
        self.knowledge_manager: KnowledgeManager | None = None
        self.agent_manager: AgentManager | None = None
        self.provider_router: ProviderRouter | None = None
        self.provider_manager: ProviderManager | None = None
        self.provider_statistics: ProviderRouterStatistics | None = None
        self.provider_execution_manager: ExecutionManager | None = None
        self.provider_execution_statistics: ProviderExecutionStatistics | None = None
        self.plugin_manager: PluginManager | None = None
        self.task_manager: TaskManager | None = None
        self.workflow_manager: WorkflowManager | None = None
        self.retrieval_manager: RetrievalManager | None = None
        self.task_intelligence_manager: TaskIntelligenceManager | None = None
        self.research_manager: ResearchManager | None = None
        self.reasoning_manager: ReasoningManager | None = None
        self.reflection_manager: ReflectionManager | None = None
        self.adaptive_manager: AdaptiveManager | None = None
        self.health_results: tuple[HealthResult, ...] = ()
        self.memory_statistics: MemoryStatistics | None = None
        self.brain_statistics: BrainStatistics | None = None
        self.knowledge_statistics: KnowledgeStatistics | None = None
        self.plugin_statistics: PluginFrameworkStatistics | None = None
        self.task_statistics: TaskEngineStatistics | None = None
        self.workflow_statistics: WorkflowStatistics | None = None
        self.retrieval_statistics: RetrievalStatistics | None = None
        self.research_statistics: ResearchStatistics | None = None
        self.reasoning_statistics: ReasoningStatistics | None = None
        self.reflection_statistics: ReflectionStatistics | None = None
        self.adaptive_statistics: AdaptiveStatistics | None = None
        self.agent_statistics: AgentFrameworkStatistics | None = None
        self.agent_creator: AgentCreator | None = None
        self.agent_creator_statistics: AgentCreatorStatistics | None = None
        self.jarvis_core: JarvisCore | None = None
        self.jarvis_statistics: JarvisExecutiveStatistics | None = None
        self.conversation_manager: ConversationManager | None = None
        self.conversation_statistics: ConversationStatistics | None = None

    def run(self) -> int:
        """Run the application lifecycle until the command loop exits."""
        display_banner()
        try:
            self.start()
            self.command_loop()
            return 0
        except KeyboardInterrupt:
            print("\nShutdown requested.")
            LOGGER.info("Shutdown requested by keyboard interrupt.")
            return 0
        except Exception:
            self.status.set_state(SystemState.FAILED)
            LOGGER.exception("JARVIS OS failed during startup or runtime.")
            print("JARVIS OS encountered a startup error. Check logs for details.")
            return 1
        finally:
            self.shutdown()

    def start(self) -> None:
        """Start core services and run health checks."""
        self.settings = load_settings()
        configure_logging(self.settings)
        LOGGER.info("startup_begin version=%s", APP_VERSION)

        required_directories = self.required_directories(self.settings)
        self.verify_required_directories(required_directories)
        self.status.mark_module_loaded("configuration")
        self.status.mark_module_loaded("logging")
        self.status.mark_module_loaded("directories")

        self.memory_manager = MemoryManager(self.settings.memory.storage_dir)
        self.memory_manager.initialize()
        self.memory_statistics = self.memory_manager.statistics()
        self.status.mark_module_loaded("memory")

        self.brain_manager = BrainManager(
            vault_path=self.settings.brain.vault_path,
            vault_name=self.settings.brain.vault_name,
            auto_create_vault=self.settings.brain.auto_create_vault,
            daily_note_format=self.settings.brain.daily_note_format,
        )
        self.brain_statistics = self.brain_manager.initialize()
        self.status.mark_module_loaded("brain")

        self.knowledge_manager = KnowledgeManager(
            self.settings.data_dir / "knowledge",
            memory_manager=self.memory_manager,
        )
        self.knowledge_manager.initialize()
        self.knowledge_statistics = self.knowledge_manager.statistics()
        self.status.mark_module_loaded("knowledge")

        self.task_manager = TaskManager()
        self.task_manager.initialize()
        self.task_statistics = self.task_manager.statistics()
        self.status.mark_module_loaded("tasks")

        self.provider_manager = ProviderManager(
            config=self.settings.providers,
            settings=self.settings,
        )
        self.provider_statistics = self.provider_manager.initialize()
        self.provider_router = self.provider_manager.router
        self.status.mark_module_loaded("providers")

        self.provider_execution_manager = ExecutionManager(
            context=ProviderExecutionContext(
                provider_router=self.provider_router,
                provider_manager=self.provider_manager,
                settings=self.settings,
                logger=logging.getLogger("provider_execution"),
            )
        )
        self.provider_execution_statistics = self.provider_execution_manager.initialize()
        self.status.mark_module_loaded("provider_execution")

        self.workflow_manager = WorkflowManager(logger=logging.getLogger("workflow"))
        self.workflow_statistics = self.workflow_manager.initialize()
        self.status.mark_module_loaded("workflow")

        self.retrieval_manager = RetrievalManager(logger=logging.getLogger("retrieval"))
        self.retrieval_statistics = self.retrieval_manager.initialize()
        self.status.mark_module_loaded("retrieval")

        self.task_intelligence_manager = TaskIntelligenceManager(logger=logging.getLogger("task_intelligence"))
        self.task_intelligence_statistics = self.task_intelligence_manager.initialize()
        self.status.mark_module_loaded("task_intelligence")

        self.research_manager = ResearchManager(logger=logging.getLogger("research"))
        self.research_statistics = self.research_manager.initialize()
        self.status.mark_module_loaded("research")

        self.reasoning_manager = ReasoningManager(logger=logging.getLogger("reasoning"))
        self.reasoning_statistics = self.reasoning_manager.initialize()
        self.status.mark_module_loaded("reasoning")

        self.reflection_manager = ReflectionManager(logger=logging.getLogger("reflection"))
        self.reflection_statistics = self.reflection_manager.initialize()
        self.status.mark_module_loaded("reflection")

        self.adaptive_manager = AdaptiveManager(logger=logging.getLogger("adaptive"))
        self.adaptive_statistics = self.adaptive_manager.initialize()
        self.status.mark_module_loaded("adaptive")

        self.plugin_manager = PluginManager(
            plugin_dir=self.settings.plugins.plugin_dir,
            settings=self.settings,
            auto_enable=self.settings.plugins.auto_enable,
        )
        if self.settings.plugins.enabled and self.settings.plugins.auto_discover:
            self.plugin_statistics = self.plugin_manager.initialize()
        else:
            self.plugin_statistics = self.plugin_manager.statistics()
            self.plugin_manager.initialized = True
        self.status.mark_module_loaded("plugins")

        agent_context = AgentContext(
            settings=self.settings,
            memory_manager=self.memory_manager,
            knowledge_manager=self.knowledge_manager,
            task_manager=self.task_manager,
            brain_manager=self.brain_manager,
            plugin_manager=self.plugin_manager,
            provider_router=self.provider_router,
            logger=logging.getLogger("agents"),
        )
        self.agent_manager = AgentManager(context=agent_context)
        self.agent_statistics = self.agent_manager.initialize()
        self.status.mark_module_loaded("agents")

        creator_context = AgentCreatorContext(
            project_root=self.settings.base_dir,
            settings=self.settings,
            agent_manager=self.agent_manager,
            plugin_manager=self.plugin_manager,
            provider_router=self.provider_router,
            logger=logging.getLogger("agent_creator"),
        )
        self.agent_creator = AgentCreator(context=creator_context)
        self.agent_creator_statistics = self.agent_creator.initialize()
        self.status.mark_module_loaded("agent_creator")

        jarvis_context = JarvisContext(
            request_id="startup",
            settings=self.settings,
            memory_manager=self.memory_manager,
            knowledge_manager=self.knowledge_manager,
            brain_manager=self.brain_manager,
            task_manager=self.task_manager,
            plugin_manager=self.plugin_manager,
            provider_router=self.provider_router,
            agent_manager=self.agent_manager,
            agent_creator=self.agent_creator,
            logger=logging.getLogger("jarvis"),
            metadata={
                "provider_manager": self.provider_manager,
                "provider_execution_manager": self.provider_execution_manager,
                "reasoning_manager": self.reasoning_manager,
                "reflection_manager": self.reflection_manager,
                "adaptive_manager": self.adaptive_manager,
            },
        )
        self.jarvis_core = JarvisCore(context=jarvis_context)
        self.jarvis_statistics = self.jarvis_core.initialize()
        self.status.mark_module_loaded("jarvis")

        self.conversation_manager = ConversationManager(
            jarvis_core=self.jarvis_core,
            memory_manager=self.memory_manager,
            knowledge_manager=self.knowledge_manager,
            task_manager=self.task_manager,
            plugin_manager=self.plugin_manager,
            provider_router=self.provider_router,
            agent_manager=self.agent_manager,
            agent_creator=self.agent_creator,
            logger=logging.getLogger("conversation"),
        )
        self.conversation_statistics = self.conversation_manager.initialize()
        self.status.mark_module_loaded("conversation")

        health_checker = HealthChecker(
            settings=self.settings,
            required_directories=required_directories,
            module_checks={
                "memory": lambda: (
                    self.memory_manager is not None
                    and self.memory_manager.initialized
                    and self.memory_manager.verify_schema()
                ),
                "brain": lambda: (
                    self.brain_manager is not None
                    and self.brain_manager.verify_connection()
                ),
                "knowledge": lambda: (
                    self.knowledge_manager is not None
                    and self.knowledge_manager.initialized
                    and self.knowledge_manager.verify_schema()
                ),
                "tasks": lambda: (
                    self.task_manager is not None
                    and self.task_manager.initialized
                ),
                "providers": lambda: (
                    self.provider_manager is not None
                    and self.provider_manager.initialized
                ),
                "provider_execution_manager": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.initialized
                ),
                "provider_execution_context": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.context is not None
                ),
                "provider_execution_request": lambda: (
                    self.provider_execution_manager is not None
                    and hasattr(self.provider_execution_manager, "build_execution_request")
                ),
                "provider_execution_response": lambda: (
                    self.provider_execution_manager is not None
                    and hasattr(self.provider_execution_manager, "execute")
                ),
                "execution_strategy": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.determine_strategy is not None
                ),
                "provider_execution": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.initialized
                ),
                "provider_selector": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.selector.initialized
                ),
                "model_selector": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.model_selector.initialized
                ),
                "provider_capabilities": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.registry is not None
                ),
                "provider_metrics": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.registry is not None
                ),
                "provider_benchmark": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.benchmark.initialized
                ),
                "provider_execution_registry": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.registry.initialized
                ),
                "provider_execution_history": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.history.initialized
                ),
                "provider_execution_cache": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.cache.initialized
                ),
                "provider_recovery": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.recovery.initialized
                ),
                "provider_diagnostics": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.diagnostics.initialized
                ),
                "provider_validator": lambda: (
                    self.provider_execution_manager is not None
                    and self.provider_execution_manager.validator.initialized
                ),
                "workflow_engine": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.engine.initialized
                ),
                "workflow_manager": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.initialized
                ),
                "workflow_registry": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.registry.initialized
                ),
                "workflow_builder": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.builder.initialized
                ),
                "workflow_executor": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.executor.initialized
                ),
                "workflow_dispatcher": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.dispatcher.initialized
                ),
                "workflow_scheduler": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.scheduler.initialized
                ),
                "workflow_checkpoint": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.checkpoint is not None
                ),
                "workflow_recovery": lambda: (
                    self.workflow_manager is not None and self.workflow_manager.recovery.initialized
                ),
                "workflow_metrics": lambda: (
                    self.workflow_manager is not None
                    and self.workflow_manager.metrics is not None
                ),
                "workflow_diagnostics": lambda: (
                    self.workflow_manager is not None
                    and self.workflow_manager.diagnostics.initialized
                ),
                "retrieval_manager": lambda: (
                    self.retrieval_manager is not None and self.retrieval_manager.initialized
                ),
                "retrieval_engine": lambda: (
                    self.retrieval_manager is not None and self.retrieval_manager.engine.initialized
                ),
                "retrieval_selector": lambda: (
                    self.retrieval_manager is not None and self.retrieval_manager.selector.initialized
                ),
                "retrieval_ranker": lambda: (
                    self.retrieval_manager is not None and self.retrieval_manager.ranker.initialized
                ),
                "retrieval_cache": lambda: (
                    self.retrieval_manager is not None and self.retrieval_manager.cache.initialized
                ),
                "retrieval_validator": lambda: (
                    self.retrieval_manager is not None and self.retrieval_manager.validator.initialized
                ),
                "retrieval_metrics": lambda: (
                    self.retrieval_manager is not None and self.retrieval_manager.metrics is not None
                ),
                "retrieval_diagnostics": lambda: (
                    self.retrieval_manager is not None
                    and self.retrieval_manager.diagnostics.initialized
                ),
                "task_intelligence": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.initialized
                ),
                "project_manager": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.project_manager.initialized
                ),
                "goal_manager": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.goal_manager.initialized
                ),
                "milestone_manager": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.milestone_manager.initialized
                ),
                "priority_engine": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.priority_engine.initialized
                ),
                "schedule_engine": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.schedule_engine.initialized
                ),
                "dependency_manager": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.dependency_manager.initialized
                ),
                "progress_tracker": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.progress_tracker.initialized
                ),
                "task_dashboard": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.dashboard.initialized
                ),
                "task_templates": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.templates.initialized
                ),
                "task_metrics": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.metrics.initialized
                ),
                "task_diagnostics": lambda: (
                    self.task_intelligence_manager is not None
                    and self.task_intelligence_manager.diagnostics.initialized
                ),
                "research": lambda: (
                    self.research_manager is not None
                    and self.research_manager.initialized
                ),
                "research_engine": lambda: (
                    self.research_manager is not None
                    and self.research_manager.engine.initialized
                ),
                "research_planner": lambda: (
                    self.research_manager is not None
                    and self.research_manager.engine.planner.initialized
                ),
                "research_summarizer": lambda: (
                    self.research_manager is not None
                    and self.research_manager.engine.summarizer.initialized
                ),
                "knowledge_builder": lambda: (
                    self.research_manager is not None
                    and self.research_manager.engine.knowledge_builder.initialized
                ),
                "learning_engine": lambda: (
                    self.research_manager is not None
                    and self.research_manager.engine.learning_engine.initialized
                ),
                "learning_planner": lambda: (
                    self.research_manager is not None
                    and self.research_manager.engine.learning_engine.planner.initialized
                ),
                "research_validator": lambda: (
                    self.research_manager is not None
                    and self.research_manager.engine.validator.initialized
                ),
                "research_metrics": lambda: (
                    self.research_manager is not None
                    and self.research_manager.metrics.initialized
                ),
                "research_diagnostics": lambda: (
                    self.research_manager is not None
                    and self.research_manager.diagnostics.initialized
                ),
                "reasoning": lambda: (
                    self.reasoning_manager is not None and self.reasoning_manager.initialized
                ),
                "reflection": lambda: (
                    self.reflection_manager is not None and self.reflection_manager.initialized
                ),
                "adaptive": lambda: (
                    self.adaptive_manager is not None and self.adaptive_manager.initialized
                ),
                "reasoning_engine": lambda: (
                    self.reasoning_manager is not None and self.reasoning_manager.engine.initialized
                ),
                "decision_engine": lambda: (
                    self.reasoning_manager is not None
                    and self.reasoning_manager.engine.decision_engine.initialized
                ),
                "planning_engine": lambda: (
                    self.reasoning_manager is not None
                    and self.reasoning_manager.engine.planning_engine.initialized
                ),
                "goal_decomposer": lambda: (
                    self.reasoning_manager is not None
                    and self.reasoning_manager.engine.goal_decomposer.initialized
                ),
                "option_generator": lambda: (
                    self.reasoning_manager is not None
                    and self.reasoning_manager.engine.option_generator.initialized
                ),
                "evaluation_engine": lambda: (
                    self.reasoning_manager is not None
                    and self.reasoning_manager.engine.evaluation_engine.initialized
                ),
                "confidence_engine": lambda: (
                    self.reasoning_manager is not None
                    and self.reasoning_manager.engine.confidence_engine.initialized
                ),
                "reflection": lambda: (
                    self.reflection_manager is not None and self.reflection_manager.initialized
                ),
                "reflection_engine": lambda: (
                    self.reflection_manager is not None and self.reflection_manager.engine.initialized
                ),
                "reflection_analyzer": lambda: (
                    self.reflection_manager is not None
                    and self.reflection_manager.engine.analyzer.initialized
                ),
                "reflection_learning": lambda: (
                    self.reflection_manager is not None
                    and self.reflection_manager.engine.learning.initialized
                ),
                "reflection_patterns": lambda: (
                    self.reflection_manager is not None
                    and self.reflection_manager.engine.patterns.initialized
                ),
                "reflection_confidence": lambda: (
                    self.reflection_manager is not None
                    and self.reflection_manager.engine.confidence.initialized
                ),
                "reflection_improvement": lambda: (
                    self.reflection_manager is not None
                    and self.reflection_manager.engine.improvement.initialized
                ),
                "reflection_registry": lambda: (
                    self.reflection_manager is not None
                    and self.reflection_manager.registry.initialized
                ),
                "reflection_metrics": lambda: (
                    self.reflection_manager is not None
                    and self.reflection_manager.metrics is not None
                ),
                "reflection_diagnostics": lambda: (
                    self.reflection_manager is not None
                    and self.reflection_manager.diagnostics is not None
                ),
                "adaptive_manager": lambda: (
                    self.adaptive_manager is not None and self.adaptive_manager.initialized
                ),
                "adaptive_engine": lambda: (
                    self.adaptive_manager is not None and self.adaptive_manager.engine.initialized
                ),
                "adaptive_experience": lambda: (
                    self.adaptive_manager is not None
                    and self.adaptive_manager.engine.experience.initialized
                ),
                "adaptive_policy": lambda: (
                    self.adaptive_manager is not None
                    and self.adaptive_manager.engine.policy is not None
                ),
                "adaptive_rules": lambda: (
                    self.adaptive_manager is not None
                    and self.adaptive_manager.engine.rules.initialized
                ),
                "adaptive_learning_queue": lambda: (
                    self.adaptive_manager is not None
                    and self.adaptive_manager.engine.queue.initialized
                ),
                "adaptive_registry": lambda: (
                    self.adaptive_manager is not None
                    and self.adaptive_manager.registry.initialized
                ),
                "adaptive_metrics": lambda: (
                    self.adaptive_manager is not None
                    and self.adaptive_manager.metrics is not None
                ),
                "adaptive_diagnostics": lambda: (
                    self.adaptive_manager is not None
                    and self.adaptive_manager.diagnostics is not None
                ),
                "plugins": lambda: (
                    self.plugin_manager is not None
                    and self.plugin_manager.initialized
                ),
                "agent_framework": lambda: (
                    self.agent_manager is not None and self.agent_manager.initialized
                ),
                "agent_registry": lambda: (
                    self.agent_manager is not None
                    and self.agent_manager.registry is not None
                ),
                "agent_manager": lambda: (
                    self.agent_manager is not None and self.agent_manager.initialized
                ),
                "agent_scheduler": lambda: (
                    self.agent_manager is not None
                    and self.agent_manager.scheduler.initialized
                ),
                "agent_router": lambda: (
                    self.agent_manager is not None
                    and self.agent_manager.router.initialized
                ),
                "agent_supervisor": lambda: (
                    self.agent_manager is not None
                    and self.agent_manager.supervisor.initialized
                ),
                "agent_orchestrator": lambda: (
                    self.agent_manager is not None
                    and self.agent_manager.orchestrator.initialized
                ),
                "agent_metrics": lambda: (
                    self.agent_manager is not None
                    and self.agent_manager.metrics is not None
                ),
                "agent_health": lambda: (
                    self.agent_manager is not None
                    and self.agent_manager.health is not None
                ),
                "agent_bus": lambda: (
                    self.agent_manager is not None
                    and self.agent_manager.bus.initialized
                ),
                "agent_creator": lambda: (
                    self.agent_creator is not None and self.agent_creator.initialized
                ),
                "blueprint_registry": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.blueprint_registry.initialized
                ),
                "template_registry": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.template_registry.initialized
                ),
                "template_loader": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.template_loader.initialized
                ),
                "agent_generator": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.generator.initialized
                ),
                "agent_installer": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.installer.initialized
                ),
                "agent_validator": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.validator.initialized
                ),
                "agent_wizard": lambda: (
                    self.agent_creator is not None and self.agent_creator.wizard.initialized
                ),
                "rollback_manager": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.rollback_manager.initialized
                ),
                "catalog": lambda: (
                    self.agent_creator is not None and self.agent_creator.catalog.initialized
                ),
                "department_manager": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.department_manager.initialized
                ),
                "department_registry": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.department_manager.registry.initialized
                ),
                "policy_engine": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.policy_engine.initialized
                ),
                "audit_manager": lambda: (
                    self.agent_creator is not None
                    and self.agent_creator.audit_manager.initialized
                ),
                "jarvis_runtime": lambda: (
                    self.jarvis_core is not None
                    and self.jarvis_core.manager.runtime.state.value in {"idle", "ready"}
                ),
                "jarvis_manager": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.initialized
                ),
                "jarvis_controller": lambda: (
                    self.jarvis_core is not None
                    and self.jarvis_core.manager.controller.initialized
                ),
                "jarvis_decision_engine": lambda: (
                    self.jarvis_core is not None
                    and self.jarvis_core.manager.controller.decision_engine.initialized
                ),
                "jarvis_intent_engine": lambda: (
                    self.jarvis_core is not None
                    and self.jarvis_core.manager.controller.intent_engine.initialized
                ),
                "jarvis_dispatcher": lambda: (
                    self.jarvis_core is not None
                    and self.jarvis_core.manager.controller.dispatcher.initialized
                ),
                "jarvis_planning": lambda: (
                    self.jarvis_core is not None
                    and self.jarvis_core.manager.controller.planning.initialized
                ),
                "jarvis_reasoning": lambda: self.jarvis_core is not None,
                "jarvis_providers": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.providers.initialized
                ),
                "jarvis_memory": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.memory.initialized
                ),
                "jarvis_knowledge": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.knowledge.initialized
                ),
                "jarvis_tasks": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.tasks.initialized
                ),
                "jarvis_plugins": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.plugins.initialized
                ),
                "jarvis_tools": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.tools.initialized
                ),
                "jarvis_skills": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.skills.initialized
                ),
                "jarvis_departments": lambda: (
                    self.jarvis_core is not None
                    and self.jarvis_core.manager.department_registry.initialized
                ),
                "jarvis_validator": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.validator.initialized
                ),
                "jarvis_metrics": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.metrics is not None
                ),
                "jarvis_diagnostics": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.diagnostics.initialized
                ),
                "jarvis_recovery": lambda: (
                    self.jarvis_core is not None and self.jarvis_core.manager.recovery.initialized
                ),
                "jarvis_health": lambda: (
                    self.jarvis_core is not None
                    and self.jarvis_core.manager.health.status.value == "healthy"
                ),
                "conversation_engine": lambda: (
                    self.conversation_manager is not None
                    and self.conversation_manager.engine.initialized
                ),
                "command_engine": lambda: (
                    self.conversation_manager is not None
                    and self.conversation_manager.command_manager.initialized
                ),
                "cli": lambda: self.conversation_manager is not None,
                "request_builder": lambda: self.conversation_manager is not None,
                "execution_planner": lambda: self.conversation_manager is not None,
                "response_pipeline": lambda: self.conversation_manager is not None,
                "conversation_sessions": lambda: (
                    self.conversation_manager is not None
                    and self.conversation_manager.active_session is not None
                ),
                "command_registry": lambda: (
                    self.conversation_manager is not None
                    and self.conversation_manager.command_manager.registry.initialized
                ),
                "executive_conversation_health": lambda: (
                    self.conversation_manager is not None
                    and self.conversation_manager.statistics().health_status == "healthy"
                ),
            },
        )
        self.health_results = health_checker.run_all()
        self.status.set_state(self._state_from_health(self.health_results))
        self.display_startup_summary()
        LOGGER.info("startup_complete status=%s", self.status.state.value)

    def shutdown(self) -> None:
        """Gracefully stop the application skeleton."""
        if self.status.state is SystemState.STOPPED:
            return

        if self.status.state is not SystemState.FAILED:
            self.status.set_state(SystemState.STOPPING)
        LOGGER.info("shutdown_begin state=%s", self.status.state.value)
        if self.jarvis_core is not None and self.jarvis_core.initialized:
            self.jarvis_core.shutdown()
        if self.agent_manager is not None and self.agent_manager.initialized:
            self.agent_manager.shutdown()
        if self.plugin_manager is not None and self.plugin_manager.initialized:
            self.plugin_manager.shutdown()
        if self.provider_manager is not None and self.provider_manager.initialized:
            self.provider_manager.shutdown()
        self.status.set_state(SystemState.STOPPED)
        LOGGER.info("shutdown_complete")

    def command_loop(self) -> None:
        """Run the interactive command loop until the user exits."""
        print("Type 'help' for available commands.")
        while True:
            command = input("Jarvis > ").strip().lower()
            if not command:
                continue

            if self.conversation_manager is None:
                print("Conversation Engine is not available.")
                continue
            response = self.conversation_manager.handle_input(command)
            if response.should_clear:
                self._handle_clear()
                continue
            if command == "status":
                self._handle_status()
                continue
            if command == "help":
                print(response.response)
                continue
            if response.response:
                print(response.response)
            if response.should_exit:
                break

    def display_startup_summary(self) -> None:
        """Display a concise startup summary."""
        summary = self.status.summary()
        print("Startup Summary")
        print(f"  Version: {summary['application_version']}")
        print(f"  State: {summary['system_state']}")
        print(f"  Loaded modules: {', '.join(self.status.loaded_modules)}")
        if self.memory_statistics is not None:
            print("  Memory Database Ready")
            print(f"    Total Memories: {self.memory_statistics.total_memories}")
            print(f"    Total Sessions: {self.memory_statistics.total_sessions}")
            print(
                "    Database Size: "
                f"{self.memory_statistics.database_size_bytes} bytes"
            )
        if self.brain_statistics is not None:
            status_label = (
                "Connected" if self.brain_statistics.connected else "Not Connected"
            )
            print("  [OK] Obsidian Brain Connected")
            print(f"    Vault Name: {self.brain_statistics.vault_name}")
            print(f"    Vault Path: {self.brain_statistics.vault_path}")
            print(f"    Total Notes: {self.brain_statistics.total_notes}")
            print(f"    Connection Status: {status_label}")
        if self.knowledge_statistics is not None:
            print("  Knowledge Engine Ready")
            print(f"    Total Documents: {self.knowledge_statistics.total_documents}")
            print(f"    Total Chunks: {self.knowledge_statistics.total_chunks}")
            print(
                "    Database Size: "
                f"{self.knowledge_statistics.database_size_bytes} bytes"
            )
        if self.provider_statistics is not None:
            print("  Provider Router Initialized")
            print(f"    Registered Providers: {self.provider_statistics.registered_providers}")
            print(f"    Enabled Providers: {self.provider_statistics.enabled_providers}")
            print(f"    Healthy Providers: {self.provider_statistics.healthy_providers}")
        if self.provider_execution_statistics is not None:
            print("  Provider Execution Framework Initialized")
            print(f"    Registered Providers: {self.provider_execution_statistics.registered_providers}")
            print(f"    Enabled Providers: {self.provider_execution_statistics.enabled_providers}")
            print(f"    Healthy Providers: {self.provider_execution_statistics.healthy_providers}")
            print(f"    Registered Models: {self.provider_execution_statistics.registered_models}")
            print(f"    Executions: {self.provider_execution_statistics.executions}")
            print(f"    Status: {self.provider_execution_statistics.status}")
            print("    Execution Components: provider_execution_manager, provider_execution_context, provider_execution_request, provider_execution_response, execution_strategy, provider_selector, model_selector, provider_capabilities, provider_metrics, provider_benchmark, provider_execution_registry, provider_execution_history, provider_execution_cache, provider_recovery, provider_diagnostics, provider_validator")
        if self.workflow_manager is not None:
            workflow_stats = self.workflow_manager.statistics()
            print("  Workflow Engine Initialized")
            print(f"    Workflow Engine Status: {workflow_stats.workflow_engine_status}")
            print(f"    Workflow Registry Status: {workflow_stats.workflow_registry_status}")
            print(f"    Workflow Scheduler Status: {workflow_stats.workflow_scheduler_status}")
            print(f"    Workflow Recovery Status: {workflow_stats.workflow_recovery_status}")
            print(f"    Registered Workflow Templates: {workflow_stats.registered_workflow_templates}")
            print(f"    Active Workflows: {workflow_stats.active_workflows}")
            print(f"    Overall Workflow Health: {workflow_stats.overall_workflow_health}")
        if self.retrieval_manager is not None:
            retrieval_stats = self.retrieval_manager.statistics()
            print("  Retrieval Engine Initialized")
            print(f"    Retrieval Engine Status: {retrieval_stats.retrieval_engine_status}")
            print(f"    Available Retrieval Sources: {retrieval_stats.available_retrieval_sources}")
            print(f"    Cache Status: {retrieval_stats.cache_status}")
            print(f"    Ranking Status: {retrieval_stats.ranking_status}")
            print(f"    Overall Retrieval Health: {retrieval_stats.overall_retrieval_health}")
        if self.task_intelligence_manager is not None:
            task_intel_stats = self.task_intelligence_manager.statistics()
            print("  Task Intelligence Initialized")
            print(f"    Task Intelligence Status: {task_intel_stats.status}")
            print(f"    Project Status: {self.task_intelligence_manager.project_manager.statistics()['status']}")
            print(f"    Goal Status: {self.task_intelligence_manager.goal_manager.statistics()['status']}")
            print(f"    Milestone Status: {self.task_intelligence_manager.milestone_manager.statistics()['status']}")
            print(f"    Dashboard Status: {self.task_intelligence_manager.dashboard.summary()['status']}")
            print("    Overall Task Health: healthy")
        if self.research_manager is not None:
            research_stats = self.research_manager.statistics()
            print("  Research Engine Initialized")
            print(f"    Research Engine Status: {research_stats.research_engine_status}")
            print(f"    Learning Engine Status: {research_stats.learning_engine_status}")
            print(f"    Knowledge Builder Status: {research_stats.knowledge_builder_status}")
            print(f"    Research Sources: {research_stats.research_sources}")
            print(f"    Overall Research Health: {research_stats.overall_research_health}")
        if self.reasoning_manager is not None:
            reasoning_stats = self.reasoning_manager.statistics()
            print("  Reasoning Engine Initialized")
            print(f"    Reasoning Status: {reasoning_stats.reasoning_status}")
            print(f"    Decision Status: {reasoning_stats.decision_status}")
            print(f"    Planning Status: {reasoning_stats.planning_status}")
            print(f"    Confidence Status: {reasoning_stats.confidence_status}")
            print(f"    Overall Intelligence Status: {reasoning_stats.overall_intelligence_status}")
        if self.reflection_manager is not None:
            reflection_stats = self.reflection_manager.statistics()
            print("  Reflection Engine Initialized")
            print(f"    Reflection Status: {reflection_stats.reflection_status}")
            print(f"    Learning Status: {reflection_stats.learning_status}")
            print(f"    Pattern Status: {reflection_stats.pattern_status}")
            print(f"    Confidence Status: {reflection_stats.confidence_status}")
            print(f"    Improvement Status: {reflection_stats.improvement_status}")
            print(f"    Overall Reflection Health: {reflection_stats.overall_reflection_health}")
        if self.adaptive_manager is not None:
            adaptive_stats = self.adaptive_manager.statistics()
            print("  Adaptive Intelligence Initialized")
            print(f"    Adaptive Intelligence Status: {adaptive_stats.adaptive_status}")
            print(f"    Experience Status: {adaptive_stats.experience_status}")
            print(f"    Learning Queue Status: {adaptive_stats.learning_queue_status}")
            print(f"    Policy Status: {adaptive_stats.policy_status}")
            print(f"    Rules Status: {adaptive_stats.rules_status}")
            print(f"    Overall Adaptive Intelligence Health: {adaptive_stats.overall_adaptive_health}")
        if self.plugin_statistics is not None:
            print("  Plugin Framework Initialized")
            print(f"    Loaded Plugins: {self.plugin_statistics.loaded_plugins}")
            print(f"    Enabled Plugins: {self.plugin_statistics.enabled_plugins}")
            print(f"    Invalid Plugins: {self.plugin_statistics.invalid_plugins}")
        if self.task_statistics is not None:
            print("  Task Engine Ready")
            print(f"    Active Tasks: {self.task_statistics.total_tasks}")
            print(f"    Queued Tasks: {self.task_statistics.queued_tasks}")
            print(f"    History Records: {self.task_statistics.history_count}")
        if self.agent_statistics is not None:
            print("  Agent Framework Initialized")
            print(f"    Registered Agents: {self.agent_statistics.registered_agents}")
            print(f"    Loaded Agents: {self.agent_statistics.loaded_agents}")
            print(f"    Enabled Agents: {self.agent_statistics.enabled_agents}")
            print(f"    Running Agents: {self.agent_statistics.running_agents}")
            print(f"    Healthy Agents: {self.agent_statistics.healthy_agents}")
            print(f"    Disabled Agents: {self.agent_statistics.disabled_agents}")
            print(f"    Failed Agents: {self.agent_statistics.failed_agents}")
            print(f"    Scheduler Status: {self.agent_statistics.scheduler_status}")
            print(f"    Supervisor Status: {self.agent_statistics.supervisor_status}")
            print(f"    Orchestrator Status: {self.agent_statistics.orchestrator_status}")
            print(f"    Agent Bus Status: {self.agent_statistics.bus_status}")
            print(f"    Health Status: {self.agent_statistics.health_status}")
        if self.agent_creator_statistics is not None:
            print("  Agent Creator Initialized")
            print(f"    Registered Blueprints: {self.agent_creator_statistics.registered_blueprints}")
            print(f"    Registered Templates: {self.agent_creator_statistics.registered_templates}")
            print(f"    Generated Agents: {self.agent_creator_statistics.generated_agents}")
            print(f"    Installed Agents: {self.agent_creator_statistics.installed_agents}")
            print(f"    Core Agents: {self.agent_creator_statistics.core_agents}")
            print(f"    Dynamic Agents: {self.agent_creator_statistics.dynamic_agents}")
            print(f"    Departments: {self.agent_creator_statistics.departments}")
            print(f"    Wizard Status: {self.agent_creator_statistics.wizard_status}")
            print(f"    Installer Status: {self.agent_creator_statistics.installer_status}")
            print(f"    Catalog Status: {self.agent_creator_statistics.catalog_status}")
            print(f"    Validation Status: {self.agent_creator_statistics.validation_status}")
            print(f"    Health Status: {self.agent_creator_statistics.health_status}")
        if self.jarvis_statistics is not None:
            print("  Executive JARVIS Initialized")
            print(f"    Runtime Status: {self.jarvis_statistics.runtime_status}")
            print(f"    Manager Status: {self.jarvis_statistics.manager_status}")
            print(f"    Controller Status: {self.jarvis_statistics.controller_status}")
            print(f"    Intent Engine: {self.jarvis_statistics.intent_engine_status}")
            print(f"    Decision Engine: {self.jarvis_statistics.decision_engine_status}")
            print(f"    Dispatcher: {self.jarvis_statistics.dispatcher_status}")
            print(f"    Planning: {self.jarvis_statistics.planning_status}")
            print(f"    Providers: {self.jarvis_statistics.providers_status}")
            print(f"    Departments: {self.jarvis_statistics.departments}")
            print(f"    Requests: {self.jarvis_statistics.requests}")
            print(f"    Health Status: {self.jarvis_statistics.health_status}")
        if self.conversation_statistics is not None:
            print("  Conversation Engine Initialized")
            print(f"    Conversation Status: {self.conversation_statistics.conversation_status}")
            print(f"    Command Engine Status: {self.conversation_statistics.command_engine_status}")
            print(f"    CLI Status: {self.conversation_statistics.cli_status}")
            print(f"    Request Pipeline Status: {self.conversation_statistics.request_pipeline_status}")
            print(f"    Response Pipeline Status: {self.conversation_statistics.response_pipeline_status}")
            print(f"    Active Conversations: {self.conversation_statistics.active_conversations}")
            print(f"    Registered Commands: {self.conversation_statistics.registered_commands}")
            print(f"    Session Status: {self.conversation_statistics.session_status}")
        print("  Health:")
        for result in self.health_results:
            print(f"    - {result.name}: {result.status.value} ({result.message})")
        print()

    def verify_required_directories(self, directories: tuple[Path, ...]) -> None:
        """Create required runtime directories if they do not already exist."""
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            LOGGER.debug("directory_verified path=%s", directory)

    def required_directories(self, settings: AppSettings) -> tuple[Path, ...]:
        """Return directories required for the runnable skeleton."""
        return (
            settings.data_dir,
            settings.data_dir / "knowledge",
            settings.logs_dir,
            settings.memory.storage_dir,
            settings.brain.vault_path,
            settings.memory.task_store_dir,
            settings.memory.vector_index_dir,
            settings.agents.workspace_dir,
            settings.plugins.plugin_dir,
            settings.downloads.download_dir,
            settings.automation.queue_dir,
            settings.security.secrets_dir,
        )

    def _handle_help(self) -> None:
        print("Available commands:")
        print("  help    Show this command list")
        print("  status  Show current system status")
        print("  version Show application version")
        print("  clear   Clear the console")
        print("  exit    Shut down JARVIS OS")

    def _handle_status(self) -> None:
        summary = self.status.summary()
        if self.memory_manager is not None and self.memory_manager.initialized:
            self.memory_statistics = self.memory_manager.statistics()
        if self.brain_manager is not None and self.brain_manager.initialized:
            self.brain_statistics = self.brain_manager.statistics()
        if self.knowledge_manager is not None and self.knowledge_manager.initialized:
            self.knowledge_statistics = self.knowledge_manager.statistics()
        if self.provider_manager is not None and self.provider_manager.initialized:
            self.provider_statistics = self.provider_manager.statistics()
        if self.provider_execution_manager is not None and self.provider_execution_manager.initialized:
            self.provider_execution_statistics = self.provider_execution_manager.statistics()
        if self.workflow_manager is not None and self.workflow_manager.initialized:
            self.workflow_statistics = self.workflow_manager.statistics()
        if self.retrieval_manager is not None and self.retrieval_manager.initialized:
            self.retrieval_statistics = self.retrieval_manager.statistics()
        if self.plugin_manager is not None and self.plugin_manager.initialized:
            self.plugin_statistics = self.plugin_manager.statistics()
        if self.task_manager is not None and self.task_manager.initialized:
            self.task_statistics = self.task_manager.statistics()
        if self.agent_manager is not None and self.agent_manager.initialized:
            self.agent_statistics = self.agent_manager.statistics()
        if self.agent_creator is not None and self.agent_creator.initialized:
            self.agent_creator_statistics = self.agent_creator.statistics()
        if self.jarvis_core is not None and self.jarvis_core.initialized:
            self.jarvis_statistics = self.jarvis_core.statistics()
        if self.conversation_manager is not None and self.conversation_manager.initialized:
            self.conversation_statistics = self.conversation_manager.statistics()
        print("System Status")
        print(f"  Version: {summary['application_version']}")
        print(f"  State: {summary['system_state']}")
        print(f"  Startup time: {summary['startup_time']}")
        print(f"  Running time: {summary['running_time_seconds']} seconds")
        print(f"  Loaded modules: {', '.join(self.status.loaded_modules)}")
        if self.memory_statistics is not None:
            print(f"  Total memories: {self.memory_statistics.total_memories}")
            print(f"  Total sessions: {self.memory_statistics.total_sessions}")
            print(
                "  Memory database size: "
                f"{self.memory_statistics.database_size_bytes} bytes"
            )
        if self.brain_statistics is not None:
            print(f"  Brain vault: {self.brain_statistics.vault_name}")
            print(f"  Brain vault path: {self.brain_statistics.vault_path}")
            print(f"  Brain notes: {self.brain_statistics.total_notes}")
            print(f"  Brain connected: {self.brain_statistics.connected}")
        if self.knowledge_statistics is not None:
            print(f"  Total documents: {self.knowledge_statistics.total_documents}")
            print(f"  Total knowledge chunks: {self.knowledge_statistics.total_chunks}")
            print(
                "  Knowledge database size: "
                f"{self.knowledge_statistics.database_size_bytes} bytes"
            )
        if self.provider_statistics is not None:
            print(f"  Registered providers: {self.provider_statistics.registered_providers}")
            print(f"  Enabled providers: {self.provider_statistics.enabled_providers}")
            print(f"  Healthy providers: {self.provider_statistics.healthy_providers}")
        if self.provider_execution_statistics is not None:
            print(f"  Provider execution status: {self.provider_execution_statistics.status}")
            print(f"  Provider execution records: {self.provider_execution_statistics.registered_providers}")
        if self.workflow_manager is not None:
            wf = self.workflow_manager.statistics()
            print(f"  Workflow engine status: {wf.workflow_engine_status}")
            print(f"  Workflow registry status: {wf.workflow_registry_status}")
            print(f"  Workflow scheduler status: {wf.workflow_scheduler_status}")
            print(f"  Workflow recovery status: {wf.workflow_recovery_status}")
            print(f"  Registered workflow templates: {wf.registered_workflow_templates}")
            print(f"  Active workflows: {wf.active_workflows}")
            print(f"  Overall workflow health: {wf.overall_workflow_health}")
        if self.retrieval_manager is not None:
            rs = self.retrieval_manager.statistics()
            print(f"  Retrieval engine status: {rs.retrieval_engine_status}")
            print(f"  Available retrieval sources: {rs.available_retrieval_sources}")
            print(f"  Retrieval cache status: {rs.cache_status}")
            print(f"  Retrieval ranking status: {rs.ranking_status}")
            print(f"  Overall retrieval health: {rs.overall_retrieval_health}")
        if self.task_intelligence_manager is not None:
            ti = self.task_intelligence_manager.statistics()
            print(f"  Task intelligence status: {ti.status}")
            print(f"  Task projects: {ti.projects}")
            print(f"  Task goals: {ti.goals}")
            print(f"  Task milestones: {ti.milestones}")
            print("  Task dashboard: ready")
        if self.research_manager is not None:
            rsr = self.research_manager.statistics()
            print(f"  Research engine status: {rsr.research_engine_status}")
            print(f"  Learning engine status: {rsr.learning_engine_status}")
            print(f"  Knowledge builder status: {rsr.knowledge_builder_status}")
            print(f"  Research sources: {rsr.research_sources}")
        if self.reasoning_manager is not None:
            rz = self.reasoning_manager.statistics()
            print(f"  Reasoning status: {rz.reasoning_status}")
            print(f"  Decision status: {rz.decision_status}")
            print(f"  Planning status: {rz.planning_status}")
            print(f"  Confidence status: {rz.confidence_status}")
        if self.reflection_manager is not None:
            rf = self.reflection_manager.statistics()
            print(f"  Reflection status: {rf.reflection_status}")
            print(f"  Learning status: {rf.learning_status}")
            print(f"  Pattern status: {rf.pattern_status}")
            print(f"  Improvement status: {rf.improvement_status}")
        if self.adaptive_manager is not None:
            ad = self.adaptive_manager.statistics()
            print(f"  Adaptive status: {ad.adaptive_status}")
            print(f"  Experience status: {ad.experience_status}")
            print(f"  Learning queue status: {ad.learning_queue_status}")
            print(f"  Rules status: {ad.rules_status}")
        if self.plugin_statistics is not None:
            print(f"  Loaded plugins: {self.plugin_statistics.loaded_plugins}")
            print(f"  Enabled plugins: {self.plugin_statistics.enabled_plugins}")
            print(f"  Invalid plugins: {self.plugin_statistics.invalid_plugins}")
        if self.task_statistics is not None:
            print(f"  Active tasks: {self.task_statistics.total_tasks}")
            print(f"  Queued tasks: {self.task_statistics.queued_tasks}")
            print(f"  Task history records: {self.task_statistics.history_count}")
        if self.agent_statistics is not None:
            print(f"  Registered agents: {self.agent_statistics.registered_agents}")
            print(f"  Loaded agents: {self.agent_statistics.loaded_agents}")
            print(f"  Enabled agents: {self.agent_statistics.enabled_agents}")
            print(f"  Running agents: {self.agent_statistics.running_agents}")
            print(f"  Healthy agents: {self.agent_statistics.healthy_agents}")
            print(f"  Agent scheduler: {self.agent_statistics.scheduler_status}")
            print(f"  Agent supervisor: {self.agent_statistics.supervisor_status}")
            print(f"  Agent orchestrator: {self.agent_statistics.orchestrator_status}")
            print(f"  Agent bus: {self.agent_statistics.bus_status}")
        if self.agent_creator_statistics is not None:
            print(f"  Registered blueprints: {self.agent_creator_statistics.registered_blueprints}")
            print(f"  Registered templates: {self.agent_creator_statistics.registered_templates}")
            print(f"  Generated agents: {self.agent_creator_statistics.generated_agents}")
            print(f"  Installed agents: {self.agent_creator_statistics.installed_agents}")
            print(f"  Departments: {self.agent_creator_statistics.departments}")
            print(f"  Agent creator health: {self.agent_creator_statistics.health_status}")
        if self.jarvis_statistics is not None:
            print(f"  Executive runtime: {self.jarvis_statistics.runtime_status}")
            print(f"  Executive requests: {self.jarvis_statistics.requests}")
            print(f"  Executive departments: {self.jarvis_statistics.departments}")
            print(f"  Executive health: {self.jarvis_statistics.health_status}")
        if self.conversation_statistics is not None:
            print(f"  Conversation status: {self.conversation_statistics.conversation_status}")
            print(f"  Registered commands: {self.conversation_statistics.registered_commands}")
            print(f"  Active conversations: {self.conversation_statistics.active_conversations}")

    def _handle_clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def _state_from_health(self, results: tuple[HealthResult, ...]) -> SystemState:
        if any(result.status is HealthStatus.FAILING for result in results):
            return SystemState.DEGRADED
        if any(result.status is HealthStatus.WARNING for result in results):
            return SystemState.DEGRADED
        return SystemState.RUNNING
