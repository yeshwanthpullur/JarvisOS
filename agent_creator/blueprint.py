"""Blueprint contracts for generated JARVIS agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from agents import AgentType
from agent_creator.capabilities import CreatorCapability
from agent_creator.constants import COMPATIBILITY_VERSION
from agent_creator.permissions import CreatorPermission
from agent_creator.state import BlueprintState, validate_blueprint_transition


@dataclass(slots=True)
class BaseBlueprint:
    """Metadata-only architectural contract for a generated agent."""

    blueprint_id: str
    name: str
    description: str
    category: str
    agent_type: AgentType = AgentType.CUSTOM
    version: str = "0.1.0"
    capabilities: tuple[CreatorCapability, ...] = ()
    permissions: tuple[CreatorPermission, ...] = ()
    dependencies: tuple[str, ...] = ()
    required_files: tuple[str, ...] = ("__init__.py", "agent.py", "manifest.json")
    optional_files: tuple[str, ...] = ("README.md", "tests.py")
    startup_hooks: tuple[str, ...] = ()
    health_hooks: tuple[str, ...] = ()
    metrics_hooks: tuple[str, ...] = ()
    documentation_template: str = "agent_readme"
    test_template: str = "agent_test"
    configuration_template: str = "agent_config"
    manifest_template: str = "agent_manifest"
    compatibility_version: str = COMPATIBILITY_VERSION
    author: str = "JARVIS OS"
    tags: tuple[str, ...] = ()
    state: BlueprintState = BlueprintState.CREATED

    def transition_to(self, state: BlueprintState) -> None:
        """Validate and apply a blueprint lifecycle transition."""
        validate_blueprint_transition(self.state, state)
        self.state = state

    def to_dict(self) -> dict[str, object]:
        """Return a serializable blueprint representation."""
        return {
            "blueprint_id": self.blueprint_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "agent_type": self.agent_type.value,
            "version": self.version,
            "capabilities": [item.value for item in self.capabilities],
            "permissions": [item.value for item in self.permissions],
            "dependencies": list(self.dependencies),
            "required_files": list(self.required_files),
            "optional_files": list(self.optional_files),
            "compatibility_version": self.compatibility_version,
            "author": self.author,
            "tags": list(self.tags),
            "state": self.state.value,
        }


def make_blueprint(blueprint_id: str, name: str, category: str, agent_type: AgentType) -> BaseBlueprint:
    """Create a standard metadata-only blueprint."""
    return BaseBlueprint(
        blueprint_id=blueprint_id,
        name=name,
        description=f"{name} blueprint for generated JARVIS OS agents.",
        category=category,
        agent_type=agent_type,
        tags=(category, agent_type.value),
    )


SystemBlueprint = lambda: make_blueprint("system", "System Blueprint", "core", AgentType.SYSTEM)
ConversationBlueprint = lambda: make_blueprint("conversation", "Conversation Blueprint", "core", AgentType.CONVERSATION)
PlanningBlueprint = lambda: make_blueprint("planning", "Planning Blueprint", "core", AgentType.PLANNER)
ResearchBlueprint = lambda: make_blueprint("research", "Research Blueprint", "core", AgentType.RESEARCH)
MemoryBlueprint = lambda: make_blueprint("memory", "Memory Blueprint", "core", AgentType.MEMORY)
KnowledgeBlueprint = lambda: make_blueprint("knowledge", "Knowledge Blueprint", "core", AgentType.KNOWLEDGE)
TaskBlueprint = lambda: make_blueprint("task", "Task Blueprint", "core", AgentType.TASK)
ToolBlueprint = lambda: make_blueprint("tool", "Tool Blueprint", "tool", AgentType.UTILITY)
UtilityBlueprint = lambda: make_blueprint("utility", "Utility Blueprint", "utility", AgentType.UTILITY)
ManagerBlueprint = lambda: make_blueprint("manager", "Manager Blueprint", "management", AgentType.COORDINATOR)
SupervisorBlueprint = lambda: make_blueprint("supervisor", "Supervisor Blueprint", "management", AgentType.SUPERVISOR)
CoordinatorBlueprint = lambda: make_blueprint("coordinator", "Coordinator Blueprint", "management", AgentType.COORDINATOR)
DepartmentBlueprint = lambda: make_blueprint("department", "Department Blueprint", "department", AgentType.COORDINATOR)
SpecialistBlueprint = lambda: make_blueprint("specialist", "Specialist Blueprint", "specialist", AgentType.WORKER)
AssistantBlueprint = lambda: make_blueprint("assistant", "Assistant Blueprint", "assistant", AgentType.WORKER)
AutomationBlueprint = lambda: make_blueprint("automation", "Automation Blueprint", "automation", AgentType.AUTOMATION)
BrowserBlueprint = lambda: make_blueprint("browser", "Browser Blueprint", "tool", AgentType.BROWSER)
VisionBlueprint = lambda: make_blueprint("vision", "Vision Blueprint", "tool", AgentType.VISION)
PhoneBlueprint = lambda: make_blueprint("phone", "Phone Blueprint", "tool", AgentType.PHONE)
CodingBlueprint = lambda: make_blueprint("coding", "Coding Blueprint", "engineering", AgentType.CODING)
EngineeringBlueprint = lambda: make_blueprint("engineering", "Engineering Blueprint", "engineering", AgentType.CODING)
HealthBlueprint = lambda: make_blueprint("health", "Health Blueprint", "monitoring", AgentType.MONITOR)
LearningBlueprint = lambda: make_blueprint("learning", "Learning Blueprint", "learning", AgentType.CUSTOM)
CustomBlueprint = lambda: make_blueprint("custom", "Custom Blueprint", "custom", AgentType.CUSTOM)

