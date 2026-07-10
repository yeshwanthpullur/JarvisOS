"""Public wizard facade for agent creation workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from agent_creator.manifest import AgentManifest
from agent_creator.status import InstallationStatus, ValidationStatus
from agent_creator.utils import utc_now


@dataclass(slots=True)
class AgentCreationRequest:
    """Request metadata for creating an agent."""

    agent_name: str
    description: str
    blueprint: str
    template: str = "core_agent"
    department: str = "general"
    capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    configuration: dict[str, object] = field(default_factory=dict)
    priority: int = 100
    creator: str = "developer"
    request_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: utc_now().isoformat())
    validation_status: ValidationStatus = ValidationStatus.NOT_VALIDATED
    installation_status: InstallationStatus = InstallationStatus.NOT_INSTALLED
    completion_status: str = "requested"


@dataclass(frozen=True, slots=True)
class CreationPlan:
    """Serializable plan for the creation workflow."""

    requested_agent: str
    blueprint: str
    template: str
    manifest: AgentManifest
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    generated_files: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    rollback_strategy: str = "metadata_only"
    completion_status: str = "planned"


class PreviewGenerator:
    """Creates non-mutating previews for generation plans."""

    def preview(self, plan: CreationPlan) -> dict[str, object]:
        """Return a structured creation preview."""
        return {
            "agent": plan.requested_agent,
            "blueprint": plan.blueprint,
            "template": plan.template,
            "generated_files": list(plan.generated_files),
            "manifest": plan.manifest.to_dict(),
            "capabilities": list(plan.capabilities),
            "permissions": list(plan.permissions),
        }


class AgentWizard:
    """Single public interface for future interactive and automated creation."""

    def __init__(self) -> None:
        self.preview_generator = PreviewGenerator()
        self.history: list[AgentCreationRequest] = []
        self.initialized = True

    def generate_plan(self, request: AgentCreationRequest) -> CreationPlan:
        """Generate a metadata-only creation plan."""
        self.history.append(request)
        manifest = AgentManifest(
            name=request.agent_name,
            description=request.description,
            category=request.department,
            blueprint_id=request.blueprint,
            template_id=request.template,
            dependencies=request.dependencies,
            configuration=request.configuration,
        )
        return CreationPlan(
            requested_agent=request.agent_name,
            blueprint=request.blueprint,
            template=request.template,
            manifest=manifest,
            capabilities=request.capabilities,
            permissions=request.permissions,
            dependencies=request.dependencies,
        )

    def preview(self, plan: CreationPlan) -> dict[str, object]:
        """Preview a creation plan."""
        return self.preview_generator.preview(plan)

