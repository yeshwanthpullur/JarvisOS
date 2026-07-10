"""High-level Agent Creator orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from agent_creator.blueprint import (
    BaseBlueprint,
    BrowserBlueprint,
    CodingBlueprint,
    ConversationBlueprint,
    CustomBlueprint,
    DepartmentBlueprint,
    EngineeringBlueprint,
    HealthBlueprint,
    KnowledgeBlueprint,
    LearningBlueprint,
    ManagerBlueprint,
    MemoryBlueprint,
    PhoneBlueprint,
    PlanningBlueprint,
    ResearchBlueprint,
    SupervisorBlueprint,
    SystemBlueprint,
    TaskBlueprint,
    UtilityBlueprint,
    VisionBlueprint,
)
from agent_creator.blueprint_registry import BlueprintRegistry
from agent_creator.catalog import AgentCatalog
from agent_creator.context import AgentCreatorContext
from agent_creator.audit import AuditManager
from agent_creator.department import DepartmentManager
from agent_creator.generator import AgentGenerator
from agent_creator.health import AgentCreatorHealth
from agent_creator.installer import AgentInstaller, InstallationReport
from agent_creator.manifest import AgentManifest
from agent_creator.metrics import AgentCreatorMetrics
from agent_creator.registry import DynamicAgentRegistry
from agent_creator.rollback import RollbackManager
from agent_creator.runtime import AgentCreatorRuntime
from agent_creator.policy import PolicyEngine
from agent_creator.security import SecurityManager
from agent_creator.template_loader import TemplateLoader
from agent_creator.template_registry import TemplateRegistry
from agent_creator.validator import AgentValidator
from agent_creator.wizard import AgentWizard


@dataclass(frozen=True, slots=True)
class AgentCreatorStatistics:
    """Startup and runtime statistics for Agent Creator."""

    registered_blueprints: int
    registered_templates: int
    generated_agents: int
    installed_agents: int
    core_agents: int
    dynamic_agents: int
    departments: int
    wizard_status: str
    installer_status: str
    catalog_status: str
    validation_status: str
    health_status: str


class AgentCreator:
    """Official manufacturing system for future JARVIS OS agents."""

    def __init__(self, context: AgentCreatorContext, logger: logging.Logger | None = None) -> None:
        self.context = context
        self.logger = logger or logging.getLogger(__name__)
        self.blueprint_registry = BlueprintRegistry(self.logger)
        self.template_registry = TemplateRegistry()
        self.template_loader = TemplateLoader()
        self.validator = AgentValidator()
        self.generator = AgentGenerator(validator=self.validator)
        self.dynamic_registry = DynamicAgentRegistry()
        self.catalog = AgentCatalog()
        self.rollback_manager = RollbackManager()
        self.installer = AgentInstaller(self.dynamic_registry, self.catalog, self.rollback_manager)
        self.wizard = AgentWizard()
        self.department_manager = DepartmentManager()
        self.security_manager = SecurityManager()
        self.policy_engine = PolicyEngine()
        self.audit_manager = AuditManager()
        self.metrics = AgentCreatorMetrics()
        self.health = AgentCreatorHealth()
        self.runtime = AgentCreatorRuntime()
        self.initialized = False
        self.wizard_initialized = False

    def initialize(self) -> AgentCreatorStatistics:
        """Initialize creator registries and built-in templates."""
        defaults = (
            SystemBlueprint(),
            ConversationBlueprint(),
            PlanningBlueprint(),
            ResearchBlueprint(),
            MemoryBlueprint(),
            KnowledgeBlueprint(),
            TaskBlueprint(),
            UtilityBlueprint(),
            ManagerBlueprint(),
            SupervisorBlueprint(),
            DepartmentBlueprint(),
            BrowserBlueprint(),
            VisionBlueprint(),
            PhoneBlueprint(),
            CodingBlueprint(),
            EngineeringBlueprint(),
            HealthBlueprint(),
            LearningBlueprint(),
            CustomBlueprint(),
        )
        self.blueprint_registry.load_defaults(defaults)
        for template in self.template_loader.discover():
            if self.template_registry.get(template.template_id) is None:
                self.template_registry.register(template)
        self.metrics.blueprints_registered = len(self.blueprint_registry.list_blueprints())
        self.metrics.templates_registered = len(self.template_registry.list_templates())
        self.department_manager.initialize_defaults()
        self.initialized = True
        self.wizard_initialized = True
        self.health.mark_ready()
        self.logger.info("agent_creator_initialized blueprints=%s templates=%s", self.metrics.blueprints_registered, self.metrics.templates_registered)
        return self.statistics()

    def create_preview(self, blueprint_id: str, template_id: str, manifest: AgentManifest):
        """Create a generation preview without installing files."""
        blueprint = self.blueprint_registry.require(blueprint_id)
        template = self.template_registry.require(template_id)
        return self.generator.generate(blueprint, template, manifest)

    def install_generated(self, blueprint_id: str, template_id: str, manifest: AgentManifest, destination_root: Path, write_files: bool = False) -> InstallationReport:
        """Generate and install an agent package."""
        plan = self.create_preview(blueprint_id, template_id, manifest)
        report = self.installer.install(plan, destination_root, write_files=write_files)
        self.metrics.generated_agents += 1
        self.metrics.installed_agents += 1
        return report

    def statistics(self) -> AgentCreatorStatistics:
        """Return creator statistics."""
        installed = sum(1 for item in self.dynamic_registry.list_agents() if item.installed)
        return AgentCreatorStatistics(
            registered_blueprints=len(self.blueprint_registry.list_blueprints()),
            registered_templates=len(self.template_registry.list_templates()),
            generated_agents=self.metrics.generated_agents,
            installed_agents=installed,
            core_agents=0,
            dynamic_agents=len(self.dynamic_registry.list_agents()),
            departments=len(self.department_manager.registry.list_departments()),
            wizard_status="ready" if self.wizard.initialized and self.wizard_initialized else "unavailable",
            installer_status="ready" if self.installer.initialized else "unavailable",
            catalog_status="ready" if self.catalog.initialized else "unavailable",
            validation_status="ready" if self.validator.initialized else "unavailable",
            health_status=self.health.status.value,
        )
