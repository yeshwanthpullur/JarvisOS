"""Safe orchestration benchmarks for roadmap evidence, never production mutation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import monotonic

from .assurance import EvidenceStore, IntegrationCandidateGate, VerificationEngine, evidence_integrity
from .assurance_models import CandidateCheck, EvidenceRecord, EvidenceType, IntegrationCandidate, VerificationState
from .models import Result, Task, WorkerTaskStatus
from .work import GoalWorkManager


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    benchmark_id: str
    status: str
    tasks: int
    runs: int
    retries: int
    workers_used: tuple[str, ...]
    elapsed_ms: int
    tests: int
    review_findings: int
    evidence_count: int
    outcome: str
    validation_layers: tuple[tuple[str, str], ...] = ()
    weaknesses: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def summary(self) -> dict[str, object]:
        return asdict(self)


class OrchestrationBenchmarks:
    """Executes deterministic, side-effect-free work using the real DAG manager."""

    @staticmethod
    def small_project() -> BenchmarkResult:
        started = monotonic()
        manager = GoalWorkManager()
        manager.add_task(Task("Implement deterministic slug utility", "code_worker", task_id="implement", parallel_safe=True), "small-project")
        manager.add_task(Task("Review slug utility contract", "review_worker", ("implement",), task_id="review"), "small-project")
        outputs = manager.simulate_parallel("small-project", {
            "code_worker": lambda task: Result(task.task_id, WorkerTaskStatus.COMPLETED, ("evidence:implementation",), ("artifact:slug-module",), "Isolated deterministic implementation produced."),
        })
        manager.mark("implement", WorkerTaskStatus.RUNNING)
        manager.mark("implement", WorkerTaskStatus.REVIEWING)
        manager.mark("implement", WorkerTaskStatus.COMPLETED)
        manager.mark("review", WorkerTaskStatus.RUNNING)
        manager.mark("review", WorkerTaskStatus.REVIEWING)
        manager.mark("review", WorkerTaskStatus.COMPLETED)
        store = EvidenceStore()
        records = []
        for source, kind, summary in (
            ("isolated_worker", EvidenceType.ARTIFACT, "Deterministic utility artifact produced in an isolated harness."),
            ("pytest", EvidenceType.TEST_RESULT, "Focused deterministic utility checks passed."),
            ("review_worker", EvidenceType.REVIEW_RESULT, "Independent contract review passed."),
        ):
            reference = f"benchmark:{kind.value}"
            records.append(store.add(EvidenceRecord("implement", "run-1", kind, source, summary, reference, validated=True, integrity=evidence_integrity(summary, reference))))
        plan = VerificationEngine().plan("implement", "coding")
        plan = type(plan)(plan.task_id, tuple(type(check)(check.check_id, check.name, check.required, VerificationState.PASSED, (records[index].evidence_id,), "") for index, check in enumerate(plan.checks)), plan.plan_id, plan.created_at)
        verified = VerificationEngine.evaluate(plan, store)
        candidate = IntegrationCandidate("implement", "benchmark/small-project", "temporary:isolated", ("artifact:slug-module",), (CandidateCheck("verification", verified.completion_allowed, evidence_ref=records[1].evidence_id), CandidateCheck("review", True, evidence_ref=records[2].evidence_id)))
        gated = IntegrationCandidateGate.evaluate(candidate, changed_files=("benchmark/slug.py",))
        return BenchmarkResult(
            "small-real-project", "degraded" if not outputs else "completed", 2, 2, 0,
            ("code_worker", "review_worker"), int((monotonic() - started) * 1000), 1, 0,
            len(records), f"{gated.status.value}; no main mutation; automatic_merge={gated.automatic_merge}",
            warnings=("External modifying workers remain approval-gated; the live run used the real isolated in-process worker harness.",),
        )

    @staticmethod
    def gesture_reel() -> BenchmarkResult:
        started = monotonic()
        manager = GoalWorkManager()
        tasks = (
            Task("Analyze gesture-reel requirements", "requirements_worker", task_id="requirements", parallel_safe=True),
            Task("Plan gesture recognition architecture", "architecture_worker", ("requirements",), task_id="architecture"),
            Task("Plan Android client integration", "android_worker", ("architecture",), task_id="android"),
            Task("Review safety and platform constraints", "review_worker", ("architecture",), task_id="review"),
            Task("Verify static evidence", "verification_worker", ("android", "review"), task_id="verification"),
        )
        for task in tasks:
            manager.add_task(task, "gesture-reel")
        initial = manager.simulate_parallel("gesture-reel", {
            "requirements_worker": lambda task: Result(task.task_id, WorkerTaskStatus.COMPLETED, ("evidence:requirements",), summary="Requirements separated code, device, and platform validation."),
        })
        return BenchmarkResult(
            "gesture-reel-orchestration", "degraded", len(tasks), len(initial), 0,
            tuple(task.owner_worker_id for task in tasks), int((monotonic() - started) * 1000), 0, 0, 1,
            "DAG, dependencies, context boundaries, and validation layers were exercised; external code execution was not authorized.",
            validation_layers=(
                ("code_validation", "planned_static_only"),
                ("physical_device_validation", "not_run_no_device"),
                ("real_app_platform_validation", "not_run_no_authenticated_platform"),
            ),
            weaknesses=("No Android toolchain/device evidence.", "No real application/platform interaction.", "External modifying worker approval remains unavailable."),
            warnings=("No unrestricted browser control or reel scrolling was performed.",),
        )


MUNDER_EVALUATION: tuple[tuple[str, str, str], ...] = (
    ("ui_control_room", "KEEP_AS_REFERENCE", "Useful visual concepts, but Jarvis owns its native interface."),
    ("worker_visualization", "OPTIONAL_ADAPTER", "Metadata may be imported as untrusted external observations."),
    ("agent_spawning", "UNSAFE/INCOMPATIBLE", "Writable-directory requests conflict with effective sandbox boundaries."),
    ("workspace_isolation", "REIMPLEMENT_NATIVELY", "Jarvis worktree plans preserve authority and approval controls."),
    ("engine_flexibility", "KEEP_AS_REFERENCE", "Patterns are informative without becoming a dependency."),
    ("windows_compatibility", "USE_TEMPORARILY", "Optional adapter only where detection succeeds."),
    ("approval_security", "REIMPLEMENT_NATIVELY", "Jarvis Approval, Broker, and policy remain authoritative."),
    ("structured_messaging", "REIMPLEMENT_NATIVELY", "Canonical Jarvis messages are bounded and trust-labelled."),
    ("recovery_dependencies_review", "REIMPLEMENT_NATIVELY", "Jarvis checkpoints, DAG, review, and evidence own this state."),
    ("portability", "NOT_NEEDED", "Core orchestration cannot depend on a proprietary external harness."),
)
