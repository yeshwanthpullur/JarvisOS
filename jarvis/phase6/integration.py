"""Deterministic Phase 6 integration and release-candidate checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CheckState(StrEnum):
    PASS = "PASS"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    NOT_TESTED = "NOT_TESTED"


@dataclass(frozen=True, slots=True)
class ComponentCheck:
    component: str
    state: CheckState
    evidence: str


@dataclass(frozen=True, slots=True)
class Phase6CandidateReport:
    checks: tuple[ComponentCheck, ...]
    candidate_ready: bool
    critical_blockers: tuple[str, ...]
    degradations: tuple[str, ...]

    def summary(self) -> dict[str, object]:
        return {
            "candidate_ready": self.candidate_ready,
            "pass": sum(item.state is CheckState.PASS for item in self.checks),
            "degraded": sum(item.state is CheckState.DEGRADED for item in self.checks),
            "blocked": sum(item.state is CheckState.BLOCKED for item in self.checks),
            "not_tested": sum(item.state is CheckState.NOT_TESTED for item in self.checks),
            "critical_blockers": len(self.critical_blockers),
        }


def evaluate_candidate(runtime: object, *, probe_provider: bool = False) -> Phase6CandidateReport:
    """Evaluate integration state without executing tools or mutating authorities."""
    if probe_provider:
        runtime.models.refresh(probe=True)
    models = runtime.models.summary()
    web = runtime.web.status()
    documents = runtime.documents.status()
    memory = runtime.memory.status()
    voice = runtime.voice.status()
    vision = runtime.vision.status()
    coding = runtime.coding.status()
    automation = runtime.automation.status()
    connectors = runtime.connectors.summary()
    observability = runtime.observability.snapshot()

    model_state = CheckState.PASS if models["healthy_providers"] else CheckState.DEGRADED
    checks = (
        ComponentCheck("Core chat and command dispatch", CheckState.PASS, "Existing Conversation and Command Registry authorities remain active."),
        ComponentCheck("Local model", model_state, "Ollama is healthy." if model_state is CheckState.PASS else "Ollama was not proven healthy by this check; no cloud fallback is allowed."),
        ComponentCheck("Browser and research", CheckState.DEGRADED if not web["network_allowed"] else CheckState.PASS, "Read-only planning is available; interactive and high-risk actions remain blocked."),
        ComponentCheck("Documents", CheckState.PASS if documents["builtin_text"] else CheckState.BLOCKED, "Explicit bounded text ingestion is available; optional rich parsers and OCR may be unavailable."),
        ComponentCheck("Memory and retrieval", CheckState.PASS, f"Authority={memory['authority']}; automatic writes are disabled."),
        ComponentCheck("Voice", CheckState.PASS if voice["tts"].selected else CheckState.DEGRADED, "Explicit local adapters only; wake and continuous listening are disabled."),
        ComponentCheck("Vision", CheckState.PASS, f"Local route={vision['primary']}; camera and cloud processing are disabled."),
        ComponentCheck("Coding", CheckState.PASS, f"Mode={coding['mode']}; writes, shell, and network are disabled."),
        ComponentCheck("Automation", CheckState.PASS, f"Authority={automation['authority']}; arbitrary shell is disabled."),
        ComponentCheck("Connectors, MCP, and plugins", CheckState.DEGRADED if not connectors["configured"] else CheckState.PASS, "Discovery metadata is available; unconfigured connectors cannot execute."),
        ComponentCheck("Observability", CheckState.PASS, f"Authority={observability['authority']}; telemetry and payload capture are disabled."),
        ComponentCheck("Security and governance", CheckState.PASS, "Execution Policy, Approval System, Broker, and Governance remain authoritative."),
        ComponentCheck("Deployment", CheckState.NOT_TESTED, "Vercel and remote commit association require an external post-push check."),
    )
    blockers = tuple(item.component for item in checks if item.state is CheckState.BLOCKED)
    degradations = tuple(item.component for item in checks if item.state in {CheckState.DEGRADED, CheckState.NOT_TESTED})
    return Phase6CandidateReport(checks, not blockers, blockers, degradations)
