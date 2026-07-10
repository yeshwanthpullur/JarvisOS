"""Core Markdown note management for the Obsidian Brain layer."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain.backlink_manager import BacklinkManager
from brain.frontmatter_manager import FrontmatterManager, NoteFrontmatter, utc_now_text
from brain.markdown_exporter import MarkdownExporter
from brain.search_manager import NoteSearchResult, SearchManager


@dataclass(frozen=True, slots=True)
class BrainNote:
    """A human-readable Markdown note in the Brain vault."""

    path: Path
    title: str
    content: str
    frontmatter: dict[str, Any]


class NoteManager:
    """Creates, reads, updates, moves, deletes, and searches Markdown notes."""

    def __init__(
        self,
        vault_path: Path,
        frontmatter_manager: FrontmatterManager | None = None,
        backlink_manager: BacklinkManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._vault_path = vault_path
        self._frontmatter = frontmatter_manager or FrontmatterManager()
        self._backlinks = backlink_manager or BacklinkManager(vault_path)
        self._exporter = MarkdownExporter(self._frontmatter)
        self._search = SearchManager(vault_path, self._frontmatter, self._backlinks)
        self._logger = logger or logging.getLogger(__name__)

    def create_note(
        self,
        title: str,
        body: str = "",
        folder: str = "Ideas",
        note_type: str = "note",
        tags: tuple[str, ...] = (),
        aliases: tuple[str, ...] = (),
        status: str = "active",
        importance: int = 1,
        source: str = "jarvis",
        project_id: str | None = None,
        task_id: str | None = None,
        memory_id: str | None = None,
        knowledge_id: str | None = None,
        related_notes: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> BrainNote:
        """Create a Markdown note with standard frontmatter."""
        path = self._note_path(folder, title)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Brain note already exists: {path}")

        frontmatter = self._frontmatter.create(
            title=title,
            note_type=note_type,
            tags=tags,
            aliases=aliases,
            status=status,
            importance=importance,
            source=source,
            project_id=project_id,
            task_id=task_id,
            memory_id=memory_id,
            knowledge_id=knowledge_id,
            related_notes=related_notes,
            metadata=metadata,
        )
        markdown = self._exporter.render_note(frontmatter, body)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        self._logger.info("brain_note_created path=%s type=%s", path, note_type)
        return self.read_note(path)

    def note_path(self, folder: str, title: str) -> Path:
        """Return the expected path for a note title in a vault folder."""
        return self._note_path(folder, title)

    def read_note(self, path: Path) -> BrainNote:
        """Read a Markdown note."""
        resolved = self._resolve_vault_path(path)
        markdown = resolved.read_text(encoding="utf-8")
        frontmatter, body = self._frontmatter.split(markdown)
        return BrainNote(
            path=resolved,
            title=str(frontmatter.get("title") or resolved.stem),
            content=body,
            frontmatter=frontmatter,
        )

    def update_note(
        self,
        path: Path,
        body: str | None = None,
        frontmatter_updates: dict[str, Any] | None = None,
    ) -> BrainNote:
        """Update note content and/or frontmatter."""
        resolved = self._resolve_vault_path(path)
        current = resolved.read_text(encoding="utf-8")
        frontmatter, existing_body = self._frontmatter.split(current)
        frontmatter.update(frontmatter_updates or {})
        frontmatter["updated"] = utc_now_text()
        new_body = existing_body if body is None else body
        resolved.write_text(
            self._frontmatter.render(frontmatter) + new_body.lstrip("\n"),
            encoding="utf-8",
        )
        self._logger.info("brain_note_updated path=%s", resolved)
        return self.read_note(resolved)

    def delete_note(self, path: Path) -> bool:
        """Delete a Markdown note."""
        resolved = self._resolve_vault_path(path)
        if not resolved.exists():
            self._logger.warning("brain_note_delete_missing path=%s", resolved)
            return False
        resolved.unlink()
        self._logger.info("brain_note_deleted path=%s", resolved)
        return True

    def rename_note(self, path: Path, new_title: str) -> BrainNote:
        """Rename a note file and update its title frontmatter."""
        resolved = self._resolve_vault_path(path)
        target = resolved.with_name(f"{self._slugify(new_title)}.md")
        resolved.rename(target)
        self._logger.info("brain_note_renamed old_path=%s new_path=%s", resolved, target)
        return self.update_note(target, frontmatter_updates={"title": new_title})

    def move_note(self, path: Path, target_folder: str) -> BrainNote:
        """Move a note into another vault folder."""
        resolved = self._resolve_vault_path(path)
        target_dir = self._vault_path / target_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / resolved.name
        resolved.rename(target)
        self._logger.info("brain_note_moved old_path=%s new_path=%s", resolved, target)
        return self.read_note(target)

    def search_notes(self, query: str, limit: int = 20) -> tuple[NoteSearchResult, ...]:
        """Search notes by title, Markdown content, tags, links, and metadata."""
        return self._search.search(query, limit=limit)

    def create_wiki_link(self, title: str, alias: str | None = None) -> str:
        """Create a wiki link for note content."""
        return self._backlinks.create_wiki_link(title, alias=alias)

    def resolve_wiki_link(self, title: str) -> Path | None:
        """Resolve a wiki link title to a note path."""
        return self._backlinks.resolve_wiki_link(title)

    def read_backlinks(self, title: str) -> tuple[Path, ...]:
        """Return note paths that link to a title."""
        return self._backlinks.read_backlinks(title)

    def read_frontmatter(self, path: Path) -> dict[str, Any]:
        """Read note frontmatter."""
        return self.read_note(path).frontmatter

    def write_frontmatter(self, path: Path, updates: dict[str, Any]) -> BrainNote:
        """Merge frontmatter updates into a note."""
        return self.update_note(path, frontmatter_updates=updates)

    def _note_path(self, folder: str, title: str) -> Path:
        return self._vault_path / folder / f"{self._slugify(title)}.md"

    def _resolve_vault_path(self, path: Path) -> Path:
        candidate = path if path.is_absolute() else self._vault_path / path
        resolved = candidate.resolve()
        vault = self._vault_path.resolve()
        if resolved != vault and vault not in resolved.parents:
            raise ValueError(f"Path is outside the Brain vault: {path}")
        return resolved

    def _slugify(self, title: str) -> str:
        cleaned = re.sub(r"[^\w\s.-]", "", title, flags=re.UNICODE).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned or "Untitled"
