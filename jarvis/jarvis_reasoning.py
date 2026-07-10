"""Reasoning architecture for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class JarvisReasoningRequest:
    """Reasoning request metadata."""

    prompt: str
    strategy: str = "metadata_only"
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class JarvisReasoningResult:
    """Reasoning result metadata."""

    confidence: float
    trace: tuple[str, ...] = ()
    provider_selection_metadata: dict[str, object] = field(default_factory=dict)
    execution_metadata: dict[str, object] = field(default_factory=dict)


class JarvisReasoning:
    """Reasoning interface without AI implementation."""

    initialized = True

    def reason(self, request: JarvisReasoningRequest) -> JarvisReasoningResult:
        """Return metadata-only reasoning output."""
        return JarvisReasoningResult(confidence=0.0, trace=("reasoning_not_implemented",))

