"""Response model for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from jarvis.jarvis_utils import utc_now


@dataclass(frozen=True, slots=True)
class JarvisResponse:
    """Unified response returned by the Executive Core."""

    request_id: str
    content: str
    success: bool = True
    response_id: str = field(default_factory=lambda: str(uuid4()))
    response_type: str = "direct"
    execution_summary: dict[str, Any] = field(default_factory=dict)
    references: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    recovery_information: dict[str, Any] = field(default_factory=dict)
    streaming_metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: object = field(default_factory=utc_now)

