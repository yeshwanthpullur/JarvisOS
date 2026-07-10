"""Diagnostics for adaptive intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AdaptiveDiagnostics:
    reports: int = 0
    warnings: int = 0
    failures: int = 0

    def initialize(self) -> None:
        self.reports = self.warnings = self.failures = 0

    def summary(self) -> dict[str, Any]:
        return {"reports": self.reports, "warnings": self.warnings, "failures": self.failures}
