"""Behavioral tests for Context Intelligence integration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from commands import CommandManager
from context_intelligence import ContextIntelligenceManager
from conversation import ConversationContext, ConversationManager, ConversationSession
from memory import MemoryManager
from personal_intelligence import PersonalIntelligenceManager
from retrieval import RetrievalManager
from task_intelligence import TaskIntelligenceManager
from workflow import WorkflowManager
from workflow.workflow_builder import WorkflowStep
from research import ResearchHistoryRecord, ResearchManager
from jarvis import JarvisCore
from core.startup_manager import StartupManager
from core.health_checker import HealthChecker


class ContextIntelligenceTests(unittest.TestCase):
    """Context intelligence behaviors should remain grounded and explainable."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.memory = MemoryManager(Path(self.tempdir.name))
        self.memory.initialize()
        self.retrieval = RetrievalManager()
        self.retrieval.initialize()
        self.personal = PersonalIntelligenceManager(memory_manager=self.memory, retrieval_manager=self.retrieval)
        self.personal.initialize()
        self.tasks = TaskIntelligenceManager()
        self.tasks.initialize()
        self.workflows = WorkflowManager()
        self.workflows.initialize()
        self.research = ResearchManager()
        self.research.initialize()
        self.context_manager = ContextIntelligenceManager(
            retrieval_manager=self.retrieval,
            personal_intelligence_manager=self.personal,
            task_intelligence_manager=self.tasks,
            workflow_manager=self.workflows,
            research_manager=self.research,
            memory_manager=self.memory,
        )
        self.context_manager.initialize()
        self.session = ConversationSession()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_establish_context_and_objective(self) -> None:
        project = self.tasks.project_manager.create_project("Drone Project")
        resolution = self.context_manager.prepare_request("Continue the Drone Project.", self.session)
        self.assertEqual(resolution.status, "resolved")
        self.assertEqual(self.context_manager.current_context(self.session).source_reference, project.project_id)
        self.assertIn("Drone Project", self.context_manager.current_objective(self.session))

    def test_continue_uses_active_context(self) -> None:
        self.tasks.project_manager.create_project("Robotic Arm Project")
        self.context_manager.prepare_request("Continue the Robotic Arm Project.", self.session)
        resolution = self.context_manager.prepare_request("Continue.", self.session)
        self.assertEqual(resolution.status, "resolved")
        self.assertIn("Robotic Arm Project", resolution.immediate_response or "")

    def test_context_switch_uses_new_active_project(self) -> None:
        self.tasks.project_manager.create_project("Project A")
        project_b = self.tasks.project_manager.create_project("Project B")
        self.context_manager.prepare_request("Continue Project A.", self.session)
        self.context_manager.prepare_request("Continue Project B.", self.session)
        self.assertEqual(self.context_manager.current_context(self.session).source_reference, project_b.project_id)

    def test_go_back_to_previous_project_restores_context(self) -> None:
        project_a = self.tasks.project_manager.create_project("Project A")
        self.tasks.project_manager.create_project("Project B")
        self.context_manager.prepare_request("Continue Project A.", self.session)
        self.context_manager.prepare_request("Continue Project B.", self.session)
        resolution = self.context_manager.prepare_request("Go back to the previous project.", self.session)
        self.assertEqual(resolution.status, "resolved")
        self.assertEqual(self.context_manager.current_context(self.session).source_reference, project_a.project_id)

    def test_ambiguous_reference_requests_clarification(self) -> None:
        self.tasks.project_manager.create_project("Drone Project")
        self.tasks.project_manager.create_project("Robotic Arm Project")
        self.context_manager.prepare_request("Continue the Drone Project.", self.session)
        self.context_manager.prepare_request("Continue the Robotic Arm Project.", self.session)
        resolution = self.context_manager.resolve_reference("Use that project.", self.session)
        self.assertTrue(resolution.ambiguity)
        self.assertIn("Do you mean", resolution.immediate_response or "")

    def test_missing_context_is_truthful(self) -> None:
        resolution = self.context_manager.prepare_request("Continue.", self.session)
        self.assertEqual(resolution.status, "missing")
        self.assertIn("reliable continuation", resolution.immediate_response or "")

    def test_pending_clarification_is_restored(self) -> None:
        self.tasks.project_manager.create_project("Robotics Project")
        self.context_manager.prepare_request("Continue the Robotics Project.", self.session)
        self.context_manager.set_pending_state(self.session, "pending_clarification", "Need your choice of motor controller.")
        resolution = self.context_manager.prepare_request("Continue.", self.session)
        self.assertEqual(resolution.pending_state["kind"], "pending_clarification")
        self.assertIn("motor controller", resolution.immediate_response or "")

    def test_current_instruction_override_switches_project(self) -> None:
        self.tasks.project_manager.create_project("Project A")
        project_b = self.tasks.project_manager.create_project("Project B")
        self.context_manager.prepare_request("Continue Project A.", self.session)
        self.context_manager.prepare_request("Continue Project B.", self.session)
        self.assertEqual(self.context_manager.current_context(self.session).source_reference, project_b.project_id)

    def test_stale_project_reference_is_detected(self) -> None:
        project = self.tasks.project_manager.create_project("Short Lived Project")
        self.context_manager.prepare_request("Continue the Short Lived Project.", self.session)
        del self.tasks.project_manager._projects[project.project_id]
        resolution = self.context_manager.prepare_request("Continue.", self.session)
        self.assertEqual(resolution.status, "stale")

    def test_what_were_we_doing_returns_objective_and_work(self) -> None:
        self.tasks.project_manager.create_project("Calibration Project")
        self.context_manager.prepare_request("Continue the Calibration Project.", self.session)
        resolution = self.context_manager.prepare_request("What were we doing?", self.session)
        self.assertIn("Current objective", resolution.immediate_response or "")
        self.assertIn("Calibration Project", resolution.immediate_response or "")

    def test_clear_context_does_not_delete_authoritative_project(self) -> None:
        project = self.tasks.project_manager.create_project("Persistent Project")
        self.context_manager.prepare_request("Continue the Persistent Project.", self.session)
        resolution = self.context_manager.prepare_request("Clear context", self.session)
        self.assertEqual(resolution.status, "cleared")
        self.assertIsNone(self.context_manager.current_context(self.session))
        self.assertTrue(any(item.project_id == project.project_id for item in self.tasks.project_manager.list_projects()))

    def test_pause_and_resume_context(self) -> None:
        self.tasks.project_manager.create_project("Paused Project")
        self.context_manager.prepare_request("Continue the Paused Project.", self.session)
        paused = self.context_manager.prepare_request("Pause this", self.session)
        resumed = self.context_manager.prepare_request("Resume this", self.session)
        self.assertEqual(paused.status, "suspended")
        self.assertEqual(resumed.status, "resolved")

    def test_workflow_context_is_resolved(self) -> None:
        definition = self.workflows.builder.create("Build Workflow", (WorkflowStep("Step 1"),))
        self.workflows.create_workflow(definition)
        resolution = self.context_manager.prepare_request("Resume the Build Workflow workflow.", self.session)
        self.assertEqual(resolution.status, "resolved")
        self.assertEqual(self.context_manager.current_context(self.session).context_type, "workflow_reference")

    def test_research_context_is_resolved(self) -> None:
        self.research.history.record(
            ResearchHistoryRecord(
                research_id="research-1",
                topic="Robotics Research",
                strategy="knowledge_first",
            )
        )
        resolution = self.context_manager.prepare_request("Continue the research.", self.session)
        self.assertEqual(resolution.status, "resolved")

    def test_context_command_show(self) -> None:
        self.tasks.project_manager.create_project("Command Project")
        self.context_manager.prepare_request("Continue the Command Project.", self.session)
        manager = CommandManager()
        manager.initialize()
        context = ConversationContext(
            session=self.session,
            metadata={"context_intelligence_manager": self.context_manager},
        )
        response = manager.execute("context show", context)
        self.assertIn("Command Project", response.response)

    def test_context_command_clear(self) -> None:
        self.tasks.project_manager.create_project("Clearable Project")
        self.context_manager.prepare_request("Continue the Clearable Project.", self.session)
        manager = CommandManager()
        manager.initialize()
        context = ConversationContext(
            session=self.session,
            metadata={"context_intelligence_manager": self.context_manager},
        )
        response = manager.execute("context clear", context)
        self.assertIn("cleared", response.response.lower())
        self.assertIsNone(self.context_manager.current_context(self.session))

    def test_conversation_manager_integrates_context(self) -> None:
        self.tasks.project_manager.create_project("Conversation Project")
        core = JarvisCore()
        core.initialize()
        manager = ConversationManager(
            jarvis_core=core,
            memory_manager=self.memory,
            task_intelligence_manager=self.tasks,
            workflow_manager=self.workflows,
            retrieval_manager=self.retrieval,
            research_manager=self.research,
            personal_intelligence_manager=self.personal,
            context_intelligence_manager=self.context_manager,
        )
        manager.initialize()
        manager.handle_input("Continue the Conversation Project.")
        response = manager.handle_input("What were we doing?")
        self.assertIn("Conversation Project", response.response)

    def test_selective_context_delivery(self) -> None:
        self.tasks.project_manager.create_project("Selective Project")
        self.context_manager.prepare_request("Continue the Selective Project.", self.session)
        resolution = self.context_manager.prepare_request("What time is it in the system status view?", self.session)
        self.assertEqual(resolution.status, "none")

    def test_startup_and_health_include_context_intelligence(self) -> None:
        startup = StartupManager()
        startup.start()
        try:
            self.assertIsNotNone(startup.context_intelligence_manager)
            self.assertTrue(startup.context_intelligence_manager.initialized)
            self.assertTrue(any(result.name == "context_intelligence" for result in startup.health_results))
            checker = HealthChecker(
                settings=startup.settings,
                required_directories=startup.required_directories(startup.settings),
                module_checks={
                    "context_intelligence": lambda: True,
                    "conversation_context": lambda: True,
                    "context_retrieval": lambda: True,
                    "reference_resolution": lambda: True,
                    "continuation_readiness": lambda: True,
                },
            )
            health = checker.check_module("context_intelligence", "Context Intelligence")
            self.assertEqual(health.message, "Context Intelligence initialized.")
        finally:
            startup.shutdown()


if __name__ == "__main__":
    unittest.main()
