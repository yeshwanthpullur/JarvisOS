"""Checks for the master product vision and future milestone alignment."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class ProductVisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vision = (DOCS / "JARVIS_USE_CASES.md").read_text(encoding="utf-8")
        cls.roadmap = (DOCS / "ROADMAP.md").read_text(encoding="utf-8")
        cls.limitations = json.loads((DOCS / "limitations_register.json").read_text(encoding="utf-8"))

    def test_master_use_cases_has_required_sections(self) -> None:
        for section in (
            "Main Goal", "Product Philosophy", "What JARVIS Should Eventually Become",
            "What JARVIS Must Never Become", "User's Core Use Cases",
            "Long-Term Capability Areas", "Safety and Permission Principles",
            "Local-First and Privacy Rules", "Roadmap Priority Mapping",
            "Current Status Mapping", "Future Milestone Ownership",
            "What Counts as Done", "What Counts as Not Done",
            "Limitations That Must Stay Honest", "Product Direction Summary",
        ):
            self.assertIn(section, self.vision)

    def test_all_core_use_cases_are_mapped(self) -> None:
        for phrase in (
            "Replace Most AI Tools", "Speak With Me Naturally", "Build Anything I Ask",
            "Advanced Coding and Builder Mode", "Help With Studies", "Help With Research",
            "Help With Documents and Presentations", "Image Generation", "Video Editing",
            "Help With Mobile", "Help With Raspberry Pi", "Vision and Camera-Based",
            "Help With Web Automation", "Calls and Communication", "Long-Term Project Management",
        ):
            self.assertIn(phrase, self.vision)
        for field in ("**Why:**", "**Eventually:**", "**Examples:**", "**Required modules:**", "**Current status:**", "**Future owner:**", "**Safety:**"):
            self.assertGreaterEqual(self.vision.count(field), 15)

    def test_safety_prohibitions_are_explicit(self) -> None:
        for phrase in (
            "hacking", "surveillance", "credential-theft", "secret-recording",
            "send communications or make purchases without explicit approval",
            "bypass CAPTCHA/paywalls/login protections", "fake provider, sync, vision, voice, test, or automation success",
        ):
            self.assertIn(phrase, self.vision)

    def test_cybersecurity_scope_is_defensive_and_authorized(self) -> None:
        for phrase in (
            "Ethical Cybersecurity Learning and Defensive Security",
            "safe local labs", "CTF-style practice", "owns or is explicitly authorized",
            "real-target exploitation", "unauthorized access", "malware",
            "credential theft", "CAPTCHA/paywall/login bypass", "stealth",
            "destructive actions",
        ):
            self.assertIn(phrase, self.vision)

    def test_roadmap_owns_prompts_35_through_50(self) -> None:
        for prompt in range(35, 51):
            self.assertIn(f"Prompt {prompt}", self.roadmap)
            self.assertIn(f"Prompt {prompt}", self.vision)

    def test_future_goals_are_not_claimed_complete(self) -> None:
        current = (DOCS / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        for phrase in (
            "Video editing workflow",
            "Safe call and communication assistance",
            "Real encrypted remote synchronization and cross-device sync",
        ):
            self.assertIn(phrase, current)
        self.assertIn("Not Started Features", current)
        self.assertIn("Interactive actions remain blocked", current)
        self.assertIn("image workflow foundation", current.lower())

    def test_limitations_counts_and_prompt_41_fix_match(self) -> None:
        by_id = {item["limitation_id"]: item for item in self.limitations["limitations"]}
        fixed = by_id["LIM-029"]
        self.assertEqual(fixed["status"], "fixed")
        self.assertTrue(fixed["fix_implemented_in_this_prompt"])
        video = by_id["LIM-030"]
        self.assertEqual(video["status"], "fixed")
        self.assertTrue(video["fix_implemented_in_this_prompt"])
        for number in range(31, 37):
            item = by_id[f"LIM-{number:03d}"]
            self.assertEqual(item["status"], "deferred")
            self.assertFalse(item["fix_implemented_in_this_prompt"])
            self.assertTrue(item["next_owner_prompt"])
        counts = self.limitations["counts"]
        self.assertEqual(counts["total"], 47)
        self.assertEqual(counts["fixed"], 24)
        self.assertEqual(counts["still_open"], 23)

    def test_master_document_is_readable_bounded_and_secret_free(self) -> None:
        self.assertGreater(len(self.vision), 10_000)
        self.assertLess(len(self.vision), 50_000)
        patterns = (
            re.compile(r"sk-[A-Za-z0-9]{16,}"),
            re.compile(r"(?i)(api[_-]?key|password|access[_-]?token|secret)\s*=\s*[^\s`]+"),
            re.compile(r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._-]+"),
        )
        for pattern in patterns:
            self.assertIsNone(pattern.search(self.vision))


if __name__ == "__main__":
    unittest.main()
