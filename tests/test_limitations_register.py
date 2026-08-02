"""Behavioral checks for the bounded limitations audit."""

from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from pathlib import Path


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
        self.assertLess(self.path.stat().st_size, 50_000)
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

    def test_health_and_status_match_register(self) -> None:
        health = json.loads((DOCS / "project_health.json").read_text(encoding="utf-8"))
        self.assertEqual(health["limitations"]["total"], self.data["counts"]["total"])
        self.assertEqual(health["limitations"]["fixed"], self.data["counts"]["fixed"])
        self.assertEqual(health["limitations"]["still_open"], self.data["counts"]["still_open"])
        current = (DOCS / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("**46** limitations", current)
        self.assertIn("**17 fixed**", current)
        self.assertIn("**29 still open**", current)

    def test_major_gaps_are_never_claimed_working(self) -> None:
        health = json.loads((DOCS / "project_health.json").read_text(encoding="utf-8"))
        statuses = {item["name"]: item["status"] for item in health["categories"]}
        self.assertEqual(statuses["Voice Input"], "Partial")
        self.assertEqual(statuses["Vision"], "Partial")
        self.assertEqual(statuses["Online Sync"], "Partial")
        self.assertEqual(statuses["Web Interface"], "Experimental")
        self.assertEqual(statuses["Web Automation"], "Partial")
        self.assertEqual(statuses["Mobile Automation"], "Partial")

    def test_setup_and_boundary_guidance_is_explicit(self) -> None:
        guide = (DOCS / "CLI_GUIDE.md").read_text(encoding="utf-8")
        status = (DOCS / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        for phrase in ("Local Voice Input Setup", "Vosk", "sounddevice", "JARVIS_VOSK_MODEL_PATH", "Local Vision Setup", "vision-capable"):
            self.assertIn(phrase, guide)
        for phrase in ("real authenticated encrypted adapter", "web interface is experimental", "Web automation", "Mobile automation"):
            self.assertIn(phrase.lower(), status.lower())
        web = (DOCS / "WEB_AUTOMATION.md").read_text(encoding="utf-8")
        for phrase in ("ReadOnlyWebInspectionAdapter", "blocked before adapter dispatch", "never persisted"):
            self.assertIn(phrase, web)

    def test_tracking_files_contain_no_secret_shaped_values(self) -> None:
        paths = (DOCS / "LIMITATIONS_REGISTER.md", self.path, DOCS / "CLI_GUIDE.md", DOCS / "CURRENT_STATUS.md")
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
