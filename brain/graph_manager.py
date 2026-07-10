"""Relationship graph hooks for the Obsidian Brain layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from brain.backlink_manager import BacklinkManager


@dataclass(frozen=True, slots=True)
class NoteRelationship:
    """A relationship between two notes or external structured records."""

    source: str
    target: str
    relationship_type: str
    metadata: dict[str, object]


class GraphManager:
    """Stores note relationships for future graph visualization."""

    def __init__(
        self,
        vault_path: Path,
        backlink_manager: BacklinkManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._vault_path = vault_path
        self._backlinks = backlink_manager or BacklinkManager(vault_path)
        self._relationships: list[NoteRelationship] = []
        self._logger = logger or logging.getLogger(__name__)

    def add_relationship(
        self,
        source: str,
        target: str,
        relationship_type: str,
        metadata: dict[str, object] | None = None,
    ) -> NoteRelationship:
        """Record a relationship without rendering a graph."""
        relationship = NoteRelationship(
            source=source,
            target=target,
            relationship_type=relationship_type,
            metadata=dict(metadata or {}),
        )
        self._relationships.append(relationship)
        self._logger.info(
            "brain_relationship_recorded source=%s target=%s type=%s",
            source,
            target,
            relationship_type,
        )
        return relationship

    def relationships(self) -> tuple[NoteRelationship, ...]:
        """Return explicitly recorded note relationships."""
        return tuple(self._relationships)

    def wiki_link_edges(self) -> tuple[NoteRelationship, ...]:
        """Return note-to-note edges inferred from wiki links."""
        if not self._vault_path.exists():
            return ()
        edges: list[NoteRelationship] = []
        for path in self._vault_path.rglob("*.md"):
            markdown = path.read_text(encoding="utf-8")
            for target in self._backlinks.extract_wiki_links(markdown):
                edges.append(
                    NoteRelationship(
                        source=path.stem,
                        target=target,
                        relationship_type="wiki_link",
                        metadata={"path": str(path)},
                    )
                )
        return tuple(edges)
