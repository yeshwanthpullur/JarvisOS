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


if __name__ == "__main__": unittest.main()
