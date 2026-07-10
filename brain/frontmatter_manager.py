"""Frontmatter parsing and serialization for Obsidian notes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_text() -> str:
    """Return the current UTC timestamp as ISO text."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class NoteFrontmatter:
    """Standard frontmatter supported by generated Brain notes."""

    uuid: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    created: str = field(default_factory=utc_now_text)
    updated: str = field(default_factory=utc_now_text)
    type: str = "note"
    tags: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    status: str = "active"
    importance: int = 1
    source: str = "jarvis"
    project_id: str | None = None
    task_id: str | None = None
    memory_id: str | None = None
    knowledge_id: str | None = None
    related_notes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return frontmatter as a plain dictionary."""
        return {
            "uuid": self.uuid,
            "title": self.title,
            "created": self.created,
            "updated": self.updated,
            "type": self.type,
            "tags": list(self.tags),
            "aliases": list(self.aliases),
            "status": self.status,
            "importance": self.importance,
            "source": self.source,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "memory_id": self.memory_id,
            "knowledge_id": self.knowledge_id,
            "related_notes": list(self.related_notes),
            "metadata": self.metadata,
        }


class FrontmatterManager:
    """Reads and writes a small YAML-compatible frontmatter subset."""

    def create(
        self,
        title: str,
        note_type: str,
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
    ) -> NoteFrontmatter:
        """Create standard note frontmatter."""
        return NoteFrontmatter(
            title=title,
            type=note_type,
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
            metadata=dict(metadata or {}),
        )

    def split(self, markdown: str) -> tuple[dict[str, Any], str]:
        """Split frontmatter and body from Markdown text."""
        if not markdown.startswith("---\n"):
            return {}, markdown

        marker = "\n---\n"
        end = markdown.find(marker, 4)
        if end == -1:
            return {}, markdown

        raw = markdown[4:end]
        body = markdown[end + len(marker) :]
        if body.startswith("\n"):
            body = body[1:]
        return self.parse(raw), body

    def parse(self, raw_frontmatter: str) -> dict[str, Any]:
        """Parse simple key-value frontmatter."""
        parsed: dict[str, Any] = {}
        for raw_line in raw_frontmatter.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip()] = self._parse_value(value.strip())
        return parsed

    def render(self, frontmatter: NoteFrontmatter | dict[str, Any]) -> str:
        """Render frontmatter as deterministic Markdown text."""
        data = (
            frontmatter.to_dict()
            if isinstance(frontmatter, NoteFrontmatter)
            else dict(frontmatter)
        )
        lines = ["---"]
        for key, value in data.items():
            lines.append(f"{key}: {self._render_value(value)}")
        lines.append("---")
        return "\n".join(lines) + "\n\n"

    def merge_into_markdown(
        self,
        markdown: str,
        updates: dict[str, Any],
    ) -> str:
        """Merge frontmatter updates into existing Markdown."""
        current, body = self.split(markdown)
        current.update(updates)
        current["updated"] = utc_now_text()
        return self.render(current) + body.lstrip("\n")

    def _parse_value(self, value: str) -> Any:
        if value in {"null", "None", ""}:
            return None
        if value in {"true", "false"}:
            return value == "true"
        if value.startswith("[") or value.startswith("{"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        try:
            return int(value)
        except ValueError:
            return value.strip('"')

    def _render_value(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (list, tuple, dict)):
            return json.dumps(value, sort_keys=True)
        if isinstance(value, int):
            return str(value)
        text = str(value)
        if any(character in text for character in (":", "#", "[", "]", "{", "}")):
            return json.dumps(text)
        return text
