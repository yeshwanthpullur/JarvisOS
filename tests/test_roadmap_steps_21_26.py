from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest

from jarvis.workers.assurance import (
    EvidenceStore,
    IntegrationCandidateGate,
    ReworkEngine,
    ReviewCoordinator,
    VerificationEngine,
    evidence_integrity,
)
from jarvis.workers.assurance_models import (
    CandidateCheck,
    CandidateStatus,
    EvidenceRecord,
    EvidenceType,
    FailureRecord,
    IntegrationCandidate,
    RecoveryAction,
    ReworkDisposition,
    ReviewFinding,
    ReviewSeverity,
    ReviewVerdict,
    StructuredReview,
    VerificationState,
    WorkCheckpoint,
)
from jarvis.workers.checkpoints import CheckpointStore, RecoveryPlanner
from jarvis.workers.models import WorkerCapabilities, WorkerRecord, WorkerStatus, WorkerTaskStatus
from jarvis.workers.registry import WorkerRegistry


def checkpoint(**changes: object) -> WorkCheckpoint:
    values: dict[str, object] = {
        "goal_id": "goal-1",
        "project_id": "project-1",
        "task_id": "task-1",
        "run_id": "run-1",
        "worker_id": "worker-1",
        "status": WorkerTaskStatus.RUNNING,
        "pending_stage": "implementation",
    }
    values.update(changes)
    return WorkCheckpoint(**values)


def evidence(task_id: str = "task-1", *, validated: bool = True, stale: bool = False) -> EvidenceRecord:
    summary = "Targeted tests passed."
    reference = "tests:focused"
    return EvidenceRecord(
        task_id,
        "run-1",
        EvidenceType.TEST_RESULT,
        "pytest",
        summary,
        reference,
        validated=validated,
        stale=stale,
        integrity=evidence_integrity(summary, reference),
    )


class CheckpointRecoveryTests(unittest.TestCase):
    def test_clean_completion_is_not_replayed(self) -> None:
        decision = RecoveryPlanner().classify(checkpoint(status=WorkerTaskStatus.COMPLETED))
        self.assertEqual(decision.action, RecoveryAction.NEEDS_REVIEW)
        self.assertFalse(decision.safe_to_resume)

    def test_interrupted_task_resumes_at_pending_stage(self) -> None:
        failure = FailureRecord("task-1", "run-1", "interrupted", "verification", True, "interrupted")
        current = checkpoint(failure=failure, completed_stages=("implementation",), pending_stage="verification")
        resumed = RecoveryPlanner().resume(current)
        self.assertEqual(resumed.pending_stage, "verification")
        self.assertEqual(resumed.completed_stages, ("implementation",))
        self.assertEqual(resumed.retry_count, 1)
        self.assertEqual(len(resumed.failure_history), 1)

    def test_worker_crash_uses_different_worker_retry(self) -> None:
        failure = FailureRecord("task-1", "run-1", "worker_crash", "implementation", True, "worker exited")
        self.assertEqual(RecoveryPlanner().classify(checkpoint(failure=failure)).action, RecoveryAction.RETRY_DIFFERENT_WORKER)

    def test_provider_failure_reroutes(self) -> None:
        failure = FailureRecord("task-1", "run-1", "provider_failure", "planning", True, "provider unavailable")
        self.assertEqual(RecoveryPlanner().classify(checkpoint(failure=failure)).action, RecoveryAction.REROUTE_PROVIDER)

    def test_timeout_safely_resumes(self) -> None:
        failure = FailureRecord("task-1", "run-1", "timeout", "tests", True, "bounded timeout")
        self.assertEqual(RecoveryPlanner().classify(checkpoint(failure=failure)).action, RecoveryAction.SAFE_RESUME)

    def test_checkpoint_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoints.json"
            original = checkpoint(context_refs=("context:1",), resume_reference="stage:implementation")
            CheckpointStore(path).save(original)
            restored = CheckpointStore(path).latest("task-1")
            self.assertEqual(restored, original)

    def test_duplicate_side_effect_is_not_repeated(self) -> None:
        store = CheckpointStore()
        self.assertTrue(store.record_side_effect("message:123", "evidence:1"))
        self.assertFalse(store.record_side_effect("message:123", "evidence:2"))
        self.assertTrue(store.side_effect_completed("message:123"))

    def test_retry_exhaustion_is_irrecoverable(self) -> None:
        failure = FailureRecord("task-1", "run-1", "timeout", "tests", True, "timeout")
        decision = RecoveryPlanner().classify(checkpoint(failure=failure, retry_count=2))
        self.assertEqual(decision.action, RecoveryAction.IRRECOVERABLE)

    def test_corrupt_checkpoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoints.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid_checkpoint_store"):
                CheckpointStore(path)

    def test_secret_payload_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsafe_checkpoint_payload"):
            CheckpointStore().save(checkpoint(context_refs=("api_key=do-not-store",)))

    def test_stale_run_detection(self) -> None:
        old = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        store = CheckpointStore()
        store.save(checkpoint(updated_at=old, timeout_seconds=5))
        self.assertEqual(len(store.stale()), 1)


class ReviewAndReworkTests(unittest.TestCase):
    def setUp(self) -> None:
        capabilities = WorkerCapabilities(independent_review=True)
        first = WorkerRecord("author", "Author", "test", (), status=WorkerStatus.DEGRADED, detected=True, capabilities=capabilities)
        second = WorkerRecord("reviewer", "Reviewer", "test", (), status=WorkerStatus.DEGRADED, detected=True, capabilities=capabilities)
        self.registry = WorkerRegistry()
        self.registry._records = {"author": first, "reviewer": second}

    def test_independent_reviewer_is_selected_and_self_review_avoided(self) -> None:
        reviewer, independent = ReviewCoordinator(self.registry).select_reviewer("author")
        self.assertEqual(reviewer, "reviewer")
        self.assertTrue(independent)

    def test_controlled_same_worker_fallback_is_degraded(self) -> None:
        self.registry._records.pop("reviewer")
        reviewer, independent = ReviewCoordinator(self.registry).select_reviewer("author")
        self.assertEqual(reviewer, "author")
        self.assertFalse(independent)

    def test_high_severity_finding_blocks_pass(self) -> None:
        finding = ReviewFinding("security", ReviewSeverity.HIGH, "Unsafe boundary.")
        with self.assertRaises(ValueError):
            StructuredReview("task-1", "reviewer", "security", ReviewVerdict.PASS, (finding,))

    def test_notes_do_not_fail_review_and_untrusted_metadata_is_retained(self) -> None:
        finding = ReviewFinding("style", ReviewSeverity.NOTE, "Minor note.")
        review = StructuredReview("task-1", "reviewer", "correctness", ReviewVerdict.PASS_WITH_NOTES, (finding,), trusted=False)
        self.assertTrue(ReviewCoordinator.validate(review))
        self.assertFalse(review.trusted)

    def test_malformed_review_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            StructuredReview("", "reviewer", "correctness", ReviewVerdict.PASS)

    def test_evidence_based_rework_and_corrected_completion(self) -> None:
        finding = ReviewFinding("correctness", ReviewSeverity.MEDIUM, "Test failed.", "Correct parser edge case.")
        review = StructuredReview("task-1", "reviewer", "correctness", ReviewVerdict.REWORK_REQUIRED, (finding,))
        engine = ReworkEngine(max_attempts=2)
        request = engine.request("task-1", review, 1)
        self.assertIn("Correct parser", request.instructions[0])
        self.assertEqual(engine.finish(request, ("evidence:fixed",), passed=True).disposition, ReworkDisposition.COMPLETED)

    def test_repeated_failure_exhausts_budget(self) -> None:
        finding = ReviewFinding("correctness", ReviewSeverity.MEDIUM, "Still failing.")
        review = StructuredReview("task-1", "reviewer", "correctness", ReviewVerdict.REWORK_REQUIRED, (finding,))
        engine = ReworkEngine(max_attempts=2)
        request = engine.request("task-1", review, 2)
        self.assertEqual(engine.finish(request, (), passed=False).disposition, ReworkDisposition.RETRY_EXHAUSTED)
        with self.assertRaisesRegex(ValueError, "rework_budget_exhausted"):
            engine.request("task-1", review, 3)

    def test_security_rejection_is_not_retried(self) -> None:
        finding = ReviewFinding("security", ReviewSeverity.CRITICAL, "Secret exposure.")
        review = StructuredReview("task-1", "reviewer", "security", ReviewVerdict.SECURITY_REJECTED, (finding,))
        request = ReworkEngine().request("task-1", review, 1)
        self.assertTrue(request.security_blocked)


class VerificationEvidenceCandidateTests(unittest.TestCase):
    def test_worker_claim_without_test_evidence_is_not_complete(self) -> None:
        plan = VerificationEngine().plan("task-1", "coding")
        attempted = replace(plan, checks=tuple(replace(item, state=VerificationState.PASSED) for item in plan.checks))
        result = VerificationEngine.evaluate(attempted, EvidenceStore())
        self.assertFalse(result.completion_allowed)

    def test_valid_evidence_satisfies_required_checks(self) -> None:
        store = EvidenceStore()
        item = store.add(evidence())
        plan = VerificationEngine().plan("task-1", "coding")
        completed = replace(plan, checks=tuple(replace(check, state=VerificationState.PASSED, evidence_refs=(item.evidence_id,)) for check in plan.checks))
        self.assertTrue(VerificationEngine.evaluate(completed, store).completion_allowed)

    def test_unknown_or_stale_evidence_is_rejected(self) -> None:
        store = EvidenceStore()
        item = store.add(evidence())
        store.invalidate(item.evidence_id)
        plan = VerificationEngine().plan("task-1", "other")
        completed = replace(plan, checks=(replace(plan.checks[0], state=VerificationState.PASSED, evidence_refs=(item.evidence_id, "forged")),))
        self.assertFalse(VerificationEngine.evaluate(completed, store).completion_allowed)

    def test_evidence_survives_reload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            item = EvidenceStore(path).add(evidence())
            self.assertEqual(EvidenceStore(path).get(item.evidence_id), item)

    def test_passing_candidate_becomes_ready_and_never_auto_merges(self) -> None:
        candidate = IntegrationCandidate("task-1", "task/one", "workspace:one", (), (CandidateCheck("tests", True), CandidateCheck("review", True)))
        result = IntegrationCandidateGate.evaluate(candidate, changed_files=("jarvis/module.py",))
        self.assertEqual(result.status, CandidateStatus.READY)
        self.assertFalse(result.automatic_merge)

    def test_failed_check_and_protected_file_block_candidate(self) -> None:
        candidate = IntegrationCandidate("task-1", "task/one", "workspace:one", (), (CandidateCheck("tests", False),))
        result = IntegrationCandidateGate.evaluate(candidate, changed_files=(".env",))
        self.assertEqual(result.status, CandidateStatus.REJECTED)

    def test_stale_candidate_is_detected(self) -> None:
        candidate = IntegrationCandidate("task-1", "task/one", "workspace:one", (), (CandidateCheck("tests", True),))
        self.assertEqual(IntegrationCandidateGate.evaluate(candidate, changed_files=(), stale_base=True).status, CandidateStatus.STALE)

    def test_env_example_is_not_treated_as_protected_env(self) -> None:
        candidate = IntegrationCandidate("task-1", "task/one", "workspace:one", (), (CandidateCheck("tests", True),))
        self.assertEqual(IntegrationCandidateGate.evaluate(candidate, changed_files=(".env.example",)).status, CandidateStatus.READY)

    def test_malformed_evidence_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceRecord("", "run", EvidenceType.TEST_RESULT, "pytest", "passed", "tests")


if __name__ == "__main__":
    unittest.main()
