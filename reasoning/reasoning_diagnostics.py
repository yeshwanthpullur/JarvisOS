"""Reasoning diagnostics."""

from __future__ import annotations


class ReasoningDiagnostics:
    def __init__(self) -> None:
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def report(self) -> dict[str, object]:
        if not self.initialized:
            raise RuntimeError("ReasoningDiagnostics must be initialized before use.")
        return {"status": "ready"}
