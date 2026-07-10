"""Department registry for Executive JARVIS."""

from __future__ import annotations

from jarvis.jarvis_departments import CORE_DEPARTMENTS, JarvisDepartment


class JarvisDepartmentRegistry:
    """Registers and looks up executive departments."""

    def __init__(self) -> None:
        self._departments: dict[str, JarvisDepartment] = {}
        self.initialized = True

    def load_defaults(self) -> None:
        """Load core departments."""
        for department in CORE_DEPARTMENTS:
            self.register(department)

    def register(self, department: JarvisDepartment) -> None:
        """Register a department."""
        self._departments[department.department_id] = department

    def unregister(self, department_id: str) -> bool:
        """Unregister a department."""
        return self._departments.pop(department_id, None) is not None

    def lookup(self, department_id: str) -> JarvisDepartment | None:
        """Lookup a department."""
        return self._departments.get(department_id)

    def list_departments(self) -> tuple[JarvisDepartment, ...]:
        """List departments."""
        return tuple(self._departments.values())

    def enable(self, department_id: str) -> None:
        """Enable hook for future department state."""

    def disable(self, department_id: str) -> None:
        """Disable hook for future department state."""

