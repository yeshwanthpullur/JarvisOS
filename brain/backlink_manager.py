"""Wiki link and backlink management for Brain notes."""

from __future__ import annotations

import re
from pathlib import Path


WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


class BacklinkManager:
    """Creates and resolves Obsidian wiki links."""

    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path

    def create_wiki_link(self, title: str, alias: str | None = None) -> str:
        """Create an Obsidian wiki link."""
        clean_title = title.strip()
        if alias:
            return f"[[{clean_title}|{alias.strip()}]]"
        return f"[[{clean_title}]]"

    def extract_wiki_links(self, markdown: str) -> tuple[str, ...]:
        """Return wiki link targets found in Markdown."""
        return tuple(match.group(1).strip() for match in WIKI_LINK_PATTERN.finditer(markdown))

    def resolve_wiki_link(self, title: str) -> Path | None:
        """Resolve a wiki link target to a note path by stem or title frontmatter."""
        normalized = title.strip().lower()
        if not self._vault_path.exists():
            return None
        for path in self._vault_path.rglob("*.md"):
            if path.stem.lower() == normalized:
                return path
        return None

    def read_backlinks(self, target_title: str) -> tuple[Path, ...]:
        """Return notes that link to the requested title."""
        normalized = target_title.strip().lower()
        backlinks: list[Path] = []
        if not self._vault_path.exists():
            return ()
        for path in self._vault_path.rglob("*.md"):
            links = self.extract_wiki_links(path.read_text(encoding="utf-8"))
            if any(link.lower() == normalized for link in links):
                backlinks.append(path)
        return tuple(backlinks)
