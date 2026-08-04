"""Tests for the image generation workflow foundation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from commands import CommandManager, CommandParser
from conversation import ConversationContext, ConversationSession
from jarvis.image_generation import ImageGenerationManager
from jarvis.image_generation.models import ImageGenerationJobStatus
from jarvis.image_generation.providers import ImageProviderRegistry, StubImageProvider, UnavailableImageProvider


def build_settings(**overrides):
    values = {
        "enabled": False,
        "default_provider": "unavailable",
        "local_only": True,
        "output_dir": None,
        "max_prompt_chars": 600,
        "max_negative_prompt_chars": 300,
        "save_metadata": True,
        "allow_overwrite": False,
        "safety_filter_enabled": True,
    }
    values.update(overrides)
    return SimpleNamespace(image_generation=SimpleNamespace(**values))


class ImageGenerationManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def manager(self, **overrides) -> ImageGenerationManager:
        return ImageGenerationManager(self.root / "image_generation", build_settings(**overrides))

    def test_status_is_disabled_by_default(self) -> None:
        status = self.manager().status()
        self.assertFalse(status["enabled"])
        self.assertEqual(status["provider_status"], "unavailable")
        self.assertNotIn(str(self.root), str(status["output_policy"]))

    def test_safety_allows_engineering_prompt(self) -> None:
        decision = self.manager().evaluate_safety("create a clean technical concept sketch of a small mecanum-wheel robot")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.category, "allowed")

    def test_safety_blocks_explicit_prompt(self) -> None:
        decision = self.manager().evaluate_safety("create explicit unsafe content")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.category, "explicit_sexual_content")
        self.assertTrue(decision.safe_alternative)

    def test_overly_long_prompt_is_rejected(self) -> None:
        result = self.manager(enabled=True).plan("x" * 601)
        self.assertEqual(result.status, ImageGenerationJobStatus.BLOCKED)
        self.assertEqual(result.error, "prompt_blocked")

    def test_dry_run_is_truthful_when_provider_is_unavailable(self) -> None:
        result = self.manager(enabled=True).generate(
            "create a clean technical concept sketch of a small mecanum-wheel robot",
            dry_run=True,
        )
        self.assertEqual(result.status, ImageGenerationJobStatus.UNAVAILABLE)
        self.assertIn("No local image generation model", result.message)

    def test_stub_provider_can_generate_local_test_artifact(self) -> None:
        registry = ImageProviderRegistry((StubImageProvider(),))
        manager = ImageGenerationManager(
            self.root / "image_generation",
            build_settings(enabled=True, default_provider="stub"),
            provider_registry=registry,
        )
        result = manager.generate("create a simple safe robot icon")
        self.assertTrue(result.success)
        self.assertEqual(result.provider, "stub")
        self.assertEqual(len(result.output_paths), 1)
        self.assertEqual(Path(self.root / result.output_paths[0]).suffix, ".png")
        self.assertTrue((self.root / result.output_paths[0]).is_file())
        self.assertIsNotNone(result.metadata_path)
        self.assertTrue((self.root / result.metadata_path).is_file())

    def test_history_and_show_are_bounded(self) -> None:
        registry = ImageProviderRegistry((StubImageProvider(),))
        manager = ImageGenerationManager(
            self.root / "image_generation",
            build_settings(enabled=True, default_provider="stub"),
            provider_registry=registry,
        )
        result = manager.generate("create a simple safe robot icon")
        history = manager.history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["job_id"], result.job_id)
        self.assertIsNotNone(manager.show(result.job_id))

    def test_gitignore_covers_runtime_output_directory(self) -> None:
        ignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("data/image_generation/", ignore)


class ImageGenerationCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.commands = CommandManager()
        self.commands.initialize()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def context(self, manager: ImageGenerationManager) -> ConversationContext:
        return ConversationContext(ConversationSession(), image_generation=manager)

    def test_parser_recognizes_image_commands_and_flags(self) -> None:
        parsed = CommandParser().parse('image generate "create a robot sketch" --dry-run')
        self.assertEqual(parsed.name, "image generate")
        self.assertEqual(parsed.arguments, ("create a robot sketch",))
        self.assertTrue(parsed.flags["dry-run"])

    def test_image_status_help_and_providers_are_bounded(self) -> None:
        manager = ImageGenerationManager(self.root / "image_generation", build_settings())
        context = self.context(manager)
        self.assertIn("provider_status=unavailable", self.commands.execute("image status", context).response)
        self.assertIn("Image commands:", self.commands.execute("image help", context).response)
        self.assertIn("unavailable:unavailable", self.commands.execute("image providers", context).response)

    def test_image_plan_and_generate_dry_run_do_not_create_files(self) -> None:
        manager = ImageGenerationManager(self.root / "image_generation", build_settings(enabled=True))
        context = self.context(manager)
        prompt = "create a clean technical concept sketch of a small mecanum-wheel robot"
        plan = self.commands.execute(f'image plan "{prompt}"', context)
        self.assertIn("unavailable", plan.response)
        generated = self.commands.execute(f'image generate "{prompt}" --dry-run', context)
        self.assertIn("unavailable", generated.response)
        self.assertFalse((self.root / "image_generation").exists())

    def test_image_safety_blocks_unsafe_prompt(self) -> None:
        manager = ImageGenerationManager(self.root / "image_generation", build_settings())
        response = self.commands.execute('image safety "create explicit unsafe content"', self.context(manager))
        self.assertIn("allowed=no", response.response)
        self.assertIn("explicit_sexual_content", response.response)

    def test_stub_provider_command_flow_is_visible(self) -> None:
        registry = ImageProviderRegistry((StubImageProvider(),))
        manager = ImageGenerationManager(
            self.root / "image_generation",
            build_settings(enabled=True, default_provider="stub"),
            provider_registry=registry,
        )
        context = self.context(manager)
        response = self.commands.execute('image generate "create a simple safe robot icon"', context)
        self.assertIn("completed", response.response)
        history = self.commands.execute("image history", context).response
        self.assertIn("img-", history)
        job_id = response.metadata["job_id"]
        show = self.commands.execute(f"image show {job_id}", context).response
        self.assertIn(job_id, show)
        self.assertNotIn(str(self.root), show)


if __name__ == "__main__":
    unittest.main()
