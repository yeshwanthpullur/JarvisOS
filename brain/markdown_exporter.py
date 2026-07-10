"""Markdown rendering helpers for Brain notes."""

from __future__ import annotations

from brain.frontmatter_manager import FrontmatterManager, NoteFrontmatter


class MarkdownExporter:
    """Builds Markdown documents with standard frontmatter."""

    def __init__(self, frontmatter_manager: FrontmatterManager | None = None) -> None:
        self._frontmatter = frontmatter_manager or FrontmatterManager()

    def render_note(self, frontmatter: NoteFrontmatter, body: str) -> str:
        """Render a complete Markdown note."""
        title = frontmatter.title.strip()
        heading = f"# {title}\n\n" if title else ""
        return self._frontmatter.render(frontmatter) + heading + body.strip() + "\n"
