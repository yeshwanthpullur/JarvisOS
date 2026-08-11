"""Behavioral checks for the bounded limitations audit."""

from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from pathlib import Path

from commands import CommandManager
from jarvis.project_limitations import LimitationsRegister, LimitationsRegisterError, VALID_CATEGORIES


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class LimitationsRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = DOCS / "limitations_register.json"
        cls.data = json.loads(cls.path.read_text(encoding="utf-8"))
        cls.items = cls.data["limitations"]

    def test_register_files_exist_and_are_bounded(self) -> None:
        self.assertTrue((DOCS / "LIMITATIONS_REGISTER.md").is_file())
        self.assertTrue(self.path.is_file())
        self.assertLess(self.path.stat().st_size, 65_000)
        self.assertLess((DOCS / "LIMITATIONS_REGISTER.md").stat().st_size, 20_000)

    def test_counts_are_internally_consistent(self) -> None:
        counts = self.data["counts"]
        statuses = Counter(item["status"] for item in self.items)
        self.assertEqual(counts["total"], len(self.items))
        for status in ("fixed", "open", "deferred", "blocked", "experimental"):
            self.assertEqual(counts[status], statuses[status])
        self.assertEqual(counts["fixed_before_prompt"], sum(item["status"] == "fixed" and not item["fix_implemented_in_this_prompt"] for item in self.items))
        self.assertEqual(counts["fixed_during_prompt"], sum(item["status"] == "fixed" and item["fix_implemented_in_this_prompt"] for item in self.items))
        self.assertEqual(counts["fixed"], counts["fixed_before_prompt"] + counts["fixed_during_prompt"])
        self.assertEqual(counts["still_open"], counts["open"] + counts["deferred"] + counts["blocked"] + counts["experimental"])
        self.assertEqual(counts["total"], counts["fixed"] + counts["still_open"])

    def test_records_have_required_fields_and_valid_values(self) -> None:
        required = {"limitation_id", "title", "source", "status", "severity", "user_impact", "evidence", "fixability_now", "fix_implemented_in_this_prompt", "verification", "next_owner_prompt"}
        self.assertEqual(len({item["limitation_id"] for item in self.items}), len(self.items))
        for item in self.items:
            self.assertTrue(required.issubset(item))
            self.assertRegex(item["limitation_id"], r"^LIM-\d{3}$")
            self.assertIn(item["status"], {"fixed", "open", "deferred", "blocked", "experimental"})
            self.assertIn(item["severity"], {"low", "medium", "high"})
            self.assertIn(item["fixability_now"], {"yes", "no", "partial"})
            self.assertTrue(item["evidence"])
            self.assertTrue(item["verification"])
            if item["status"] != "fixed":
                self.assertTrue(item["next_owner_prompt"])

    def test_review_classifies_every_open_record(self) -> None:
        open_items = [item for item in self.items if item["status"] != "fixed"]
        categories = Counter(item.get("review_category") for item in open_items)
        self.assertNotIn(None, categories)
        self.assertTrue(set(categories).issubset(VALID_CATEGORIES))
        self.assertEqual(dict(categories), self.data["review"]["category_totals"])
        for item in open_items:
            self.assertTrue(item["next_owner_prompt"])
            self.assertTrue(item["evidence"])

    def test_fixed_entry_has_prompt_42_video_evidence(self) -> None:
        fixed = next(item for item in self.items if item["limitation_id"] == "LIM-030")
        self.assertEqual(fixed["status"], "fixed")
        self.assertTrue(fixed["fix_implemented_in_this_prompt"])
        self.assertTrue(fixed["fixed_at"])
        self.assertIn("test_video_editing", fixed["test_coverage"])

    def test_limitations_reader_rejects_malformed_data_safely(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"counts": {}, "limitations": [{"limitation_id": "LIM-001", "status": "wrong"}]}', encoding="utf-8")
            with self.assertRaises(LimitationsRegisterError):
                LimitationsRegister(path).load()

    def test_limitations_cli_is_bounded_and_project_status_has_categories(self) -> None:
        manager = CommandManager()
        manager.initialize()
        for command in ("limitations status", "limitations open", "limitations fixed", "limitations next", "limitations show LIM-029", "limitations show LIM-018"):
            response = manager.execute(command)
            self.assertTrue(response.response)
            self.assertLess(len(response.response), 1600)
            self.assertNotRegex(response.response, r"[A-Z]:\\")
        project = manager.execute("project status")
        self.assertIn("restricted:", project.response)
        self.assertIn("blocked:", project.response)
        self.assertIn("next=Prompt 83", project.response)

    def test_health_and_status_match_register(self) -> None:
        health = json.loads((DOCS / "project_health.json").read_text(encoding="utf-8"))
        self.assertEqual(health["limitations"]["total"], self.data["counts"]["total"])
        self.assertEqual(health["limitations"]["fixed"], self.data["counts"]["fixed"])
        self.assertEqual(health["limitations"]["still_open"], self.data["counts"]["still_open"])
        current = (DOCS / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("**47** limitations", current)
        self.assertIn("**24 fixed**", current)
        self.assertIn("**23 still open**", current)

    def test_markdown_and_json_counts_agree(self) -> None:
        register = (DOCS / "LIMITATIONS_REGISTER.md").read_text(encoding="utf-8")
        counts = self.data["counts"]
        for label, key in (("Total limitations audited", "total"), ("Fixed total", "fixed"), ("Still open in any form", "still_open")):
            self.assertRegex(register, rf"\| {re.escape(label)} \| {counts[key]} \|")

    def test_capability_statuses_match_verified_scope(self) -> None:
        health = json.loads((DOCS / "project_health.json").read_text(encoding="utf-8"))
        statuses = {item["name"]: item["status"] for item in health["categories"]}
        self.assertEqual(statuses["Voice Input"], "Working")
        self.assertEqual(statuses["Vision"], "Working")
        self.assertEqual(statuses["Online Sync"], "Partial")
        self.assertEqual(statuses["Web Interface"], "Experimental")
        self.assertEqual(statuses["Web Automation"], "Partial")
        self.assertEqual(statuses["Mobile Automation"], "Partial")
        self.assertEqual(statuses["Conversation Intelligence"], "Working")
        self.assertEqual(statuses["Creative Media Workflows"], "Partial")

    def test_setup_and_boundary_guidance_is_explicit(self) -> None:
        guide = (DOCS / "CLI_GUIDE.md").read_text(encoding="utf-8")
        status = (DOCS / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        for phrase in ("Local Voice Input Setup", "Vosk", "sounddevice", "JARVIS_VOSK_MODEL_PATH", "Local Vision Setup", "vision-capable", "Image Generation Workflow", "Video Editing Workflow"):
            self.assertIn(phrase, guide)
        for phrase in ("real authenticated encrypted adapter", "web interface is experimental", "Web Automation", "Mobile Automation"):
            self.assertIn(phrase.lower(), status.lower())
        web = (DOCS / "WEB_AUTOMATION.md").read_text(encoding="utf-8")
        for phrase in ("ReadOnlyWebInspectionAdapter", "blocked before adapter dispatch", "never persisted"):
            self.assertIn(phrase, web)
        image = (DOCS / "IMAGE_GENERATION.md").read_text(encoding="utf-8")
        for phrase in ("local-first workflow foundation", "image safety", "unavailable", "Vercel remains status-only"):
            self.assertIn(phrase, image)
        video = (DOCS / "VIDEO_EDITING.md").read_text(encoding="utf-8")
        for phrase in ("local-first video editing workflow foundation", "video safety", "unavailable", "Vercel remains status-only"):
            self.assertIn(phrase, video)

    def test_tracking_files_contain_no_secret_shaped_values(self) -> None:
        paths = (DOCS / "LIMITATIONS_REGISTER.md", self.path, DOCS / "CLI_GUIDE.md", DOCS / "CURRENT_STATUS.md", DOCS / "IMAGE_GENERATION.md", DOCS / "VIDEO_EDITING.md")
        patterns = (
            re.compile(r"sk-[A-Za-z0-9]{16,}"),
            re.compile(r"(?i)(api[_-]?key|password|access[_-]?token|secret)\s*=\s*[^\s`]+"),
            re.compile(r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._-]+"),
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for pattern in patterns:
                self.assertIsNone(pattern.search(text), f"Potential secret value in {path.name}")


if __name__ == "__main__":
    unittest.main()
