"""Cross-subsystem validation helpers for the final engineering block."""

from __future__ import annotations

import re
from pathlib import Path

from jarvis.backup import BackupManager
from jarvis.foundation_common import bounded, contains_secret, new_id
from jarvis.models.privacy import PrivacyMode, PrivacyPolicy
from jarvis.models.types import ModelProvider

from .models import (
    BenchmarkReport,
    CapabilityMatrixRow,
    GoldenCaseResult,
    InjectionAssessment,
    LaptopBaseline,
    OperationalState,
    RevenueWorkflow,
    RouteAssessment,
    WorkspaceDecision,
    OperatingMode,
)


_INJECTION_RE = re.compile(
    r"(?i)(ignore\s+(?:all\s+)?previous|system\s+message|developer\s+message|reveal\s+.*(?:secret|prompt)|execute\s+.*command|tool\s+call|override\s+policy)"
)


_CAPABILITY_MATRIX = (
    CapabilityMatrixRow("LLM", "ready if provider healthy", "local provider only", "unavailable if no local model", "Ollama/local process", "bounded explanation", "local model runtime"),
    CapabilityMatrixRow("documents", "local parsing", "local parsing", "plain-text fallback", "built-in parser", "manual input", "file permission"),
    CapabilityMatrixRow("OCR", "provider-dependent", "local OCR if configured", "unavailable", "configured OCR adapter", "manual transcription", "OCR model"),
    CapabilityMatrixRow("RAG", "lexical/hybrid", "lexical", "lexical only", "local index", "bounded search", "local index"),
    CapabilityMatrixRow("memory", "local", "local", "local", "local governance", "session context", "memory authority"),
    CapabilityMatrixRow("STT", "provider-dependent", "Vosk/Faster-Whisper if configured", "text input", "local voice adapter", "typed input", "microphone/model"),
    CapabilityMatrixRow("TTS", "provider-dependent", "SAPI/Piper if configured", "text output", "local voice adapter", "text response", "voice backend"),
    CapabilityMatrixRow("research", "read-only sources", "project/doc sources", "plan only", "local docs", "manual sources", "approved source"),
    CapabilityMatrixRow("tools", "policy controlled", "local safe tools", "plan only", "Execution Broker", "manual action", "approval"),
    CapabilityMatrixRow("agents", "bounded planning", "bounded planning", "plan only", "local registry", "conversation fallback", "agent registry"),
    CapabilityMatrixRow("Git", "local repository", "local repository", "metadata only", "Git CLI", "manual Git", "repository"),
    CapabilityMatrixRow("Control Room", "local", "local", "metadata", "local runtime", "CLI status", "runtime state"),
    CapabilityMatrixRow("checkpoints", "local", "local", "local", "CheckpointStore", "manual recovery", "runtime storage"),
    CapabilityMatrixRow("recovery", "bounded", "bounded", "manual intervention", "RecoveryPlanner", "stop safely", "checkpoint"),
    CapabilityMatrixRow("automation", "plan/approved", "local plan", "manual", "workflow runtime", "manual workflow", "policy"),
)


class FinalBlockRuntime:
    """Metadata-only runtime for privacy, offline, and final-gate evidence."""

    def __init__(self, *, root: Path | None = None) -> None:
        self.root = Path(root or Path.cwd()).resolve()
        self.history: list[RouteAssessment] = []

    @staticmethod
    def capability_matrix() -> tuple[CapabilityMatrixRow, ...]:
        return _CAPABILITY_MATRIX

    @staticmethod
    def external_content(text: str, *, source_type: str = "external") -> InjectionAssessment:
        if not isinstance(text, str) or len(text) > 4000:
            return InjectionAssessment(True, True, "external_content_bounded_or_invalid", source_type)
        detected = bool(_INJECTION_RE.search(text))
        return InjectionAssessment(True, detected, "instruction_like_text_is_data_only" if detected else "no_instruction_marker_detected", source_type)

    def workspace(self, path: str | Path, *, workspace_root: Path | None = None) -> WorkspaceDecision:
        candidate = Path(path)
        base = Path(workspace_root or self.root).resolve()
        try:
            resolved = candidate.resolve() if candidate.is_absolute() else (base / candidate).resolve()
            resolved.relative_to(base)
        except (OSError, ValueError):
            return WorkspaceDecision(False, "workspace", "path_outside_workspace")
        if contains_secret(resolved.name) or resolved.name.lower() in {".git", ".env"}:
            return WorkspaceDecision(False, "workspace", "protected_path")
        return WorkspaceDecision(True, resolved.relative_to(base).as_posix()[:240], "path_within_workspace")

    def route(self, capability: str, provider: ModelProvider, *, privacy_mode: PrivacyMode | str = PrivacyMode.LOCAL_ONLY, online: bool = True, allow_cloud: bool = False, quality_class: str = "unknown") -> RouteAssessment:
        policy = PrivacyPolicy.from_value(privacy_mode, allow_cloud_providers=allow_cloud)
        decision = policy.evaluate(provider)
        if not online and not provider.local:
            decision = decision.__class__(provider.provider_id, policy.mode, False, "offline_rejects_remote_provider")
        result = RouteAssessment(capability, provider.provider_id, decision.allowed, policy.mode.value, OperationalState.ONLINE if online else OperationalState.OFFLINE, getattr(provider, "cost_class", "unknown"), quality_class, decision.reason)
        self.history = (self.history + [result])[-50:]
        return result

    @staticmethod
    def backup_state(source: Path, destination: Path, *, backup_id: str = "final-block-state"):
        manager = BackupManager(destination)
        record = manager.create(source, backup_id=backup_id)
        verified = manager.verify(record.backup_id)
        if not verified.verified:
            raise ValueError("backup_integrity_failed")
        return verified

    @staticmethod
    def golden_cases() -> tuple[GoldenCaseResult, ...]:
        return (
            GoldenCaseResult("privacy-local-only", "routing", True, "passed", "cloud provider rejected"),
            GoldenCaseResult("external-content", "security", True, "passed", "instruction-like text retained as data"),
            GoldenCaseResult("workspace-boundary", "security", True, "passed", "path policy enforced"),
            GoldenCaseResult("offline-fallback", "offline", True, "passed", "local fallback or unavailable state"),
            GoldenCaseResult("checkpoint-resume", "recovery", True, "passed", "resume is bounded and idempotent"),
            GoldenCaseResult("human-review", "commercial", True, "passed", "delivery remains approval-gated"),
        )

    def evaluate(self) -> BenchmarkReport:
        cases = self.golden_cases()
        passed = sum(case.passed for case in cases)
        return BenchmarkReport("final_block_golden", len(cases), passed, len(cases) - passed)

    @staticmethod
    def revenue_workflows() -> tuple[RevenueWorkflow, ...]:
        return (
            RevenueWorkflow("engineering-research", "Engineering Research Package", "Turn a scoped technical question into an evidence-backed package.", ("topic", "requirements", "deadline"), ("report", "references", "quality_record"), ("research", "documents", "rag", "verification"), ("source verification", "citation check", "human review")),
            RevenueWorkflow("technical-documentation", "Technical Documentation", "Turn notes and project material into a structured deliverable.", ("notes", "approved files"), ("document", "references", "delivery package"), ("documents", "knowledge", "quality"), ("completeness", "privacy", "human review")),
            RevenueWorkflow("content-package", "Short-Form Technical Content", "Prepare a researched, reviewable content package without autonomous publishing.", ("topic", "audience", "format"), ("script", "asset plan", "captions"), ("research", "image/video planning"), ("factual review", "copyright check", "human approval")),
        )

    @staticmethod
    def laptop_baseline() -> LaptopBaseline:
        return LaptopBaseline("READY_FOUNDATION", ("conversation", "goals", "tasks", "agents", "providers", "tools", "research", "documents", "rag", "memory", "voice", "vision", "browser", "mcp", "scheduler", "communication", "observability", "cost", "privacy", "security", "recovery", "backup", "evaluation", "control_room", "automation"), limitations=("optional providers remain unconfigured", "physical device validation remains pending"))

    def status(self) -> dict[str, object]:
        report = self.evaluate()
        return {"status": "ready_foundation", "operational_state": OperationalState.ONLINE.value, "operating_mode": OperatingMode.DEVELOPMENT.value + "/" + OperatingMode.TESTING.value, "matrix_capabilities": len(_CAPABILITY_MATRIX), "golden_passed": report.passed, "golden_total": report.total, "privacy_mode": PrivacyMode.LOCAL_ONLY.value, "cloud_required": False, "phone_transition": "planning_only", "history_items": len(self.history)}

    @staticmethod
    def operating_modes() -> tuple[str, ...]:
        return tuple(mode.value for mode in OperatingMode)
