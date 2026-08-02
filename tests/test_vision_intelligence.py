"""Behavioral tests for the Vision Intelligence foundation."""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from commands import CommandManager
from commands.command_parser import CommandParser
from conversation import ConversationContext, ConversationSession
from jarvis.vision_intelligence import VisionIntelligence, VisionProviderInfo, VisionResult, VisionStatus
from providers.provider_types import ModelInfo, ProviderCapabilities, ProviderCapability, ProviderResponse


def png(width: int = 3, height: int = 2) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00"


class FakeVisionAdapter:
    def __init__(self, available: bool = True, local: bool = True) -> None:
        self.available = available
        self.local = local
        self.last_request = None

    def providers(self, local_only: bool = True):
        if not self.available or (local_only and not self.local): return ()
        return (VisionProviderInfo("vision-test", "vision-model", self.local, True, ("vision",)),)

    def execute(self, request, image_bytes, metadata):
        self.last_request = request
        return VisionResult(request.request_id, VisionStatus.COMPLETED, "A test image.", metadata, "vision-test", "vision-model")


class FakeOllamaProvider:
    provider_id = "ollama"
    kind = SimpleNamespace(value="ollama")
    enabled = True
    initialized = True

    def __init__(self, *, vision: bool = True) -> None:
        capabilities = (ProviderCapability.CHAT, ProviderCapability.VISION) if vision else (ProviderCapability.CHAT,)
        self._models = (ModelInfo("llava:7b" if vision else "llama3.2:1b", "local model", capabilities),)

    def health_check(self):
        return SimpleNamespace(available=True)

    def capabilities(self):
        capabilities = (ProviderCapability.CHAT, ProviderCapability.VISION) if ProviderCapability.VISION in self._models[0].capabilities else (ProviderCapability.CHAT,)
        return ProviderCapabilities(capabilities, self._models)


class FakeOllamaManager:
    def __init__(self, *, vision: bool = True, error: str | None = None) -> None:
        provider = FakeOllamaProvider(vision=vision)
        config = SimpleNamespace(local_only=True, base_url="http://127.0.0.1:11434")
        record = SimpleNamespace(provider=provider, config=config)
        self.registry = SimpleNamespace(all=lambda: (record,))
        self.last_request = None
        self.error = error
        self.router = self

    async def execute_with_failover(self, request):
        self.last_request = request
        return ProviderResponse("ollama", request.model or "", "A blue square on a white background." if not self.error else "", request_id=request.request_id, error=self.error)


class VisionIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        settings = SimpleNamespace(base_dir=self.root, vision=SimpleNamespace(enabled=True, local_only=True, privacy_mode="strict", max_image_size=1024, timeout_seconds=5, allowed_directories=(self.root,)))
        self.vision = VisionIntelligence(settings)

    def image(self, name: str = "sample.png", content: bytes | None = None) -> Path:
        path = self.root / name;path.write_bytes(png() if content is None else content);return path

    def context(self) -> ConversationContext:
        return ConversationContext(session=ConversationSession(), vision_intelligence=self.vision)

    def test_initialization_and_default_privacy(self):
        self.assertTrue(self.vision.initialized);self.assertTrue(self.vision.local_only);self.assertFalse(self.vision.status()["raw_image_persistence"])

    def test_valid_png_metadata(self):
        metadata = self.vision.validate_image(str(self.image()))
        self.assertEqual((metadata["width"], metadata["height"]), (3, 2));self.assertEqual(metadata["extension"], "png");self.assertNotEqual(metadata["file_size"], 0)

    def test_missing_image_rejected(self):
        self.assertEqual(self.vision.analyze(str(self.root / "missing.png")).status, VisionStatus.INVALID_INPUT)

    def test_unsupported_extension_rejected(self):
        self.assertEqual(self.vision.analyze(str(self.image("sample.txt"))).error, "unsupported_image_format")

    def test_empty_image_rejected(self):
        self.assertEqual(self.vision.analyze(str(self.image(content=b""))).error, "empty_image")

    def test_renamed_non_image_rejected(self):
        self.assertEqual(self.vision.analyze(str(self.image(content=b"not an image"))).error, "invalid_image_signature")

    def test_too_large_image_rejected(self):
        self.vision.max_image_size = 8
        self.assertEqual(self.vision.analyze(str(self.image())).error, "image_too_large")

    def test_outside_scope_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            path=Path(other)/"outside.png";path.write_bytes(png())
            self.assertEqual(self.vision.analyze(str(path)).error, "image_path_outside_allowed_scope")

    def test_unavailable_provider_is_truthful(self):
        result=self.vision.analyze(str(self.image()));self.assertEqual(result.status,VisionStatus.UNAVAILABLE);self.assertNotIn(str(self.root),result.error or "")

    def test_real_adapter_result_is_returned_without_persistence(self):
        adapter=FakeVisionAdapter();self.vision.adapter=adapter
        result=self.vision.analyze(str(self.image()),"What is shown?")
        self.assertEqual(result.status,VisionStatus.COMPLETED);self.assertEqual(result.content,"A test image.");self.assertNotIn("path",result.metadata);self.assertTrue(adapter.last_request.local_only)

    def test_local_only_blocks_cloud_adapter(self):
        self.vision.adapter=FakeVisionAdapter(local=False)
        self.assertEqual(self.vision.analyze(str(self.image()),local_only=True).status,VisionStatus.BLOCKED_BY_POLICY)

    def test_cli_status(self):
        manager=CommandManager();manager.initialize();response=manager.execute("vision status",self.context())
        self.assertIn("unavailable",response.response);self.assertIn("raw_image_persistence=off",response.response)

    def test_cli_describe_unavailable(self):
        manager=CommandManager();manager.initialize();response=manager.execute(f'vision describe "{self.image()}"',self.context())
        self.assertIn("vision-capable",response.response);self.assertNotIn(str(self.root),response.response)

    def test_cli_ask_completed(self):
        self.vision.adapter=FakeVisionAdapter();manager=CommandManager();manager.initialize()
        response=manager.execute(f'vision ask "{self.image()}" What is visible?',self.context())
        self.assertEqual(response.response,"A test image.");self.assertEqual(response.metadata["provider_id"],"vision-test")

    def test_parser_keeps_vision_commands_separate(self):
        parsed=CommandParser().parse(r'vision ask "C:\images\sample.png" What is visible?')
        self.assertEqual(parsed.name,"vision ask");self.assertEqual(parsed.arguments[0],r"C:\images\sample.png")


class LocalOllamaVisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "sample.png";self.image.write_bytes(png())

    def manager(self, provider_manager=None, **overrides):
        values = dict(enabled=True, local_only=True, privacy_mode="strict", provider="ollama", model="llava", ollama_host="http://127.0.0.1:11434", max_image_size=1024, timeout_seconds=5, audit_enabled=True, audit_retention=2, store_image_content=False, allowed_directories=(self.root,))
        values.update(overrides)
        settings = SimpleNamespace(base_dir=self.root, vision=SimpleNamespace(**values))
        return VisionIntelligence(settings, provider_manager, storage_dir=self.root / "audit")

    def context(self, vision):
        return ConversationContext(session=ConversationSession(), vision_intelligence=vision)

    def test_model_missing_state_is_distinct_from_ollama_unavailable(self):
        vision = self.manager(FakeOllamaManager(vision=False))
        status = vision.status()
        self.assertTrue(status["ollama_available"])
        self.assertFalse(status["model_available"])
        self.assertEqual(status["availability_status"], "model_missing")

    def test_mocked_local_ollama_analysis_uses_provider_router(self):
        provider_manager = FakeOllamaManager()
        vision = self.manager(provider_manager)
        result = vision.analyze(str(self.image), "What is visible?")
        self.assertTrue(result.success)
        self.assertEqual(result.provider_id, "ollama")
        self.assertEqual(result.model_id, "llava:7b")
        self.assertEqual(provider_manager.last_request.metadata["allowed_provider_ids"], ("ollama",))
        self.assertEqual(provider_manager.last_request.metadata["execution_policy"], "local_only")
        self.assertTrue(provider_manager.last_request.metadata["images"][0])
        self.assertIn("Do not identify real people", provider_manager.last_request.system_instructions)
        self.assertEqual(provider_manager.last_request.max_output_tokens, 512)
        audit_text = (self.root / "audit" / "audit.json").read_text(encoding="utf-8")
        self.assertNotIn(provider_manager.last_request.metadata["images"][0], audit_text)
        self.assertNotIn(str(self.root), audit_text)
        self.assertNotIn("What is visible?", audit_text)

    def test_non_local_only_mode_still_uses_only_local_ollama(self):
        provider_manager = FakeOllamaManager()
        vision = self.manager(provider_manager)
        result = vision.analyze(str(self.image), local_only=False)
        self.assertTrue(result.success)
        self.assertEqual(result.provider_id, "ollama")
        self.assertEqual(provider_manager.last_request.metadata["allowed_provider_ids"], ("ollama",))

    def test_timeout_is_normalized(self):
        vision = self.manager(FakeOllamaManager(error="request timed out"))
        result = vision.analyze(str(self.image))
        self.assertEqual(result.status, VisionStatus.TIMED_OUT)

    def test_question_length_is_bounded_before_dispatch(self):
        provider_manager = FakeOllamaManager()
        vision = self.manager(provider_manager)
        result = vision.analyze(str(self.image), "x" * 2_001)
        self.assertEqual(result.status, VisionStatus.INVALID_INPUT)
        self.assertIsNone(provider_manager.last_request)

    def test_non_loopback_ollama_host_is_rejected(self):
        vision = self.manager(FakeOllamaManager(), ollama_host="http://192.168.1.20:11434")
        self.assertEqual(vision.status()["availability_status"], "ollama_host_mismatch")

    def test_identity_and_medical_requests_are_blocked_before_dispatch(self):
        provider_manager = FakeOllamaManager()
        vision = self.manager(provider_manager)
        for question in ("Who is this person?", "Diagnose this rash"):
            with self.subTest(question=question):
                result = vision.analyze(str(self.image), question)
                self.assertEqual(result.status, VisionStatus.BLOCKED_BY_POLICY)
        self.assertIsNone(provider_manager.last_request)

    def test_audit_is_bounded_and_cleanup_never_deletes_image(self):
        vision = self.manager(FakeOllamaManager())
        for _ in range(3):
            vision.analyze(str(self.image))
        self.assertEqual(len(vision.audit_events()), 2)
        cleanup = vision.cleanup()
        self.assertEqual(cleanup["removed"], 2)
        self.assertTrue(self.image.exists())

    def test_cli_models_analyze_audit_and_cleanup(self):
        vision = self.manager(FakeOllamaManager())
        commands = CommandManager();commands.initialize();context = self.context(vision)
        self.assertIn("llava:7b", commands.execute("vision models", context).response)
        self.assertIn("blue square", commands.execute(f'vision analyze "{self.image}"', context).response)
        self.assertIn("metadata events", commands.execute("vision audit", context).response)
        self.assertIn("User images were not changed", commands.execute("vision cleanup", context).response)

    def test_parser_recognizes_all_new_commands(self):
        parser = CommandParser()
        for text, name in (("vision models", "vision models"), (r'vision analyze "C:\images\x.png"', "vision analyze"), ("vision audit", "vision audit"), ("vision cleanup", "vision cleanup")):
            self.assertEqual(parser.parse(text).name, name)


if __name__ == "__main__": unittest.main()
