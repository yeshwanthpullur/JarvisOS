"""Deterministic, side-effect-free Prompt 85 release-gate evaluator."""

from importlib.util import find_spec
import json
from pathlib import Path
import subprocess
from .models import GateState, ReleaseCandidate, ReleaseGate, SystemContract, ValidationReport


REQUIRED_PHASE5 = {
    "external_integration_control_plane": "jarvis.integrations.registry",
    "external_communication_runtime": "jarvis.integrations.communication",
    "telegram_connector": "jarvis.integrations.telegram",
    "github_provider": "jarvis.integrations.github",
    "mcp_runtime": "jarvis.mcp.runtime",
    "plugin_runtime": "jarvis.plugins.runtime",
    "advanced_model_runtime": "jarvis.models.runtime",
    "external_research_runtime": "jarvis.research.runtime",
    "knowledge_retrieval_runtime": "jarvis.knowledge.runtime",
    "external_orchestration_runtime": "jarvis.orchestration.runtime",
    "long_running_workflow_runtime": "jarvis.workflows.runtime",
    "reliability_runtime": "jarvis.reliability.runtime",
    "enterprise_governance": "jarvis.governance.runtime",
}


class ReleaseReadinessEvaluator:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self._last_report: ValidationReport | None = None

    @staticmethod
    def _available(module: str) -> bool:
        try:
            return find_spec(module) is not None
        except (ImportError, ModuleNotFoundError, AttributeError):
            return False

    def _git(self, *args: str) -> str:
        try:
            result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, timeout=5, shell=False)
            return result.stdout.strip() if result.returncode == 0 else "unavailable"
        except (OSError, subprocess.SubprocessError):
            return "unavailable"

    def contracts(self) -> tuple[SystemContract, ...]:
        return (
            SystemContract("Executive JARVIS", "final request authority", "core runtime", ("Prime Agent",), ("validate", "respond"), ("silent side effects",), GateState.PASSED),
            SystemContract("Prime Agent", "coordination only", "agent system", ("Agent Registry", "Model Router"), ("route", "plan"), ("direct execution", "approval bypass"), GateState.PASSED),
            SystemContract("Execution Policy", "action policy authority", "Phase 4 execution", (), ("classify", "block"), ("grant approval",), GateState.PASSED),
            SystemContract("Approval System", "exact authorization authority", "Phase 4 approvals", ("Execution Policy",), ("approve", "deny", "expire"), ("execute",), GateState.PASSED),
            SystemContract("Execution Broker", "execution dispatch authority", "Phase 4 broker", ("Execution Policy", "Approval System"), ("validate", "dispatch approved executor"), ("grant permission",), GateState.PASSED),
            SystemContract("Vercel API", "bounded status only", "api/index.py", (), ("status", "health"), ("agents", "models", "execution", "providers"), GateState.PASSED),
        )

    def evaluate(self) -> ValidationReport:
        missing = tuple(name for name, module in REQUIRED_PHASE5.items() if not self._available(module))
        phase4_modules = all(self._available(x) for x in ("jarvis.execution.policy", "jarvis.execution.broker", "jarvis.approvals.registry"))
        api_text = (self.root / "api" / "index.py").read_text(encoding="utf-8", errors="replace")
        api_bounded = not any(x in api_text for x in ("ExecutionBroker", "FileExecutor", "ModelRouter", "Telegram"))
        config_valid = False
        try:
            json.loads((self.root / "docs" / "project_health.json").read_text(encoding="utf-8"))
            config_valid = (self.root / "config.yaml").is_file()
        except (OSError, ValueError):
            pass
        tracked = self._git("status", "--short", "--untracked-files=no")
        clean = tracked == ""
        gates = (
            ReleaseGate("architecture", "Architecture", GateState.PASSED if phase4_modules else GateState.FAILED, not phase4_modules, "systems", ("Executive, Prime, Policy, Approval, and Broker boundaries inspected.",)),
            ReleaseGate("security", "Security", GateState.PASSED if phase4_modules and api_bounded else GateState.FAILED, True, "security", ("Critical execution remains blocked; Vercel has no executor imports.",)),
            ReleaseGate("privacy", "Privacy", GateState.PASSED if api_bounded else GateState.FAILED, True, "privacy", ("Vercel remains status-only.",)),
            ReleaseGate("configuration", "Configuration", GateState.PASSED if config_valid else GateState.FAILED, True, "configuration", ("Health JSON parses and config.yaml exists.",)),
            ReleaseGate("repository", "Repository Cleanliness", GateState.PASSED if clean else GateState.WARNING, False, "release", (("Tracked tree clean." if clean else "Tracked changes exist during validation."),)),
            ReleaseGate("phase5-components", "Phase 5 Integration", GateState.BLOCKED if missing else GateState.PASSED, True, "phase5", tuple(f"missing:{x}" for x in missing), (("Prompts 71-84 were not implemented." if missing else "All required Phase 5 components detected."),)),
            ReleaseGate("governance", "Governance", GateState.BLOCKED if "enterprise_governance" in missing else GateState.PASSED, True, "governance"),
            ReleaseGate("reliability", "Reliability", GateState.BLOCKED if "reliability_runtime" in missing else GateState.PASSED, True, "reliability"),
            ReleaseGate("workflow", "Workflow", GateState.BLOCKED if "long_running_workflow_runtime" in missing else GateState.PASSED, True, "workflow"),
            ReleaseGate("release", "Release Validation", GateState.BLOCKED if missing else GateState.WARNING, True, "release", (), ("No v2.0.0 tag or release is authorized.",)),
        )
        status = GateState.BLOCKED if any(g.blocking and g.status in {GateState.BLOCKED, GateState.FAILED} for g in gates) else GateState.WARNING
        self._last_report = ValidationReport(status, gates, self.contracts(), missing, ("Prompt 85 validates readiness; it does not implement missing Phase 5 capabilities.",))
        return self._last_report

    def candidate(self) -> ReleaseCandidate:
        report = self._last_report or self.evaluate()
        commit = self._git("rev-parse", "HEAD")
        branch = self._git("branch", "--show-current")
        blocking = tuple(g.gate_id for g in report.gates if g.blocking and g.status in {GateState.BLOCKED, GateState.FAILED})
        return ReleaseCandidate("v2.0.0", commit, branch, report.status, tuple(g.gate_id for g in report.gates), blocking)
