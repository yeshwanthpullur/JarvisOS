"""Markdown search support for the Obsidian Brain layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain.backlink_manager import BacklinkManager
from brain.frontmatter_manager import FrontmatterManager


@dataclass(frozen=True, slots=True)
class NoteSearchResult:
    """Single Brain note search result."""

    path: Path
    title: str
    matches: tuple[str, ...]
    frontmatter: dict[str, Any]


class SearchManager:
    """Searches note titles, content, tags, links, backlinks, and metadata."""

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
        self._logger = logger or logging.getLogger(__name__)

    def search(self, query: str, limit: int = 20) -> tuple[NoteSearchResult, ...]:
        """Search all Markdown notes for a query."""
        normalized = query.strip().lower()
        if not normalized or not self._vault_path.exists():
            return ()

        results: list[NoteSearchResult] = []
        for path in self._vault_path.rglob("*.md"):
            markdown = path.read_text(encoding="utf-8")
            frontmatter, body = self._frontmatter.split(markdown)
            title = str(frontmatter.get("title") or path.stem)
            haystacks = {
                "title": title,
                "content": body,
                "tags": " ".join(str(tag) for tag in frontmatter.get("tags") or ()),
                "frontmatter": str(frontmatter),
                "wiki_links": " ".join(self._backlinks.extract_wiki_links(markdown)),
                "metadata": str(frontmatter.get("metadata") or {}),
            }
            matches = tuple(
                name for name, value in haystacks.items() if normalized in value.lower()
            )
            if matches:
                results.append(
                    NoteSearchResult(
                        path=path,
                        title=title,
                        matches=matches,
                        frontmatter=frontmatter,
                    )
                )
            if len(results) >= limit:
                break

        self._logger.info("brain_note_search query=%s count=%s", query, len(results))
        return tuple(results)
