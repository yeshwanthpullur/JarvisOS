import unittest
from types import SimpleNamespace

from commands import CommandManager
from conversation.conversation_intelligence import ConversationIntelligenceManager
from jarvis.autonomous_planning import AutonomousPlanning, PlanningProviderError
from jarvis.jarvis_context import JarvisContext
from jarvis.jarvis_controller import JarvisController
from jarvis.jarvis_request import JarvisRequest
from provider_execution import ExecutionManager, ProviderExecutionResponse


class FakeExecutionManager(ExecutionManager):
    def __init__(self, result: ProviderExecutionResponse) -> None:
        self.result = result
        self.requests = []
        self.context = SimpleNamespace(
            settings=SimpleNamespace(
                providers=SimpleNamespace(default_provider="ollama"),
                models=SimpleNamespace(local_only_default=True),
            )
        )

    def build_execution_request(self, intent, goal, **metadata):
        request = SimpleNamespace(intent=intent, goal=goal, **metadata)
        self.requests.append(request)
        return request

    def execute_through_provider_router(self, request):
        return self.result

    def validate_response(self, response):
        if response.success and not isinstance(response.response, str):
            return False, ("Successful responses must include response content.",)
        if response.success and not response.response.strip():
            return False, ("Successful responses must include response content.",)
        return True, ()


def provider_result(content="Useful local response", *, success=True, provider="ollama", warnings=(), diagnostics=None):
    return ProviderExecutionResponse(
        response=content,
        provider=provider,
        model="llama3.2:1b",
        success=success,
        warnings=warnings,
        diagnostics=diagnostics or {},
    )


class PostPhase6RoutingRepairTests(unittest.TestCase):
    def _conversation_request(self, prior_turn=False):
        conversation = ConversationIntelligenceManager()
        if prior_turn:
            conversation.prepare("hi")
            conversation.record_response("Hi.")
        text = "Tell me what you can currently do in 5 bullet points."
        plan = conversation.prepare(text)
        return text, plan.provider_input

    def _handle(self, original, provider_input, result):
        execution = FakeExecutionManager(result)
        context = JarvisContext(
            request_id="repair-test",
            autonomous_planning=AutonomousPlanning(),
            provider_execution_manager=execution,
            metadata={"provider_execution_manager": execution},
        )
        response = JarvisController().handle(
            JarvisRequest(
                content=provider_input,
                request_id="repair-test",
                metadata={"conversation_original_input": original},
            ),
            context,
        )
        return response, execution, context

    def test_simple_conversation_uses_direct_provider_path(self):
        response, _, context = self._handle("hi", "hi", provider_result("Hi."))
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Hi.")
        self.assertFalse(context.metadata["planning_assessment"].requires_plan)

    def test_capability_summary_context_does_not_trigger_planning(self):
        original, enriched = self._conversation_request(prior_turn=True)
        self.assertGreater(len(enriched.split()), 45)
        response, _, context = self._handle(original, enriched, provider_result("- Chat\n- Voice"))
        self.assertTrue(response.success)
        self.assertIn("Chat", response.content)
        self.assertFalse(context.metadata["planning_assessment"].requires_plan)

    def test_normal_planning_request_uses_configured_local_default(self):
        original = "Create a plan for implementing, testing, and documenting a safe feature."
        response, execution, context = self._handle(original, "[Context]\n" + original, provider_result("Local planning summary"))
        self.assertTrue(response.success)
        self.assertEqual(response.response_type, "planning")
        self.assertIn("Local planning summary", response.content)
        self.assertTrue(context.metadata["planning_assessment"].requires_plan)
        request = execution.requests[-1]
        self.assertEqual(request.provider, "ollama")
        self.assertTrue(request.metadata["local_only"])

    def test_malformed_provider_response_is_rejected_with_bounded_reason(self):
        planner = AutonomousPlanning()
        objective = planner.create_objective("r", "Create a plan for a safe local change")
        with self.assertRaisesRegex(PlanningProviderError, "invalid_empty_response"):
            planner.generate_with_provider(objective, FakeExecutionManager(provider_result(None)), {})

    def test_unavailable_provider_reports_normalized_reason(self):
        original = "Create a plan for implementing and testing this feature."
        failed = provider_result("", success=False, warnings=("connection refused",))
        response, _, _ = self._handle(original, original, failed)
        self.assertFalse(response.success)
        self.assertIn("reason=provider_unavailable", response.content)
        self.assertNotIn("no permitted provider produced", response.content.lower())

    def test_valid_local_provider_response_is_accepted(self):
        planner = AutonomousPlanning()
        objective = planner.create_objective("r", "Create a plan for a safe local change")
        plan = planner.generate_with_provider(objective, FakeExecutionManager(provider_result("Verified local summary")), {})
        self.assertIn("Verified local summary", plan.summary)
        self.assertTrue(plan.validation.valid)

    def test_structured_command_still_routes_through_command_manager(self):
        commands = CommandManager()
        commands.initialize()
        response = commands.execute("provider status")
        self.assertNotIn("unknown command", response.response.lower())


if __name__ == "__main__":
    unittest.main()
