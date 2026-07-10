"""Composition context for Agent Creator services."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentCreatorContext:
    """References supplied to Agent Creator without exposing internals."""

    project_root: Path
    settings: Any | None = None
    agent_manager: Any | None = None
    plugin_manager: Any | None = None
    provider_router: Any | None = None
    logger: logging.Logger | None = None

