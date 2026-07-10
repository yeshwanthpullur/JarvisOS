"""Obsidian vault management for the JARVIS OS Brain layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path


REQUIRED_VAULT_FOLDERS = (
    "Daily Notes",
    "Knowledge",
    "Projects",
    "Research",
    "Skills",
    "Conversations",
    "Ideas",
    "Tasks",
    "Logs",
    "Prompts",
    "Architecture",
    "Decisions",
    "Attachments",
    "Templates",
)


@dataclass(frozen=True, slots=True)
class VaultStatus:
    """Current connection details for the configured Obsidian vault."""

    vault_name: str
    vault_path: Path
    exists: bool
    connected: bool
    total_notes: int
    required_folders: tuple[str, ...]


class VaultManager:
    """Verifies and prepares an Obsidian-compatible Markdown vault."""

    def __init__(
        self,
        vault_path: Path,
        vault_name: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self.vault_path = vault_path.expanduser()
        self.vault_name = vault_name
        self._logger = logger or logging.getLogger(__name__)

    def connect(self, create_if_missing: bool = False) -> VaultStatus:
        """Connect to the vault and optionally create it when missing."""
        exists = self.vault_path.exists()
        if not exists and create_if_missing:
            self.create_vault()
            exists = True
        elif not exists:
            self._logger.warning("obsidian_vault_missing path=%s", self.vault_path)

        if exists:
            self.ensure_required_folders()

        status = self.status()
        self._logger.info(
            "obsidian_vault_connected name=%s path=%s connected=%s",
            status.vault_name,
            status.vault_path,
            status.connected,
        )
        return status

    def create_vault(self) -> None:
        """Create the vault directory."""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self._logger.info("obsidian_vault_created path=%s", self.vault_path)

    def ensure_required_folders(self) -> None:
        """Create all standard Brain folders inside the vault."""
        for folder in REQUIRED_VAULT_FOLDERS:
            path = self.folder_path(folder)
            path.mkdir(parents=True, exist_ok=True)
            self._logger.debug("obsidian_vault_folder_verified path=%s", path)

    def folder_path(self, folder: str) -> Path:
        """Return an absolute path for a vault folder."""
        return self.vault_path / folder

    def note_count(self) -> int:
        """Return the number of Markdown notes in the vault."""
        if not self.vault_path.exists():
            return 0
        return sum(1 for path in self.vault_path.rglob("*.md") if path.is_file())

    def status(self) -> VaultStatus:
        """Return current vault connection status."""
        exists = self.vault_path.exists() and self.vault_path.is_dir()
        return VaultStatus(
            vault_name=self.vault_name,
            vault_path=self.vault_path,
            exists=exists,
            connected=exists,
            total_notes=self.note_count(),
            required_folders=REQUIRED_VAULT_FOLDERS,
        )
