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
    "IMAGE_GENERATION.md",
    "VIDEO_EDITING.md",
    "AGENTS.md",
    "PRIME_AGENT.md",
    "MODEL_ROUTER.md",
    "SKILLS.md",
    "MULTI_AGENT_OS_FOUNDATION.md",
    "RESEARCH_AGENT.md",
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
        self.assertEqual(health["release"], "v1.7.0-alpha")
        self.assertEqual(health["commit"], "d2fe98726183b9c8d0f776663330d169f172f0b7")
        self.assertEqual(health["next_milestone"], "Prompt 85 validation blocked; Prompt 72 awaits explicit approval")
        self.assertEqual(health["overall_mvp_readiness"], 92)
        self.assertEqual(health["phase3"]["coding_agent"], "ready_plan_only")
        self.assertFalse(health["phase3"]["coding_write_operations_enabled"])
        self.assertFalse(health["phase3"]["coding_command_execution_enabled"])
        vision = next(item for item in health["categories"] if item["name"] == "Vision")
        self.assertEqual(vision["status"], "Working")
        memory = next(item for item in health["categories"] if item["name"] == "Memory")
        self.assertEqual(memory["status"], "Working")
        creative = next(item for item in health["categories"] if item["name"] == "Creative Media Workflows")
        self.assertEqual(creative["status"], "Partial")
        self.assertEqual(creative["confidence"], 44)
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
        conversation = next(item for item in health["categories"] if item["name"] == "Conversation Intelligence")
        self.assertEqual(conversation["status"], "Working")
        self.assertEqual(len(health["categories"]), 31)
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
        self.assertIn("current primary", text.lower())
        self.assertIn("Vision Intelligence", text)
        self.assertIn("Online Sync", text)
        self.assertIn("automatic detection treated root `main.py`", text)
        self.assertIn("jarvis-os-6oy2", text)
        self.assertIn("read-only public", text)
        self.assertIn("image generation workflow foundation", text.lower())
        self.assertIn("video editing workflow foundation", text.lower())
        self.assertIn("research_agent_status", text)

    def test_roadmap_covers_completed_and_next_milestones(self) -> None:
        text = (DOCS / "ROADMAP.md").read_text(encoding="utf-8")
        for milestone in range(27, 43):
            self.assertIn(f"Prompt {milestone}", text)
        self.assertIn("v0.3.0-alpha", text)
        self.assertIn("Prompt 42 - Video Editing Workflow Foundation", text)
        self.assertIn("Prompt 49 - Phase 3 Integration", text)
        self.assertIn("Prompt 51 - Research Agent Foundation", text)
        self.assertIn("Prompt 52 - Coding Agent Foundation", text)
        self.assertIn("Prompt 60 - Phase 3 Batch 2", text)

    def test_release_checklist_contains_core_gates(self) -> None:
        text = (DOCS / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
        for gate in ("git status --short", "git diff --check", "CHANGELOG.md", "Annotated tag", "Manual"):
            self.assertIn(gate.lower(), text.lower())

    def test_changelog_contains_current_unreleased_sections(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("Image Generation Workflow Foundation", text)
        self.assertIn("Limitations Review and Safe Fix Pass", text)
        self.assertIn("1,600 passed", text)
        self.assertIn("Video Editing Workflow Foundation", text)
        self.assertIn("Multi-Agent OS Foundation", text)

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
        self.assertIn("release=v1.7.0-alpha", response.response)
        self.assertIn("MVP=92%", response.response)
        self.assertIn("Prompt 85 validation blocked", response.response)
        self.assertIn("p85=blocked", response.response)
        self.assertIn("coding:ready_plan_only", response.response)
        self.assertIn("limitations=fixed:24/open:23/restricted:5/blocked:2", response.response)
        self.assertIn("focus=LIM-045", response.response)
        self.assertIn("phase3=agents:", response.response)
        self.assertIn("prime:ready", response.response)
        self.assertIn("model_router:ready", response.response)
        self.assertLess(len(response.response), 700)
        self.assertEqual(response.metadata["overall_mvp_readiness"], 92)
        self.assertEqual(response.metadata["fixed_limitations"], 24)
        self.assertEqual(response.metadata["open_limitations"], 23)
        self.assertEqual(response.metadata["total_agents"], 29)
        self.assertEqual(response.metadata["coding_agent_status"], "ready_plan_only")
        self.assertEqual(response.metadata["coding_default_mode"], "plan_only")
        self.assertEqual(response.metadata["prime_agent_status"], "ready")
        self.assertEqual(response.metadata["model_router_status"], "ready")
        self.assertEqual(response.metadata["skill_registry_status"], "ready")

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
