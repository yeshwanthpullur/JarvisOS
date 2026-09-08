from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jarvis.backup import BackupManager
from jarvis.models import (
    ModelCapability,
    ModelProvider,
    ModelProviderRegistry,
    ModelProviderStatus,
    ModelProviderType,
    PrivacyMode,
    PrivacyPolicy,
)
from jarvis.models.router import ModelRouter


class EngineeringSteps64To94Tests(unittest.TestCase):
    def test_backup_round_trip_is_integrity_checked_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "state.json"
            restored = root / "restored.json"
            source.write_text('{"state":"bounded"}', encoding="utf-8")
            manager = BackupManager(root / "backups")
            record = manager.create(source, backup_id="step-77")
            self.assertTrue(record.verified)
            self.assertTrue(manager.verify("step-77").verified)
            manager.restore("step-77", restored)
            self.assertEqual(restored.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

    def test_backup_rejects_secret_shaped_files(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / ".env"
            source.write_text("TOKEN=do-not-read", encoding="utf-8")
            with self.assertRaises(ValueError):
                BackupManager(Path(folder) / "backups").create(source)

    def test_privacy_policy_rejects_remote_provider_in_local_mode(self) -> None:
        provider = ModelProvider(
            "remote", ModelProviderType.OPENAI_COMPATIBLE, "Remote", ModelProviderStatus.READY,
            (ModelCapability.CHAT,), local=False, enabled=True,
        )
        decision = PrivacyPolicy(PrivacyMode.LOCAL_ONLY, allow_cloud_providers=True).evaluate(provider)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "local_only_rejects_remote_provider")

    def test_router_preserves_explicit_privacy_policy_and_health(self) -> None:
        remote = ModelProvider(
            "remote", ModelProviderType.OPENAI_COMPATIBLE, "Remote", ModelProviderStatus.READY,
            (ModelCapability.CHAT,), local=False, enabled=True,
        )
        registry = ModelProviderRegistry((remote,))
        router = ModelRouter(registry, local_only_default=False, allow_cloud_providers=True, privacy_mode=PrivacyMode.NORMAL_HYBRID)
        route = router.route_for_task("conversation", privacy_mode=PrivacyMode.LOCAL_ONLY)
        self.assertEqual(route.status, ModelProviderStatus.UNAVAILABLE)
        self.assertIn("local_only", route.reason)

    def test_router_allows_explicit_hybrid_only_when_cloud_policy_is_enabled(self) -> None:
        remote = ModelProvider(
            "remote", ModelProviderType.OPENAI_COMPATIBLE, "Remote", ModelProviderStatus.READY,
            (ModelCapability.CHAT,), local=False, enabled=True,
        )
        registry = ModelProviderRegistry((remote,))
        blocked = ModelRouter(registry, local_only_default=False, allow_cloud_providers=False, privacy_mode=PrivacyMode.NORMAL_HYBRID).route_for_task("chat")
        allowed = ModelRouter(registry, local_only_default=False, allow_cloud_providers=True, privacy_mode=PrivacyMode.NORMAL_HYBRID).route_for_task("chat")
        self.assertEqual(blocked.status, ModelProviderStatus.UNAVAILABLE)
        self.assertEqual(allowed.status, ModelProviderStatus.READY)

    def test_existing_foundations_are_importable(self) -> None:
        from jarvis.execution import ExecutionPolicyEngine
        from jarvis.scheduler import SchedulerAgent
        from jarvis.browser import BrowserAgent
        from jarvis.evaluation import EvaluationRunner

        self.assertEqual(ExecutionPolicyEngine().plan("write a file").status.value, "approval_required")
        self.assertIn("background_runner", SchedulerAgent().status())
        self.assertIn("read_only", BrowserAgent().status()["status"])
        self.assertTrue(EvaluationRunner)

    def test_reconciled_ledger_has_every_step_and_record(self) -> None:
        root = Path(__file__).resolve().parents[1]
        ledger = (root / "docs" / "ENGINEERING_ROADMAP_1_122.md").read_text(encoding="utf-8")
        detail = (root / "docs" / "ENGINEERING_STEPS_64_94.md").read_text(encoding="utf-8")
        for step in range(64, 95):
            self.assertIn(f"| {step} |", ledger)
            self.assertIn(f"### Engineering Step {step}", detail)
        self.assertIn("Required step IDs: 64-94 inclusive = 31", detail)
        self.assertNotIn("Step 95", detail.split("## Block-Level Final Gate", 1)[0])


if __name__ == "__main__":
    unittest.main()
