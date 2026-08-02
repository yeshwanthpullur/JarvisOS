"""Tests for the planning-only Mobile Automation foundation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from commands import CommandManager
from conversation.conversation_context import ConversationContext
from conversation.conversation_session import ConversationSession
from jarvis.mobile_automation import (
    MobileActionRequest,
    MobileActionType,
    MobileAutomationManager,
    MobileAutomationStatus,
    NullMobileAutomationAdapter,
    PlanningOnlyMobileAdapter,
    SAFE_ACTIONS,
)


def settings(**overrides):
    values = dict(automation_enabled=True, automation_mode="planning_only", automation_adapter="planning-only", audit_retention=5, live_control_enabled=False, store_private_data=False)
    values.update(overrides)
    return SimpleNamespace(mobile=SimpleNamespace(**values))


class MobileAutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.manager = MobileAutomationManager(Path(self.temp.name), settings())

    def tearDown(self):
        self.temp.cleanup()

    def test_default_is_planning_only_without_phone_access(self):
        state = self.manager.status()
        self.assertEqual(state["status"], "partial")
        self.assertEqual(state["mode"], "planning_only")
        self.assertEqual(state["adapter_id"], "planning-only")
        self.assertFalse(state["real_phone_adapter"])
        self.assertFalse(state["live_control"])
        self.assertEqual(state["private_data_access"], "blocked")
        self.assertEqual(self.manager.device_summaries(), ())

    def test_adapters_are_truthful_and_have_no_live_control(self):
        self.assertFalse(NullMobileAutomationAdapter().available)
        self.assertFalse(NullMobileAutomationAdapter().live_control)
        self.assertTrue(PlanningOnlyMobileAdapter().available)
        self.assertFalse(PlanningOnlyMobileAdapter().live_control)
        result = NullMobileAutomationAdapter().execute(MobileActionRequest("r", MobileActionType.STATUS))
        self.assertEqual(result.status, MobileAutomationStatus.UNAVAILABLE)
        self.assertEqual(result.error_code, "MOBILE_NO_ADAPTER")

    def test_safe_actions_never_create_device_state(self):
        for action in SAFE_ACTIONS:
            with self.subTest(action=action):
                result = self.manager.execute(MobileActionRequest(str(action), action))
                self.assertIn(result.status, {MobileAutomationStatus.PARTIAL, MobileAutomationStatus.CLOSED})
        self.assertFalse(self.manager.sessions)
        self.assertEqual(self.manager.device_summaries(), ())

    def test_every_sensitive_action_is_blocked_before_adapter_dispatch(self):
        for action in set(MobileActionType) - set(SAFE_ACTIONS):
            with self.subTest(action=action):
                result = self.manager.execute(MobileActionRequest(str(action), action, "private payload"))
                self.assertEqual(result.status, MobileAutomationStatus.BLOCKED_BY_POLICY)
                self.assertTrue(result.approval_required)
                self.assertIn(result.error_code, {"MOBILE_ACTION_BLOCKED", "MOBILE_PRIVATE_DATA_BLOCKED"})

    def test_sensitive_plans_are_blocked_and_safe_plans_do_not_execute(self):
        for objective in ("send a message", "read my notifications", "make a call", "access camera", "use microphone", "track location", "install app", "unlock phone"):
            with self.subTest(objective=objective):
                self.assertEqual(self.manager.plan(objective).status, MobileAutomationStatus.BLOCKED_BY_POLICY)
        result = self.manager.plan("prepare a future Android testing checklist")
        self.assertEqual(result.status, MobileAutomationStatus.PARTIAL)
        self.assertIn("Nothing was connected", result.message)

    def test_audit_is_bounded_and_does_not_retain_request_content(self):
        secret_text = "send a message to Private Person at 5551234567"
        for _ in range(8):
            self.manager.plan(secret_text)
        self.assertEqual(len(self.manager.audit_events()), 5)
        stored = self.manager.audit_path.read_text(encoding="utf-8")
        self.assertNotIn(secret_text, stored)
        self.assertNotIn("Private Person", stored)
        self.assertNotIn("5551234567", stored)
        self.assertTrue(all(event.safe_summary == "mobile request evaluated; private content not retained" for event in self.manager.audit_events()))

    def test_disabled_mode_is_safe(self):
        manager = MobileAutomationManager(Path(self.temp.name), settings(automation_enabled=False))
        result = manager.setup()
        self.assertEqual(result.status, MobileAutomationStatus.DISABLED)
        self.assertEqual(result.error_code, "MOBILE_DISABLED")


class MobileCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.mobile = MobileAutomationManager(Path(self.temp.name), settings())
        self.commands = CommandManager(); self.commands.initialize()
        self.context = ConversationContext(ConversationSession(), mobile_automation=self.mobile)

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, text):
        return self.commands.execute(text, self.context)

    def test_status_policy_capabilities_setup_audit_close(self):
        self.assertIn("planning_only", self.execute("mobile status").response)
        self.assertIn("private_data_access=blocked", self.execute("mobile status").response)
        self.assertIn("Private phone data", self.execute("mobile policy").response)
        self.assertIn("future_blocked", self.execute("mobile capabilities").response)
        self.assertIn("Future Android support", self.execute("mobile setup").response)
        self.assertIn("Mobile audit", self.execute("mobile audit").response)
        self.assertIn("closed", self.execute("mobile close").response)
        self.assertIn("no phone identifiers", self.execute("mobile devices").response)
        self.assertIn("no device connection", self.execute("mobile session").response)

    def test_plan_command_blocks_sensitive_requests(self):
        self.assertIn("Usage", self.execute("mobile plan").response)
        for text in ("mobile plan send a message", "mobile plan read my notifications", "mobile plan make a call", "mobile plan access camera"):
            response = self.execute(text)
            self.assertIn("blocked_by_policy", response.response)
            self.assertEqual(response.metadata["error_code"], "MOBILE_ACTION_BLOCKED")

    def test_commands_are_registered_and_stay_on_command_path(self):
        for text in ("mobile status", "mobile policy", "mobile capabilities", "mobile setup", "mobile plan safe checklist", "mobile audit", "mobile close"):
            with self.subTest(text=text):
                response = self.execute(text)
                self.assertNotIn("Unknown command", response.response)


class MobileTrackingTests(unittest.TestCase):
    def test_mobile_config_defaults_are_private(self):
        from config.defaults import DEFAULT_CONFIG
        config = DEFAULT_CONFIG["mobile"]
        self.assertEqual(config["automation_mode"], "planning_only")
        self.assertFalse(config["live_control_enabled"])
        self.assertFalse(config["store_private_data"])

    def test_mobile_docs_and_health_are_honest(self):
        root = Path(__file__).resolve().parents[1]
        guide = root / "docs" / "MOBILE_AUTOMATION.md"
        self.assertTrue(guide.is_file())
        text = guide.read_text(encoding="utf-8")
        self.assertIn("Live phone control is not implemented", text)
        self.assertIn("Private mobile data is not accessed", text)
        health = json.loads((root / "docs" / "project_health.json").read_text(encoding="utf-8"))
        mobile = next(item for item in health["categories"] if item["name"] == "Mobile Automation")
        self.assertEqual(mobile["status"], "Partial")
        self.assertLessEqual(mobile["confidence"], 50)


if __name__ == "__main__":
    unittest.main()
