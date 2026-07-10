"""Installer interfaces for generated agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from agent_creator.builder import AgentBuildPlan
from agent_creator.catalog import AgentCatalog, CatalogEntry
from agent_creator.registry import DynamicAgentRegistry, GeneratedAgentRecord
from agent_creator.rollback import RollbackManager, RollbackPlan
from agent_creator.status import InstallationStatus
from agent_creator.utils import utc_now


@dataclass(frozen=True, slots=True)
class InstallationReport:
    """Report returned by installation operations."""

    agent_id: str
    status: InstallationStatus
    target_path: Path
    installed_files: tuple[Path, ...] = ()
    rollback_plan: RollbackPlan | None = None
    messages: tuple[str, ...] = ()
    timestamp: str = field(default_factory=lambda: utc_now().isoformat())


class AgentInstaller:
    """Installs generated agent packages into a caller-provided directory."""

    def __init__(
        self,
        registry: DynamicAgentRegistry | None = None,
        catalog: AgentCatalog | None = None,
        rollback_manager: RollbackManager | None = None,
    ) -> None:
        self.registry = registry or DynamicAgentRegistry()
        self.catalog = catalog or AgentCatalog()
        self.rollback_manager = rollback_manager or RollbackManager()
        self.initialized = True

    def plan_installation(self, plan: AgentBuildPlan, destination_root: Path) -> tuple[Path, ...]:
        """Return paths that would be written during installation."""
        package_root = destination_root / plan.package_name
        return tuple(package_root / relative for relative in sorted(plan.generated_files))

    def install(self, plan: AgentBuildPlan, destination_root: Path, write_files: bool = False) -> InstallationReport:
        """Install an agent package, optionally writing generated files."""
        package_root = destination_root / plan.package_name
        target_files = self.plan_installation(plan, destination_root)
        rollback = self.rollback_manager.prepare(plan.manifest.agent_id, package_root, target_files)
        if write_files:
            package_root.mkdir(parents=True, exist_ok=True)
            for relative, content in plan.generated_files.items():
                target = package_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

        record = GeneratedAgentRecord(
            manifest=plan.manifest,
            package_name=plan.package_name,
            installed=True,
            enabled=False,
        )
        self.registry.register(record)
        self.catalog.add(CatalogEntry(plan.manifest, plan.manifest.template_id, plan.manifest.blueprint_id, installed_at=utc_now().isoformat()))
        return InstallationReport(
            agent_id=plan.manifest.agent_id,
            status=InstallationStatus.INSTALLED,
            target_path=package_root,
            installed_files=target_files,
            rollback_plan=rollback,
            messages=("Installation metadata recorded.",),
        )

    def uninstall(self, agent_id: str) -> InstallationReport:
        """Return uninstall metadata without deleting files."""
        record = self.registry.get(agent_id)
        if record is None:
            return InstallationReport(agent_id=agent_id, status=InstallationStatus.FAILED, target_path=Path("."), messages=("Agent not registered.",))
        record.installed = False
        return InstallationReport(agent_id=agent_id, status=InstallationStatus.NOT_INSTALLED, target_path=Path(record.package_name), messages=("Uninstall metadata recorded.",))

