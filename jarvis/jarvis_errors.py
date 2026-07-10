"""Error classification models for the Executive JARVIS Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class JarvisErrorRecord:
    """Structured error record for diagnostics and recovery."""

    category: str
    message: str
    recoverable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

