from __future__ import annotations

import unittest

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from jarvis.skills import (
    SkillCapability,
    SkillExecutionMode,
    SkillManifest,
    SkillPermission,
    SkillRegistry,
    SkillRegistryError,
    SkillRiskLevel,
    SkillStatus,
    build_default_skill_registry,
)


class Phase3SkillRegistryTests(unittest.TestCase):
    def test_skill_models_and_permission_policy(self) -> None:
        capability = SkillCapability("status", "Read status.", "system")
        manifest = SkillManifest("status", "Status", "Status", "1", "JARVIS", "system", SkillStatus.READY, (capability,), enabled=True, execution_mode=SkillExecutionMode.PLAN_ONLY)
        self.assertEqual(manifest.risk_level, SkillRiskLevel.LOW)

    def test_side_effect_requires_approval(self) -> None:
        with self.assertRaises(ValueError):
            SkillCapability("write", "Write.", "files", side_effects=("files",))

    def test_duplicate_skill_and_capability_rejected(self) -> None:
        capability = SkillCapability("status", "Read status.", "system")
        with self.assertRaises(ValueError):
            SkillManifest("a", "A", "A", "1", "J", "system", SkillStatus.READY, (capability, capability), enabled=True)
        manifest = SkillManifest("a", "A", "A", "1", "J", "system", SkillStatus.READY, (capability,), enabled=True)
        registry = SkillRegistry((manifest,))
        with self.assertRaises(SkillRegistryError):
            registry.register_skill(manifest)

    def test_secrets_access_is_blocked(self) -> None:
        manifest = SkillManifest("secret", "Secret", "Blocked", "1", "J", "system", SkillStatus.FUTURE, (), required_permissions=(SkillPermission.SECRETS_ACCESS,), requires_approval=True)
        with self.assertRaises(SkillRegistryError):
            SkillRegistry((manifest,))

    def test_future_skills_are_not_executable(self) -> None:
        registry = build_default_skill_registry()
        self.assertEqual(registry.get_skill("mcp_gateway_skill").status, SkillStatus.FUTURE)
        self.assertFalse(registry.get_skill("mcp_gateway_skill").enabled)
        self.assertNotIn("mcp_gateway_skill", {item.skill_id for item in registry.list_skills(executable_only=True)})

    def test_builtin_skills_are_truthful(self) -> None:
        registry = build_default_skill_registry()
        self.assertEqual(registry.get_skill("web_read_only_skill").status, SkillStatus.READY)
        self.assertIn("workflow", registry.get_skill("video_workflow_skill").capabilities[0].name)
        self.assertTrue(registry.registry_summary()["valid"])

    def test_capability_and_category_lookup(self) -> None:
        registry = build_default_skill_registry()
        self.assertIn("memory_search_skill", {item.skill_id for item in registry.find_by_capability("memory")})
        self.assertIn("email_skill", {item.skill_id for item in registry.find_by_category("email")})

    def test_skill_cli_commands_are_bounded(self) -> None:
        registry = build_default_skill_registry()
        commands = CommandManager(); commands.initialize()
        context = ConversationContext(session=ConversationSession(), metadata={"skill_registry": registry})
        for command in (
            "skill status", "skill list", "skill capabilities", "skill show memory_search_skill",
            "skill find memory", "skill permissions memory_search_skill", "skill diagnostics",
        ):
            response = commands.execute(command, context).response
            self.assertTrue(response)
            self.assertLess(len(response), 6000)
            self.assertNotIn("C:\\Users", response)

    def test_config_defaults_disable_external_plugins(self) -> None:
        from config import load_settings

        config = load_settings().skills
        self.assertFalse(config.allow_external_plugins)
        self.assertFalse(config.allow_mcp)
        self.assertTrue(config.block_secrets_access)


if __name__ == "__main__":
    unittest.main()
