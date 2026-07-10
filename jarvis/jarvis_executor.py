"""Executor facade for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class JarvisExecutionResult:
    """Execution result metadata."""

    success: bool = True
    output: dict[str, object] = field(default_factory=dict)
    errors: tuple[str, ...] = ()


class JarvisExecutor:
    """Execution interface that performs no external work in this foundation."""

    initialized = True

    def execute(self, route: str, payload: dict[str, object] | None = None) -> JarvisExecutionResult:
        """Return metadata-only execution result."""
        return JarvisExecutionResult(output={"route": route, "payload": payload or {}})

