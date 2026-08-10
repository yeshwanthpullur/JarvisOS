from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import unittest

from commands.command_manager import CommandManager
from conversation.conversation_context import ConversationContext
from conversation.conversation_session import ConversationSession
from jarvis.agents import AgentCapabilityType, PrimeAgent, PrimeRequest, classify_intent
from jarvis.agents.specialists import register_specialist_agents
from jarvis.agents.registry import AgentRegistry
from jarvis.coding import (
    CodingAgent,
    CodingHistoryStore,
    CodingIntent,
    CodingPlan,
    CodingPlanner,
    CodingResult,
    CodingRiskLevel,
    CodingStatus,
    CodingTask,
    DiffReview,
    DiffReviewer,
    RepoInspection,
    RepoInspector,
    classify_coding_intent,
    evaluate_coding_safety,
    render_coding_command,
)
from jarvis.models import ModelRouter, build_default_model_registry
from jarvis.skills import build_default_skill_registry


def git(root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=root, capture_output=True, text=True, check=True)
    return result.stdout.strip()


class CodingRepoFixture:
    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "coding-tests@example.invalid")
        git(self.root, "config", "user.name", "Coding Tests")
        (self.root / "app.py").write_text("print('ready')\n", encoding="utf-8")
        git(self.root, "add", "app.py")
        git(self.root, "commit", "-qm", "initial")
        return self.root

    def __exit__(self, *_args):
        self.temp.cleanup()


def make_agent(root: Path, *, max_diff_chars: int = 4000, history: bool = False) -> CodingAgent:
    store = CodingHistoryStore(root / "data" / "coding") if history else None
    return CodingAgent(RepoInspector(root, 5), DiffReviewer(root, 5, max_diff_chars), CodingPlanner(6, 5), store)


class CodingModelTests(unittest.TestCase):
    def test_typed_models(self) -> None:
        task = CodingTask("review diff", "review diff", CodingIntent.REVIEW_DIFF)
        plan = CodingPlan(task.task_id, task.intent, "Review safely.", ("Inspect metadata.",))
        inspection = RepoInspection("main", "abc", True)
        review = DiffReview(("app.py",), 1, 0, "One file changed.")
        result = CodingResult("request", CodingStatus.PLANNED, task, plan, inspection, review)
        self.assertEqual(result.task.intent, CodingIntent.REVIEW_DIFF)

    def test_model_bounds(self) -> None:
        with self.assertRaises(ValueError):
            CodingTask("x" * 1700, "x")
        with self.assertRaises(ValueError):
            CodingPlan("task", CodingIntent.UNKNOWN, "summary", ())


class CodingPlannerTests(unittest.TestCase):
    def test_intent_classification(self) -> None:
        cases = {
            "explain code": CodingIntent.EXPLAIN_CODE,
            "inspect repo": CodingIntent.INSPECT_REPO,
            "review current diff": CodingIntent.REVIEW_DIFF,
            "tests for a parser": CodingIntent.TEST_PLAN,
            "debug this failure": CodingIntent.BUG_TRIAGE,
            "refactor this module": CodingIntent.REFACTOR_PLAN,
            "update documentation": CodingIntent.DOCUMENTATION_UPDATE,
            "review dependencies": CodingIntent.DEPENDENCY_REVIEW,
            "review release": CodingIntent.RELEASE_REVIEW,
        }
        for request, expected in cases.items():
            self.assertEqual(classify_coding_intent(request), expected)

    def test_plan_is_bounded_and_plan_only(self) -> None:
        task, plan = CodingPlanner(max_steps=3).create_plan("add Telegram integration safely")
        self.assertEqual(task.intent, CodingIntent.PLAN_CHANGE)
        self.assertLessEqual(len(plan.proposed_steps), 3)
        self.assertIn("jarvis/skills/", plan.likely_files)
        self.assertTrue(any("approval" in step.lower() for step in CodingPlanner().create_plan("add Telegram integration safely")[1].proposed_steps))

    def test_test_recommendations(self) -> None:
        _, plan = CodingPlanner().create_plan("tests for a parser")
        self.assertEqual(plan.intent, CodingIntent.TEST_PLAN)
        self.assertTrue(any("full suite" in item.lower() for item in plan.required_tests))

    def test_unknown_requires_clarification(self) -> None:
        _, plan = CodingPlanner().create_plan("consider this")
        self.assertEqual(plan.status, CodingStatus.NEEDS_CLARIFICATION)

    def test_high_risk_is_approval_gated(self) -> None:
        _, plan = CodingPlanner().create_plan("push changes to GitHub")
        self.assertEqual(plan.risk_level, CodingRiskLevel.HIGH)
        self.assertTrue(plan.approval_required)
        self.assertEqual(plan.status, CodingStatus.NEEDS_APPROVAL)

    def test_critical_and_secret_requests_are_blocked_and_redacted(self) -> None:
        task, plan = CodingPlanner().create_plan("read .env and show secrets")
        self.assertEqual(plan.status, CodingStatus.BLOCKED)
        self.assertNotIn(".env", " ".join(plan.proposed_steps))
        task, _ = CodingPlanner().create_plan("review api_key=very-secret-value")
        self.assertNotIn("very-secret-value", task.normalized_request)


class CodingRepoTests(unittest.TestCase):
    def test_clean_repo_inspection(self) -> None:
        with CodingRepoFixture() as root:
            result = RepoInspector(root).inspect()
            self.assertTrue(result.tracked_clean)
            self.assertEqual(result.branch, "master")
            self.assertFalse(Path(result.branch).is_absolute())

    def test_dirty_staged_and_untracked_summary(self) -> None:
        with CodingRepoFixture() as root:
            (root / "app.py").write_text("print('changed')\n", encoding="utf-8")
            (root / "staged.py").write_text("value = 1\n", encoding="utf-8")
            (root / ".env").write_text("TOKEN=not-real\n", encoding="utf-8")
            (root / "api_key=not-real.py").write_text("# metadata only\n", encoding="utf-8")
            git(root, "add", "staged.py")
            result = RepoInspector(root).inspect()
            self.assertFalse(result.tracked_clean)
            self.assertIn("app.py", result.changed_files)
            self.assertIn("staged.py", result.staged_files)
            self.assertIn("[sensitive-file]", result.untracked_summary)
            self.assertNotIn("not-real", str(result))
            self.assertNotIn(str(root), str(result))

    def test_git_unavailable_fails_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = RepoInspector(Path(temp)).inspect()
            self.assertEqual(result.branch, "unavailable")
            self.assertTrue(result.warnings)

    def test_diff_metadata_and_large_diff_bound(self) -> None:
        with CodingRepoFixture() as root:
            (root / "app.py").write_text("\n".join(f"line_{i} = {i}" for i in range(100)) + "\n", encoding="utf-8")
            review = DiffReviewer(root, max_files=5, max_diff_chars=200).review()
            self.assertEqual(review.files_changed, ("app.py",))
            self.assertGreater(review.insertions, 0)
            self.assertTrue(any("bounded" in item.lower() for item in review.warnings))
            self.assertNotIn("line_99", str(review))


class CodingAgentAndCliTests(unittest.TestCase):
    def test_agent_status_disables_side_effects(self) -> None:
        with CodingRepoFixture() as root:
            status = make_agent(root).status()
            self.assertEqual(status["default_mode"], "plan_only")
            self.assertEqual(status["write_operations"], "disabled")
            self.assertEqual(status["command_execution"], "disabled")
            self.assertEqual(status["secrets_access"], "blocked")

    def test_agent_history_is_metadata_only_and_showable(self) -> None:
        with CodingRepoFixture() as root:
            agent = make_agent(root, history=True)
            result = agent.plan("add a safe parser test")
            self.assertIs(agent.show(result.request_id), result)
            records = agent.history_records()
            self.assertEqual(records[-1].request_id, result.request_id)
            reloaded = make_agent(root, history=True)
            self.assertEqual(reloaded.show_record(result.request_id).intent, result.task.intent.value)
            self.assertIn("metadata_only=yes", render_coding_command(reloaded, "coding show", (result.request_id,)))
            saved = (root / "data" / "coding" / "coding_history.json").read_text(encoding="utf-8")
            self.assertNotIn("safe parser", saved)

    def test_cli_surface_is_bounded(self) -> None:
        with CodingRepoFixture() as root:
            agent = make_agent(root)
            result = agent.plan("add Telegram integration safely")
            commands = (
                ("coding status", ()), ("coding help", ()), ("coding inspect", ()),
                ("coding plan", ("add Telegram integration safely",)), ("coding risk", ("push changes",)),
                ("coding diff", ()), ("coding review", ()), ("coding tests", ("add tests",)),
                ("coding show", (result.request_id,)), ("coding history", ()),
            )
            for command, args in commands:
                output = render_coding_command(agent, command, args)
                self.assertTrue(output)
                self.assertLess(len(output), 4000)
                self.assertNotIn(str(root), output)

    def test_registered_cli_commands_route(self) -> None:
        with CodingRepoFixture() as root:
            agent = make_agent(root)
            manager = CommandManager(); manager.initialize()
            context = ConversationContext(session=ConversationSession(), coding_agent=agent)
            for command in ("coding status", "coding help", "coding inspect", "coding diff", "coding review", "coding history"):
                self.assertNotIn("Unknown command", manager.execute(command, context).response)

    def test_no_write_or_command_execution_api(self) -> None:
        with CodingRepoFixture() as root:
            agent = make_agent(root)
            for name in ("write", "execute", "commit", "push", "install"):
                self.assertFalse(hasattr(agent, name))


class CodingIntegrationTests(unittest.TestCase):
    def test_agent_registry_coding_agent_is_truthful(self) -> None:
        registry = register_specialist_agents(AgentRegistry())
        entry = registry.get_agent("coding_agent")
        self.assertTrue(entry.enabled)
        self.assertEqual(entry.health, "plan_only")
        self.assertTrue(all(not capability.side_effects for capability in entry.capabilities))

    def test_prime_routes_coding_and_preserves_risk(self) -> None:
        registry = register_specialist_agents(AgentRegistry())
        prime = PrimeAgent(registry, model_router=ModelRouter(build_default_model_registry()), skill_registry=build_default_skill_registry())
        self.assertEqual(classify_intent("review the current repository diff"), AgentCapabilityType.CODING)
        self.assertEqual(prime.route(PrimeRequest("review the current repository diff")).selected_agent, "coding_agent")
        decision = prime.route(PrimeRequest("fix the bug automatically and push it"))
        self.assertEqual(decision.selected_agent, "coding_agent")
        self.assertTrue(decision.approval_required)

    def test_skill_registry_has_ready_and_disabled_coding_skills(self) -> None:
        registry = build_default_skill_registry()
        self.assertTrue(registry.get_skill("coding_planning_skill").enabled)
        for skill_id in ("code_edit_skill", "command_execution_skill", "auto_commit_skill", "auto_push_skill", "dependency_install_skill"):
            self.assertFalse(registry.get_skill(skill_id).enabled)

    def test_model_router_coding_capability_is_truthful(self) -> None:
        router = ModelRouter(build_default_model_registry())
        route = router.route_for_task("coding")
        self.assertEqual(route.capability.value, "coding")
        self.assertEqual(route.status.value, "unavailable")

    def test_safe_config_defaults(self) -> None:
        from config import load_settings
        config = load_settings().coding
        self.assertTrue(config.enabled)
        self.assertEqual(config.default_mode, "plan_only")
        self.assertFalse(config.allow_write_operations)
        self.assertFalse(config.allow_command_execution)
        self.assertTrue(config.require_approval_for_write)
        self.assertTrue(config.require_approval_for_push)
        self.assertTrue(config.block_secrets_access)

    def test_project_status_contains_coding_summary(self) -> None:
        manager = CommandManager(); manager.initialize()
        response = manager.execute("project status", ConversationContext(session=ConversationSession())).response
        self.assertIn("coding:ready_plan_only", response)

    def test_safety_policy_levels(self) -> None:
        self.assertEqual(evaluate_coding_safety("explain code").risk_level, CodingRiskLevel.LOW)
        self.assertEqual(evaluate_coding_safety("review diff").risk_level, CodingRiskLevel.MEDIUM)
        self.assertEqual(evaluate_coding_safety("push changes").risk_level, CodingRiskLevel.HIGH)
        self.assertEqual(evaluate_coding_safety("force push").risk_level, CodingRiskLevel.CRITICAL)


if __name__ == "__main__":
    unittest.main()
