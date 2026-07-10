"""Facade for Obsidian-specific vault and note operations."""

from __future__ import annotations

import logging
from pathlib import Path

from brain.backlink_manager import BacklinkManager
from brain.frontmatter_manager import FrontmatterManager
from brain.graph_manager import GraphManager
from brain.note_manager import NoteManager
from brain.search_manager import SearchManager
from brain.template_manager import TemplateManager
from brain.vault_manager import VaultManager, VaultStatus


class ObsidianManager:
    """Composes Obsidian vault, note, search, template, and graph managers."""

    def __init__(
        self,
        vault_path: Path,
        vault_name: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.frontmatter = FrontmatterManager()
        self.vault = VaultManager(vault_path, vault_name, logger=self._logger)
        self.backlinks = BacklinkManager(self.vault.vault_path)
        self.notes = NoteManager(
            self.vault.vault_path,
            frontmatter_manager=self.frontmatter,
            backlink_manager=self.backlinks,
            logger=self._logger,
        )
        self.search = SearchManager(
            self.vault.vault_path,
            frontmatter_manager=self.frontmatter,
            backlink_manager=self.backlinks,
            logger=self._logger,
        )
        self.templates = TemplateManager(self.vault.folder_path("Templates"))
        self.graph = GraphManager(
            self.vault.vault_path,
            backlink_manager=self.backlinks,
            logger=self._logger,
        )
        self.initialized = False

    def initialize(self, create_if_missing: bool = False) -> VaultStatus:
        """Initialize the Obsidian vault connection."""
        status = self.vault.connect(create_if_missing=create_if_missing)
        self.initialized = status.connected
        if not status.connected:
            self._logger.warning(
                "obsidian_manager_unavailable path=%s",
                status.vault_path,
            )
        return status
