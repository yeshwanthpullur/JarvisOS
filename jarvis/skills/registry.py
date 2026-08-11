"""Controlled, non-executing skill registry."""

from __future__ import annotations

from .models import SkillManifest, SkillPermission, SkillStatus


class SkillRegistryError(ValueError):
    pass


class SkillRegistry:
    def __init__(self, skills: tuple[SkillManifest, ...] = (), *, max_skills: int = 512, block_secrets_access: bool = True) -> None:
        self.max_skills = max(1, min(max_skills, 512))
        self.block_secrets_access = block_secrets_access
        self._skills: dict[str, SkillManifest] = {}
        for skill in skills:
            self.register_skill(skill)

    def register_skill(self, skill: SkillManifest) -> None:
        if skill.skill_id in self._skills:
            raise SkillRegistryError(f"duplicate_skill:{skill.skill_id}")
        if len(self._skills) >= self.max_skills:
            raise SkillRegistryError("skill_registry_limit_exceeded")
        if self.block_secrets_access and SkillPermission.SECRETS_ACCESS in skill.required_permissions:
            raise SkillRegistryError("secrets_access_blocked")
        self._skills[skill.skill_id] = skill

    def get_skill(self, skill_id: str) -> SkillManifest | None:
        return self._skills.get(skill_id)

    def list_skills(self, *, executable_only: bool = False) -> tuple[SkillManifest, ...]:
        skills = tuple(self._skills.values())
        if executable_only:
            skills = tuple(item for item in skills if item.enabled and item.status is SkillStatus.READY)
        return skills

    def list_capabilities(self) -> tuple[tuple[str, str, str], ...]:
        return tuple((skill.skill_id, capability.name, capability.capability_type) for skill in self._skills.values() for capability in skill.capabilities)

    def find_by_capability(self, query: str) -> tuple[SkillManifest, ...]:
        needle = query.strip().lower()
        return tuple(skill for skill in self._skills.values() if needle in skill.skill_id.lower() or needle in skill.category.lower() or any(needle in cap.name.lower() or needle in cap.capability_type.lower() for cap in skill.capabilities))

    def find_by_category(self, category: str) -> tuple[SkillManifest, ...]:
        return tuple(item for item in self._skills.values() if item.category.lower() == category.strip().lower())

    def skill_status(self, skill_id: str) -> SkillStatus | None:
        item = self.get_skill(skill_id)
        return item.status if item else None

    def registry_summary(self) -> dict[str, int | bool]:
        skills = self.list_skills()
        capabilities = [cap for item in skills for cap in item.capabilities]
        return {
            "total_skills": len(skills),
            "ready_skills": sum(item.status is SkillStatus.READY for item in skills),
            "future_skills": sum(item.status is SkillStatus.FUTURE for item in skills),
            "unavailable_skills": sum(item.status in {SkillStatus.UNAVAILABLE, SkillStatus.NOT_CONFIGURED, SkillStatus.ERROR} for item in skills),
            "approval_required_skills": sum(item.requires_approval for item in skills),
            "total_capabilities": len(capabilities),
            "valid": not self.validate_registry(),
        }

    def validate_registry(self) -> tuple[str, ...]:
        errors = []
        for item in self._skills.values():
            if self.block_secrets_access and SkillPermission.SECRETS_ACCESS in item.required_permissions:
                errors.append(f"secrets_access:{item.skill_id}")
            if item.status is SkillStatus.READY and not item.enabled:
                errors.append(f"ready_disabled:{item.skill_id}")
        return tuple(errors[:32])
