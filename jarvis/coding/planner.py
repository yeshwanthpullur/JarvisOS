"""Deterministic, bounded coding planner."""

from __future__ import annotations

from dataclasses import dataclass

from .models import CodingIntent, CodingPlan, CodingStatus, CodingTask
from .safety import evaluate_coding_safety, redact_secret_shaped


_INTENTS: tuple[tuple[CodingIntent, tuple[str, ...]], ...] = (
    (CodingIntent.REVIEW_DIFF, ("review diff", "explain diff", "current diff")),
    (CodingIntent.INSPECT_REPO, ("inspect repo", "review repo", "repository status", "repo status")),
    (CodingIntent.TEST_PLAN, ("test plan", "tests for", "testing strategy")),
    (CodingIntent.BUG_TRIAGE, ("bug", "debug", "broken", "failure", "error")),
    (CodingIntent.REFACTOR_PLAN, ("refactor", "restructure", "clean up code")),
    (CodingIntent.DOCUMENTATION_UPDATE, ("documentation", "readme", "docs")),
    (CodingIntent.DEPENDENCY_REVIEW, ("dependency", "dependencies", "package", "requirements")),
    (CodingIntent.RELEASE_REVIEW, ("release", "tag", "prerelease")),
    (CodingIntent.EXPLAIN_CODE, ("explain code", "how does this code", "understand code")),
    (CodingIntent.PLAN_CHANGE, ("add ", "implement", "change", "fix", "integration")),
)


def classify_coding_intent(request: str) -> CodingIntent:
    lowered = " ".join(request.lower().split())
    for intent, terms in _INTENTS:
        if any(term in lowered for term in terms):
            return intent
    return CodingIntent.UNKNOWN


@dataclass(slots=True)
class CodingPlanner:
    max_steps: int = 6
    max_files: int = 20

    def __post_init__(self) -> None:
        self.max_steps = max(1, min(int(self.max_steps), 12))
        self.max_files = max(1, min(int(self.max_files), 50))

    def create_task(self, request: str) -> CodingTask:
        normalized = " ".join(redact_secret_shaped(request).strip().split())
        safety = evaluate_coding_safety(request)
        return CodingTask(request=normalized, normalized_request=normalized, intent=classify_coding_intent(normalized), risk_level=safety.risk_level)

    def create_plan(self, request: str) -> tuple[CodingTask, CodingPlan]:
        task = self.create_task(request)
        safety = evaluate_coding_safety(request)
        if not safety.allowed:
            return task, CodingPlan(task.task_id, task.intent, "The requested coding action is blocked by policy.", ("Do not access secrets or perform destructive repository operations.",), risk_level=safety.risk_level, approval_required=True, status=CodingStatus.BLOCKED, warnings=(safety.reason,))
        likely_files = self._likely_files(task.normalized_request)
        status = CodingStatus.NEEDS_APPROVAL if safety.approval_required else CodingStatus.NEEDS_CLARIFICATION if task.intent is CodingIntent.UNKNOWN else CodingStatus.PLANNED
        steps = self._steps(task.intent, task.normalized_request)[: self.max_steps]
        tests = self._tests(task.intent)
        warnings = (safety.reason, "No files, commands, commits, pushes, or deployments will be performed.")
        return task, CodingPlan(task.task_id, task.intent, f"Plan-only coding support for {task.intent.value}.", steps, likely_files[: self.max_files], tests, safety.risk_level, safety.approval_required, status, warnings)

    def _likely_files(self, request: str) -> tuple[str, ...]:
        lowered = request.lower()
        if "telegram" in lowered:
            return ("jarvis/skills/", "jarvis/agents/", "config/", "commands/", "tests/", "docs/")
        if "document" in lowered or "docs" in lowered:
            return ("docs/", "README.md", "CHANGELOG.md", "tests/")
        if "provider" in lowered or "model" in lowered:
            return ("jarvis/models/", "config/", "tests/", "docs/")
        return ("affected subsystem", "tests/", "docs/")

    def _steps(self, intent: CodingIntent, request: str) -> tuple[str, ...]:
        common = ("Confirm repository state and authoritative subsystem boundaries.", "Inspect the smallest relevant implementation surface.")
        if "telegram" in request.lower():
            return common + (
                "Define a disabled-by-default communication connector through the existing skill architecture.",
                "Define token handling without reading or changing local secrets.",
                "Require explicit approval before any message is sent.",
                "Add mocked routing, permission, safety, and documentation tests.",
            )
        specific = {
            CodingIntent.REVIEW_DIFF: ("Review bounded diff metadata and identify risk areas.", "Recommend focused and regression tests."),
            CodingIntent.INSPECT_REPO: ("Summarize branch, HEAD, and bounded working-tree metadata.",),
            CodingIntent.TEST_PLAN: ("Map behavior to focused tests and cross-subsystem regressions.",),
            CodingIntent.BUG_TRIAGE: ("Reproduce safely and isolate the failure path.", "Propose the smallest correction and regression coverage."),
            CodingIntent.REFACTOR_PLAN: ("Identify ownership boundaries and compatibility risks.", "Plan incremental behavior-preserving changes."),
            CodingIntent.DEPENDENCY_REVIEW: ("Review necessity, local-first compatibility, licensing, and supply-chain risk.",),
            CodingIntent.RELEASE_REVIEW: ("Verify commit, tests, tracking, and artifact cleanliness before release actions.",),
        }.get(intent, ("Define acceptance criteria and propose a minimal implementation sequence.",))
        return common + specific + ("Require explicit approval before any write or command execution.",)

    def _tests(self, intent: CodingIntent) -> tuple[str, ...]:
        focused = f"Add focused tests for {intent.value}."
        return (focused, "Run Python compilation and relevant integration tests.", "Run the full suite and git diff --check before commit.")
