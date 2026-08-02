"""Regression tests for normal free-form CLI chat routing."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from commands import CommandManager
from conversation import ConversationManager, ConversationResponse
from conversation.conversation_state import ConversationState
from core.startup_manager import StartupManager
from jarvis import JarvisContext, JarvisRequest
from jarvis.jarvis_controller import JarvisController
from provider_execution import ExecutionManager
from provider_execution.execution_context import ProviderExecutionContext
from provider_execution.execution_response import ProviderExecutionResponse


class _StubExecutionManager(ExecutionManager):
    def __init__(self, result: ProviderExecutionResponse) -> None:
        settings = SimpleNamespace(
            providers=SimpleNamespace(default_provider="ollama"),
        )
        super().__init__(context=ProviderExecutionContext(settings=settings))
        self.result = result
        self.last_request = None
        self.calls = 0

    def execute_through_provider_router(self, request):
        self.calls += 1
        self.last_request = request
        return self.result


class _ControllerCore:
    def __init__(self, execution: _StubExecutionManager) -> None:
        self.controller = JarvisController()
        self.context = JarvisContext(
            request_id="chat-hotfix",
            metadata={"provider_execution_manager": execution},
        )

    def handle(self, request: JarvisRequest):
        return self.controller.handle(request, self.context)


class ChatHotfixTests(unittest.TestCase):
    def manager_for(self, result: ProviderExecutionResponse):
        execution = _StubExecutionManager(result)
        manager = ConversationManager(jarvis_core=_ControllerCore(execution))
        manager.initialize()
        return manager, execution

    def test_plain_free_form_input_routes_to_configured_default_provider(self) -> None:
        manager, execution = self.manager_for(
            ProviderExecutionResponse(response="Paris.", provider="ollama", model="llama3.2:1b")
        )

        response = manager.handle_input("What is the capital of France?")

        self.assertEqual(response.response, "Paris.")
        self.assertEqual(response.conversation_state, ConversationState.RESPONDING)
        self.assertEqual(execution.calls, 1)
        self.assertEqual(execution.last_request.provider, "ollama")

    def test_unknown_natural_language_is_not_ignored(self) -> None:
        manager, execution = self.manager_for(
            ProviderExecutionResponse(response="Hello!", provider="ollama", model="llama3.2:1b")
        )

        response = manager.handle_input("hello")

        self.assertEqual(response.response, "Hello!")
        self.assertEqual(execution.calls, 1)

    def test_registered_command_stays_on_command_engine(self) -> None:
        manager, execution = self.manager_for(
            ProviderExecutionResponse(response="must not be used", provider="ollama")
        )

        response = manager.handle_input("provider status")

        self.assertIn("provider status", response.response.lower())
        self.assertEqual(execution.calls, 0)

    def test_provider_failure_is_visible_and_actionable(self) -> None:
        manager, _ = self.manager_for(
            ProviderExecutionResponse(
                response="",
                provider="ollama",
                success=False,
                diagnostics={
                    "fallback": (
                        {"provider": "ollama", "error": "Ollama service is unreachable."},
                    )
                },
            )
        )

        response = manager.handle_input("Tell me a short joke.")

        self.assertIn("Start Ollama", response.response)
        self.assertIn("provider status", response.response)
        self.assertEqual(response.conversation_state, ConversationState.FAILED)
        self.assertEqual(response.execution_state, "failed")
        self.assertIn("provider_execution_failed", response.warnings)

    def test_empty_cli_input_is_ignored_safely(self) -> None:
        commands = CommandManager()
        commands.initialize()
        handled: list[str] = []

        def handle_input(text: str) -> ConversationResponse:
            handled.append(text)
            return ConversationResponse("Shutting down.", should_exit=True)

        startup = StartupManager()
        startup.conversation_manager = SimpleNamespace(
            command_manager=commands,
            handle_input=handle_input,
        )
        with patch("builtins.input", side_effect=["", "exit"]), patch("builtins.print"):
            startup.command_loop()

        self.assertEqual(handled, ["exit"])


if __name__ == "__main__":
    unittest.main()
