"""Logger helpers for Agent Creator."""

from __future__ import annotations

import logging


class AgentCreatorLoggerFactory:
    """Creates namespaced loggers for creator components."""

    def get_logger(self, name: str) -> logging.Logger:
        """Return a component logger."""
        return logging.getLogger(f"agent_creator.{name}")

