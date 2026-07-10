"""Option generation."""

from __future__ import annotations

import logging


class OptionGenerator:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("option_generator_initialized")

    def generate(self, objective: str) -> tuple[str, ...]:
        self._ensure_initialized()
        return (
            f"best:{objective}",
            f"fastest:{objective}",
            f"lowest_cost:{objective}",
            f"lowest_risk:{objective}",
            f"highest_quality:{objective}",
            f"local:{objective}",
            f"cloud:{objective}",
            f"hybrid:{objective}",
            f"user_preferred:{objective}",
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("OptionGenerator must be initialized before use.")
