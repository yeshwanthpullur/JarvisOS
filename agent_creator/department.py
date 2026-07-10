"""Department architecture for generated agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_creator.state import DepartmentState


@dataclass(slots=True)
class BaseDepartment:
    """Metadata for an agent department."""

    department_id: str
    name: str
    description: str = ""
    parent_department: str | None = None
    agents: tuple[str, ...] = ()
    shared_resources: dict[str, object] = field(default_factory=dict)
    state: DepartmentState = DepartmentState.CREATED


class DepartmentRegistry:
    """Registry for departments."""

    def __init__(self) -> None:
        self._departments: dict[str, BaseDepartment] = {}
        self.initialized = True

    def register(self, department: BaseDepartment) -> None:
        """Register a department."""
        department.state = DepartmentState.REGISTERED
        self._departments[department.department_id] = department

    def list_departments(self) -> tuple[BaseDepartment, ...]:
        """List departments."""
        return tuple(self._departments.values())


class DepartmentManager:
    """Coordinates department metadata."""

    def __init__(self, registry: DepartmentRegistry | None = None) -> None:
        self.registry = registry or DepartmentRegistry()
        self.initialized = True

    def initialize_defaults(self) -> None:
        """Register default departments."""
        if not self.registry.list_departments():
            self.registry.register(BaseDepartment("core", "Core Agents"))
            self.registry.register(BaseDepartment("engineering", "Engineering"))
            self.registry.register(BaseDepartment("research", "Research"))

