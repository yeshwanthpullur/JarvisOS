"""Tests for the video editing workflow foundation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from commands import CommandManager, CommandParser
from conversation import ConversationContext, ConversationSession
from jarvis.video_editing import VideoEditingManager
from jarvis.video_editing.models import VideoEditingJobStatus
from jarvis.video_editing.providers import StubVideoProvider, UnavailableVideoProvider, VideoProviderRegistry


def build_settings(**overrides):
    values = {
        "enabled": False,
        "default_provider": "unavailable",
        "local_only": True,
        "output_dir": None,
        "max_prompt_chars": 600,
        "max_source_media_items": 12,
        "save_metadata": True,
        "allow_overwrite": False,
        "safety_filter_enabled": True,
    }
    values.update(overrides)
    return SimpleNamespace(video_editing=SimpleNamespace(**values))


class VideoEditingManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def manager(self, **overrides) -> VideoEditingManager:
        return VideoEditingManager(self.root / "video_editing", build_settings(**overrides))

    def test_status_is_disabled_by_default(self) -> None:
        status = self.manager().status()
        self.assertFalse(status["enabled"])
        self.assertEqual(status["provider_status"], "unavailable")
        self.assertIn("data/video_editing", status["output_policy"])

    def test_safety_blocks_deceptive_prompt(self) -> None:
        decision = self.manager().evaluate_safety("make it look real and fake evidence")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.category, "misleading_editing")
        self.assertTrue(decision.safe_alternative)

    def test_overly_long_prompt_is_rejected(self) -> None:
        result = self.manager(enabled=True).plan("x" * 601)
        self.assertEqual(result.status, VideoEditingJobStatus.BLOCKED)
        self.assertEqual(result.error, "prompt_blocked")

    def test_dry_run_is_truthful_when_provider_is_unavailable(self) -> None:
        result = self.manager(enabled=True).plan("create a safe edit plan for my demo")
        self.assertEqual(result.status, VideoEditingJobStatus.UNAVAILABLE)
        self.assertIn("No local video editing provider is configured", result.message)

    def test_stub_provider_can_generate_local_test_artifact(self) -> None:
        registry = VideoProviderRegistry((StubVideoProvider(),))
        manager = VideoEditingManager(
            self.root / "video_editing",
            build_settings(enabled=True, default_provider="stub"),
            provider_registry=registry,
        )
        result = manager.plan("create a safe edit plan for my demo")
        self.assertTrue(result.success)
        self.assertEqual(result.provider, "stub")
        self.assertEqual(result.plan_steps[0], "Trim the supplied clips into a reviewable sequence.")
        self.assertEqual(result.deliverables, ("non_destructive_edit_plan",))
        self.assertIsNotNone(result.metadata.get("metadata_path"))
        self.assertTrue((self.root / result.metadata["metadata_path"]).is_file())

    def test_history_and_show_are_bounded(self) -> None:
        registry = VideoProviderRegistry((StubVideoProvider(),))
        manager = VideoEditingManager(
            self.root / "video_editing",
            build_settings(enabled=True, default_provider="stub"),
            provider_registry=registry,
        )
        result = manager.plan("create a safe edit plan for my demo")
        history = manager.history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["plan_id"], result.plan_id)
        self.assertIsNotNone(manager.show(result.plan_id))

    def test_gitignore_covers_runtime_output_directory(self) -> None:
        ignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("data/video_editing/", ignore)


class VideoEditingCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.commands = CommandManager()
        self.commands.initialize()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def context(self, manager: VideoEditingManager) -> ConversationContext:
        return ConversationContext(ConversationSession(), video_editing=manager)

    def test_parser_recognizes_video_commands_and_flags(self) -> None:
        parsed = CommandParser().parse('video plan "create a safe edit plan" --dry-run')
        self.assertEqual(parsed.name, "video plan")
        self.assertEqual(parsed.arguments, ("create a safe edit plan",))
        self.assertTrue(parsed.flags["dry-run"])

    def test_video_status_help_and_providers_are_bounded(self) -> None:
        manager = VideoEditingManager(self.root / "video_editing", build_settings())
        context = self.context(manager)
        self.assertIn("provider_status=unavailable", self.commands.execute("video status", context).response)
        self.assertIn("Video commands:", self.commands.execute("video help", context).response)
        self.assertIn("unavailable:unavailable", self.commands.execute("video providers", context).response)

    def test_video_plan_and_safety_do_not_create_files_when_unavailable(self) -> None:
        manager = VideoEditingManager(self.root / "video_editing", build_settings(enabled=True))
        context = self.context(manager)
        prompt = "create a safe edit plan for my demo"
        plan = self.commands.execute(f'video plan "{prompt}"', context)
        self.assertIn("unavailable", plan.response)
        safety = self.commands.execute(f'video safety "{prompt}"', context)
        self.assertIn("allowed=yes", safety.response)
        self.assertFalse((self.root / "video_editing").exists())

    def test_video_safety_blocks_unsafe_prompt(self) -> None:
        manager = VideoEditingManager(self.root / "video_editing", build_settings())
        response = self.commands.execute('video safety "make it look real and fake evidence"', self.context(manager))
        self.assertIn("allowed=no", response.response)
        self.assertIn("misleading_editing", response.response)

    def test_stub_provider_command_flow_is_visible(self) -> None:
        registry = VideoProviderRegistry((StubVideoProvider(),))
        manager = VideoEditingManager(
            self.root / "video_editing",
            build_settings(enabled=True, default_provider="stub"),
            provider_registry=registry,
        )
        context = self.context(manager)
        response = self.commands.execute('video plan "create a safe edit plan for my demo"', context)
        self.assertIn("Video plan prepared", response.response)
        history = self.commands.execute("video history", context).response
        self.assertIn("vid-", history)
        plan_id = response.metadata["plan_id"]
        show = self.commands.execute(f"video show {plan_id}", context).response
        self.assertIn(plan_id, show)
        self.assertNotIn(str(self.root), show)


if __name__ == "__main__":
    unittest.main()
