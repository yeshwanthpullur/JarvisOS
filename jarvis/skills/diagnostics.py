"""Bounded CLI rendering for declarative skill metadata."""

from __future__ import annotations

from .registry import SkillRegistry


def render_skill_command(registry: SkillRegistry, command: str, arguments: tuple[str, ...]) -> str:
    if command == "skill status":
        data = registry.registry_summary()
        return "Skill Registry: status=ready mode=plan_only external_plugins=disabled mcp=disabled " + " ".join(f"{key}={value}" for key, value in data.items())
    if command == "skill list":
        skills = registry.list_skills()
        bounded = tuple(item for item in skills if item.enabled)[:20] + tuple(item for item in skills if not item.enabled)[:10]
        return "Skills: " + ", ".join(f"{item.skill_id}:{item.status.value}" for item in bounded)
    if command == "skill capabilities":
        return "Skill capabilities: " + ", ".join(f"{skill}.{capability}:{kind}" for skill, capability, kind in registry.list_capabilities()[:45])
    if command == "skill diagnostics":
        return "Skill diagnostics: " + " ".join(f"{key}={value}" for key, value in registry.registry_summary().items())
    skill_id = arguments[0] if arguments else ""
    if command == "skill find":
        matches = registry.find_by_capability(skill_id)
        return f"Skill matches for {skill_id or 'none'}: " + (", ".join(item.skill_id for item in matches[:20]) or "none")
    skill = registry.get_skill(skill_id)
    if skill is None:
        return "Skill not found."
    if command == "skill permissions":
        permissions = ", ".join(item.value for item in skill.required_permissions) or "none"
        return f"Skill permissions {skill.skill_id}: permissions={permissions} approval_required={'yes' if skill.requires_approval else 'no'} execution_mode={skill.execution_mode.value}."
    capabilities = ", ".join(item.name for item in skill.capabilities) or "none"
    return f"Skill {skill.skill_id}: status={skill.status.value} enabled={'yes' if skill.enabled else 'no'} category={skill.category} capabilities={capabilities} local_only={'yes' if skill.local_only else 'no'}."
