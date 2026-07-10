"""Retrieval execution context."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievalContext:
    memory_manager: Any | None = None
    knowledge_manager: Any | None = None
    brain_manager: Any | None = None
    conversation_history: Any | None = None
    workflow_history: Any | None = None
    task_history: Any | None = None
    provider_history: Any | None = None
    plugin_history: Any | None = None
    execution_history: Any | None = None
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("retrieval"))
    metadata: dict[str, Any] = field(default_factory=dict)
