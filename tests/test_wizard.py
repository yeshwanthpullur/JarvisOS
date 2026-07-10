"""Tests for Agent Creation Wizard."""

from __future__ import annotations

import unittest

from agent_creator.wizard import AgentCreationRequest, AgentWizard


class WizardTests(unittest.TestCase):
    """Wizard tests."""

    def test_wizard_generates_plan(self) -> None:
        wizard = AgentWizard()
        plan = wizard.generate_plan(AgentCreationRequest("Demo", "Demo", "custom"))
        self.assertEqual(plan.requested_agent, "Demo")
        self.assertEqual(plan.blueprint, "custom")

    def test_wizard_preserves_request_history(self) -> None:
        wizard = AgentWizard()
        request = AgentCreationRequest("Demo", "Demo", "custom")
        wizard.generate_plan(request)
        self.assertEqual(wizard.history, [request])

    def test_preview_contains_manifest(self) -> None:
        wizard = AgentWizard()
        plan = wizard.generate_plan(AgentCreationRequest("Demo", "Demo", "custom"))
        preview = wizard.preview(plan)
        self.assertEqual(preview["agent"], "Demo")
        self.assertIn("manifest", preview)

    def test_creation_request_defaults(self) -> None:
        request = AgentCreationRequest("Demo", "Demo", "custom")
        self.assertEqual(request.template, "core_agent")
        self.assertEqual(request.completion_status, "requested")

    def test_creation_plan_is_serializable_shape(self) -> None:
        plan = AgentWizard().generate_plan(AgentCreationRequest("Demo", "Demo", "custom"))
        self.assertTrue(plan.plan_id)
        self.assertTrue(plan.manifest.to_dict()["agent_id"])

    def test_wizard_initialized(self) -> None:
        self.assertTrue(AgentWizard().initialized)

