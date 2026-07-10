"""Command logger factory."""

from __future__ import annotations

import logging


class CommandLogger:
    """Provides command logger."""

    initialized = True

    def get_logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger("commands")

