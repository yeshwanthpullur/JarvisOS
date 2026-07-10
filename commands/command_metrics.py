"""Command metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CommandMetrics:
    """Command metrics."""

    commands_executed: int = 0
    commands_failed: int = 0
    registered_commands: int = 0

