"""Tests for project status, roadmap, health, and data-policy tracking."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from commands import CommandManager


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REQUIRED_DOCS = (
    "CURRENT_STATUS.md",
    "ROADMAP.md",
    "PROJECT_HEALTH.md",
    "RELEASE_CHECKLIST.md",
    "SYNC_STRATEGY.md",
    "AUTOMATION_STRATEGY.md",
    "MEMORY_AND_DATA_POLICY.md",
    "MEMORY_INTELLIGENCE.md",
    "VISION_INTELLIGENCE.md",
    "LIMITATIONS_REGISTER.md",
    "WEB_AUTOMATION.md",
    "JARVIS_USE_CASES.md",
    "MOBILE_AUTOMATION.md",
    "VOICE_INPUT.md",
)


class ProjectTrackingTests(unittest.TestCase):
    def test_required_status_documents_exist(self) -> None:
        for name in REQUIRED_DOCS:
            with self.subTest(name=name):
                self.assertTrue((DOCS / name).is_file())
        self.assertTrue((ROOT / "CHANGELOG.md").is_file())

    def test_project_health_json_is_valid_and_bounded(self) -> None:
        path = DOCS / "project_health.json"
        health = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(health["release"], "v0.9.0-alpha")
        self.assertEqual(health["commit"], "b0222c76a054fad0a9c735d7d2ad58253c2142af")
        vision = next(item for item in health["categories"] if item["name"] == "Vision")
        self.assertEqual(vision["status"], "Working")
        memory = next(item for item in health["categories"] if item["name"] == "Memory")
        self.assertEqual(memory["status"], "Working")
        self.assertGreaterEqual(health["overall_mvp_readiness"], 0)
        self.assertLessEqual(health["overall_mvp_readiness"], 100)
        self.assertLess(path.stat().st_size, 20_000)
        deployment = next(item for item in health["categories"] if item["name"] == "Deployment / Online Foundation")
        self.assertEqual(deployment["status"], "Working")
        online_sync = next(item for item in health["categories"] if item["name"] == "Online Sync")
        self.assertEqual(online_sync["status"], "Partial")
        web = next(item for item in health["categories"] if item["name"] == "Web Automation")
        self.assertEqual(web["status"], "Partial")
        mobile = next(item for item in health["categories"] if item["name"] == "Mobile Automation")
        self.assertEqual(mobile["status"], "Partial")
        self.assertEqual(len(health["categories"]), 24)
        allowed = {"Working", "Partial", "Experimental", "Not Started", "Blocked"}
        for category in health["categories"]:
            self.assertIn(category["status"], allowed)
            self.assertGreaterEqual(category["confidence"], 0)
            self.assertLessEqual(category["confidence"], 100)
            self.assertTrue(category["evidence"])
            self.assertTrue(category["next_action"])

    def test_current_status_has_required_sections(self) -> None:
        text = (DOCS / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        for heading in (
            "## Current Release",
            "## Stable Launch",
            "## Working Features",
            "## Partially Working Features",
            "## Experimental Features",
            "## Not Started Features",
            "## Blocked Features",
            "## Known Limitations",
            "## Next Recommended Prompt",
            "## Last Verified Tests",
            "## Manual Verification Checklist",
        ):
            self.assertIn(heading, text)
        self.assertIn("normal CLI is the current primary", text)
        self.assertIn("Vision Intelligence", text)
        self.assertIn("Online Sync", text)
        self.assertIn("automatic detection treated root `main.py`", text)
        self.assertIn("jarvis-os-6oy2", text)
        self.assertIn("jarvis-221b5o5fc-jj1-e21e.vercel.app/api/status", text)
        self.assertIn("read-only public", text)

    def test_roadmap_covers_completed_and_next_milestones(self) -> None:
        text = (DOCS / "ROADMAP.md").read_text(encoding="utf-8")
        for milestone in range(27, 36):
            if milestone in {27, 28, 29, 30, 31, 32, 33, 34, 35}:
                self.assertIn(f"Prompt {milestone}", text)
        self.assertIn("v0.3.0-alpha", text)

    def test_release_checklist_contains_core_gates(self) -> None:
        text = (DOCS / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
        for gate in ("git status --short", "git diff --check", "CHANGELOG.md", "Annotated tag", "Manual"):
            self.assertIn(gate.lower(), text.lower())

    def test_changelog_contains_alpha_release(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("v0.3.0-alpha", text)
        self.assertIn("Local Voice and CLI Stability", text)
        self.assertIn("1,374 passed", text)

    def test_tracking_docs_are_readable_and_nonempty(self) -> None:
        paths = tuple(DOCS / name for name in REQUIRED_DOCS) + (ROOT / "CHANGELOG.md",)
        for path in paths:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertGreater(len(text), 200)
                limit = 50_000 if path.name == "JARVIS_USE_CASES.md" else 20_000
                self.assertLess(len(text), limit)
                self.assertTrue(text.startswith("# "))

    def test_tracking_docs_do_not_contain_secret_values(self) -> None:
        paths = tuple(DOCS / name for name in REQUIRED_DOCS) + (
            DOCS / "project_health.json",
            ROOT / "CHANGELOG.md",
            ROOT / "README.md",
        )
        patterns = (
            re.compile(r"sk-[A-Za-z0-9]{16,}"),
            re.compile(r"(?i)(api[_-]?key|password|access[_-]?token|secret)\s*=\s*[^\s`]+"),
            re.compile(r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._-]+"),
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for pattern in patterns:
                self.assertIsNone(pattern.search(text), f"Potential secret value in {path.name}")

    def test_project_status_command_is_concise_and_data_backed(self) -> None:
        commands = CommandManager()
        commands.initialize()
        response = commands.execute("project status")
        self.assertIn("release=v0.9.0-alpha", response.response)
        self.assertIn("MVP=75%", response.response)
        self.assertIn("Prompt 39", response.response)
        self.assertIn("limitations=fixed:20/open:26", response.response)
        self.assertIn("focus=LIM-018", response.response)
        self.assertLess(len(response.response), 500)
        self.assertEqual(response.metadata["overall_mvp_readiness"], 75)
        self.assertEqual(response.metadata["fixed_limitations"], 20)
        self.assertEqual(response.metadata["open_limitations"], 26)

    def test_sync_tracking_is_honest_and_local_first(self) -> None:
        status = (DOCS / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        strategy = (DOCS / "SYNC_STRATEGY.md").read_text(encoding="utf-8")
        policy = (DOCS / "MEMORY_AND_DATA_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("No real encrypted remote adapter", status)
        self.assertIn("not a sync backend", status)
        self.assertIn("defaults to `off`", strategy)
        self.assertIn("unavailable remote adapter cannot mark an item synced", strategy)
        self.assertIn("must not contain raw memory", policy)
        self.assertIn("Persistent Personal Context", policy)
        self.assertIn("bounded retrieval snippets", policy)


if __name__ == "__main__":
    unittest.main()
