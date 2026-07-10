"""Markdown template support for Brain notes."""

from __future__ import annotations

from pathlib import Path
from string import Template


class TemplateManager:
    """Stores and renders simple Markdown templates."""

    def __init__(self, templates_path: Path) -> None:
        self._templates_path = templates_path
        self._templates_path.mkdir(parents=True, exist_ok=True)

    def save_template(self, name: str, content: str) -> Path:
        """Save a Markdown template."""
        path = self._template_path(name)
        path.write_text(content, encoding="utf-8")
        return path

    def read_template(self, name: str) -> str:
        """Read a Markdown template."""
        return self._template_path(name).read_text(encoding="utf-8")

    def render_template(self, name: str, values: dict[str, object]) -> str:
        """Render a template using safe string substitution."""
        template = Template(self.read_template(name))
        return template.safe_substitute({key: str(value) for key, value in values.items()})

    def _template_path(self, name: str) -> Path:
        clean_name = name.strip().removesuffix(".md") or "template"
        return self._templates_path / f"{clean_name}.md"
