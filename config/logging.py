"""Application logging configuration."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path

from config.settings import AppSettings


def configure_logging(settings: AppSettings) -> None:
    """Configure structured, file-backed application logging."""
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = settings.logging.log_dir / settings.logging.log_file

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": settings.log_level,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "standard",
                    "level": settings.log_level,
                    "filename": str(Path(log_path)),
                    "maxBytes": settings.logging.max_bytes,
                    "backupCount": settings.logging.backup_count,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": settings.log_level,
            },
        }
    )
