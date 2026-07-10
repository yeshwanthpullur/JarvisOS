"""Knowledge update preparation for research findings."""

from __future__ import annotations

import logging


class KnowledgeBuilder:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("knowledge_builder_initialized")

    def prepare_updates(self, findings: tuple[str, ...]) -> dict[str, object]:
        self._ensure_initialized()
        return {"findings": findings, "relationships": (), "metadata": {}}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("KnowledgeBuilder must be initialized before use.")
