from __future__ import annotations

import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path

from commands.command_parser import CommandParser
from jarvis.jarvis_context import JarvisContext
from jarvis.jarvis_controller import JarvisController
from jarvis.jarvis_request import JarvisRequest
from jarvis.jarvis_tools import (
    JarvisToolRecord,
    JarvisTools,
    ToolLimits,
    ToolMode,
    ToolRiskClass,
    ToolStatus,
)


class ToolIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tools = JarvisTools()

    def test_safe_tools_are_registered(self): self.assertIsNotNone(self.tools.lookup("core.calculator"))
    def test_duplicate_registration_rejected(self):
        with self.assertRaises(ValueError): self.tools.register(self.tools.lookup("core.calculator"))  # type: ignore[arg-type]
    def test_malformed_registration_rejected(self):
        with self.assertRaises(ValueError): self.tools.register(JarvisToolRecord("?", "bad", ("x",)))
    def test_executable_tool_requires_capability(self):
        with self.assertRaises(ValueError): self.tools.register(JarvisToolRecord("valid.tool", "bad", implementation=lambda _: {}))
    def test_assessment_avoids_provider_question(self): self.assertFalse(self.tools.assess("Explain Python").requires_tool)
    def test_assessment_detects_calculator(self): self.assertEqual(self.tools.assess("calculate 2 + 3").requested_capability, "calculate")
    def test_assessment_detects_transform(self): self.assertEqual(self.tools.assess("make hello uppercase").arguments["operation"], "upper")
    def test_match_by_capability(self): self.assertEqual(self.tools.match("calculate").selected_tool_id, "core.calculator")
    def test_missing_capability_has_no_selection(self): self.assertIsNone(self.tools.match("unknown").selected_tool_id)
    def test_permission_rejection(self): self.assertIsNone(self.tools.match("calculate", ()).selected_tool_id)
    def test_missing_argument_requires_clarification(self): self.assertEqual(self.tools.prepare("r", "core.calculator", "calculate", {}).decision, "require_clarification")
    def test_unknown_argument_rejected(self): self.assertIn("unknown_arguments", self.tools.prepare("r", "core.calculator", "calculate", {"expression": "2+2", "extra": 1}).reason)
    def test_secret_argument_rejected(self): self.assertEqual(self.tools.prepare("r", "core.calculator", "calculate", {"expression": "2+2", "token": "x"}).decision, "require_clarification")
    def test_real_calculation(self):
        result = self.tools.execute(self.tools.prepare("r", "core.calculator", "calculate", {"expression": "2 + 3 * 4"}), executive_approved=True)
        self.assertEqual((result.status, result.content), (ToolStatus.COMPLETED, "14"))
    def test_unsupported_expression_fails(self):
        result = self.tools.execute(self.tools.prepare("r", "core.calculator", "calculate", {"expression": "open('x')"}), executive_approved=True)
        self.assertEqual(result.status, ToolStatus.FAILED)
    def test_text_transform(self):
        result = self.tools.execute(self.tools.prepare("r", "core.text_transform", "text_transform", {"text": "Hello", "operation": "lower"}), executive_approved=True)
        self.assertEqual(result.content, "hello")
    def test_dry_run_does_not_execute(self):
        calls = []
        self.tools.register(JarvisToolRecord("test.dry", "dry", ("dry",), input_schema={"type": "object", "additionalProperties": False}, implementation=lambda _: calls.append(1)))
        result = self.tools.execute(self.tools.prepare("r", "test.dry", "dry", {}, dry_run=True), executive_approved=True)
        self.assertTrue(result.success); self.assertEqual(calls, [])
    def test_executive_approval_is_required(self):
        result = self.tools.execute(self.tools.prepare("r", "core.calculator", "calculate", {"expression": "1+1"}))
        self.assertEqual(result.status, ToolStatus.REJECTED)
    def test_confirm_mode_requires_approval_reference(self):
        self.tools.set_mode("confirm")
        self.assertEqual(self.tools.prepare("r", "core.calculator", "calculate", {"expression": "1+1"}).decision, "require_approval")
    def test_high_risk_requires_approval(self):
        self.tools.register(JarvisToolRecord("test.high", "high", ("high",), risk_class=ToolRiskClass.HIGH, implementation=lambda _: {"result": "ok"}))
        self.assertEqual(self.tools.prepare("r", "test.high", "high", {}).decision, "require_approval")
    def test_mode_off_blocks(self): self.tools.set_mode("off"); self.assertEqual(self.tools.prepare("r", "core.calculator", "calculate", {"expression": "1"}).decision, "blocked")
    def test_invalid_output_rejected(self):
        self.tools.register(JarvisToolRecord("test.output", "output", ("output",), output_schema={"type": "object", "required": ["needed"]}, implementation=lambda _: {"other": 1}))
        result = self.tools.execute(self.tools.prepare("r", "test.output", "output", {}), executive_approved=True)
        self.assertEqual(result.status, ToolStatus.INVALID_OUTPUT)
    def test_timeout_is_normalized(self):
        tools = JarvisTools(limits=ToolLimits(maximum_timeout_seconds=1))
        tools.register(JarvisToolRecord("test.slow", "slow", ("slow",), timeout_seconds=1, implementation=lambda _: time.sleep(1.2)))
        result = tools.execute(tools.prepare("r", "test.slow", "slow", {}), executive_approved=True)
        self.assertEqual(result.status, ToolStatus.TIMED_OUT)
    def test_history_and_invocation(self):
        result = self.tools.execute(self.tools.prepare("r", "core.calculator", "calculate", {"expression": "4"}), executive_approved=True)
        self.assertEqual(self.tools.invocation(result.invocation_id), result)
    def test_request_limit(self):
        tools = JarvisTools(limits=ToolLimits(maximum_per_request=1))
        one = tools.prepare("same", "core.calculator", "calculate", {"expression": "1"})
        tools.execute(one, executive_approved=True)
        two = tools.execute(tools.prepare("same", "core.calculator", "calculate", {"expression": "2"}), executive_approved=True)
        self.assertEqual(two.status, ToolStatus.BLOCKED)
    def test_persistence_excludes_structured_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            tools = JarvisTools(Path(directory)); tools.execute(tools.prepare("r", "core.calculator", "calculate", {"expression": "2"}), executive_approved=True)
            content = (Path(directory) / "history.json").read_text()
            self.assertNotIn("validated_arguments", content)
    def test_command_parser_separates_tool_commands(self): self.assertEqual(CommandParser().parse("tool match calculate").name, "tool match")
    def test_controller_uses_tool_for_calculation(self):
        context = JarvisContext(request_id="r", tool_manager=self.tools)
        response = JarvisController().handle(JarvisRequest(content="calculate 7 * 6", request_id="r"), context)
        self.assertEqual((response.response_type, response.content), ("tool", "42"))
    def test_controller_leaves_normal_chat_on_existing_path(self):
        context = JarvisContext(request_id="r", tool_manager=self.tools)
        response = JarvisController().handle(JarvisRequest(content="Explain Python", request_id="r"), context)
        self.assertNotEqual(response.response_type, "tool")
    def test_mutation_requires_approval_and_idempotency(self):
        self.tools.register(JarvisToolRecord("test.write", "write", ("write",), mutation_type="write", risk_class=ToolRiskClass.MODERATE, implementation=lambda _: {"result": "ok"}))
        pending = self.tools.prepare("r", "test.write", "write", {})
        approved = self.tools.prepare("r", "test.write", "write", {}, approval_reference="approval-1")
        self.assertEqual(pending.decision, "require_approval"); self.assertIsNotNone(approved.request.idempotency_key)  # type: ignore[union-attr]
    def test_task_workflow_and_coordination_ids_preserved(self):
        plan = self.tools.prepare("r", "core.calculator", "calculate", {"expression": "3"}, coordination_id="c", workflow_id="w", task_id="t")
        result = self.tools.execute(plan, executive_approved=True)
        self.assertEqual((result.coordination_id, result.workflow_id, result.task_id), ("c", "w", "t"))


if __name__ == "__main__": unittest.main()
