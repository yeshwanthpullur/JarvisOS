"""Agent logger factory."""

from __future__ import annotations

import logging


class AgentLoggerFactory:
    """Creates namespaced agent loggers."""

    def get_logger(self, agent_id: str) -> logging.Logger:
        """Return a logger for an agent."""
        return logging.getLogger(f"agents.{agent_id}")
