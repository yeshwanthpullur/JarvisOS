"""Department models for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class JarvisDepartment:
    """Department metadata."""

    department_id: str
    name: str
    capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    enabled: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


CORE_DEPARTMENTS: tuple[JarvisDepartment, ...] = (
    JarvisDepartment("executive", "Executive"),
    JarvisDepartment("system", "System"),
    JarvisDepartment("memory", "Memory"),
    JarvisDepartment("knowledge", "Knowledge"),
    JarvisDepartment("planning", "Planning"),
    JarvisDepartment("research", "Research"),
    JarvisDepartment("coding", "Coding"),
    JarvisDepartment("tasks", "Tasks"),
    JarvisDepartment("health", "Health"),
    JarvisDepartment("engineering", "Engineering"),
    JarvisDepartment("learning", "Learning"),
    JarvisDepartment("automation", "Automation"),
    JarvisDepartment("communication", "Communication"),
    JarvisDepartment("productivity", "Productivity"),
    JarvisDepartment("media", "Media"),
)

