"""Logger factory for Executive JARVIS."""

from __future__ import annotations

import logging


class JarvisLogger:
    """Provides loggers under the jarvis namespace."""

    initialized = True

    def get_logger(self, name: str = "executive") -> logging.Logger:
        """Return a configured child logger."""
        return logging.getLogger(f"jarvis.{name}")

