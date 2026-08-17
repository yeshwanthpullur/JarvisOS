from __future__ import annotations

import unittest
from pathlib import Path

from commands import CommandManager
from conversation import ConversationContext, ConversationManager, ConversationSession
from jarvis.documents import DocumentAgent
from jarvis.execution.cli import Phase4Runtime
from jarvis.jarvis_context import JarvisContext
from jarvis.jarvis_manager import JarvisManager
from jarvis.jarvis_request import JarvisRequest


class AuditRuntimeWiringTests(unittest.TestCase):
    def test_document_commands_use_provided_session_agent(self) -> None:
        commands = CommandManager()
        commands.initialize()
        agent = DocumentAgent(Path.cwd())
        context = ConversationContext(session=ConversationSession(), document_agent=agent)

        commands.execute("document plan summarize this file", context)

        self.assertEqual(len(agent.history), 1)
        history = commands.execute("document history", context).response
        self.assertIn(agent.history[0].request_id, history)

    def test_phase4_commands_use_provided_session_runtime(self) -> None:
        commands = CommandManager()
        commands.initialize()
        runtime = Phase4Runtime(Path.cwd())
        context = ConversationContext(session=ConversationSession(), phase4_runtime=runtime)

        response = commands.execute("approval request create file report.txt", context).response

        self.assertIn("Approval: id=", response)
        self.assertEqual(len(runtime.approvals.requests), 1)

    def test_conversation_manager_preserves_later_phase_singletons(self) -> None:
        document_agent = DocumentAgent(Path.cwd())
        phase4_runtime = Phase4Runtime(Path.cwd())
        manager = ConversationManager(
            document_agent=document_agent,
            phase4_runtime=phase4_runtime,
        )
        manager.initialize()

        manager.handle_input("document plan summarize this file")
        manager.handle_input("approval request create file report.txt")

        self.assertEqual(len(document_agent.history), 1)
        self.assertEqual(len(phase4_runtime.approvals.requests), 1)

    def test_jarvis_manager_context_exposes_later_phase_foundations(self) -> None:
        manager = JarvisManager(context=JarvisContext(request_id="base"))
        request = JarvisRequest(content="status")

        context = manager._context_for_request(request)

        self.assertIs(context.document_agent, manager.document_agent)
        self.assertIs(context.browser_agent, manager.browser_agent)
        self.assertIs(context.scheduler_agent, manager.scheduler_agent)
        self.assertIs(context.communication_agent, manager.communication_agent)
        self.assertIs(context.adapter_agent, manager.adapter_agent)
        self.assertIs(context.phase4_runtime, manager.phase4_runtime)
        self.assertIs(context.metadata["phase4_runtime"], manager.phase4_runtime)


if __name__ == "__main__":
    unittest.main()
