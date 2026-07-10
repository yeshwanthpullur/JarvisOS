"""Conversation logger factory."""

from __future__ import annotations

import logging


class ConversationLogger:
    """Provides conversation loggers."""

    initialized = True

    def get_logger(self) -> logging.Logger:
        """Return conversation logger."""
        return logging.getLogger("conversation")

