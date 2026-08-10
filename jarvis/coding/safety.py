"""Deterministic safety classification for coding requests."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .models import CodingRiskLevel


SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|password|access[_-]?token|secret|authorization|credential)\s*[:=]\s*\S+"
)

_CRITICAL_TERMS = (
    "force push",
    "git reset --hard",
    "delete all files",
    "wipe repository",
    "steal credential",
    "show secrets",
    "read .env",
    "expose token",
    "disable security",
)
_HIGH_TERMS = (
    "edit file",
    "modify code",
    "fix automatically",
    "run command",
    "execute command",
    "install dependency",
    "commit",
    "push",
    "deploy",
    "change config",
)
_MEDIUM_TERMS = ("review diff", "refactor", "dependency", "inspect file", "local file")


@dataclass(frozen=True, slots=True)
class CodingSafetyDecision:
    risk_level: CodingRiskLevel
    allowed: bool
    approval_required: bool
    reason: str


def redact_secret_shaped(value: str) -> str:
    return SECRET_PATTERN.sub("[REDACTED]", value)


def evaluate_coding_safety(request: str) -> CodingSafetyDecision:
    lowered = " ".join(request.lower().split())
    if SECRET_PATTERN.search(request) or any(term in lowered for term in _CRITICAL_TERMS):
        return CodingSafetyDecision(CodingRiskLevel.CRITICAL, False, True, "Critical or secret-access coding actions are blocked.")
    if any(term in lowered for term in _HIGH_TERMS):
        return CodingSafetyDecision(CodingRiskLevel.HIGH, True, True, "Write, command, commit, push, dependency, and deployment actions require approval and are plan-only here.")
    if any(term in lowered for term in _MEDIUM_TERMS):
        return CodingSafetyDecision(CodingRiskLevel.MEDIUM, True, False, "Read-only review is allowed with bounded output.")
    return CodingSafetyDecision(CodingRiskLevel.LOW, True, False, "Plan-only coding support is allowed.")
