"""Metadata extraction for local knowledge sources."""

from __future__ import annotations

from pathlib import Path

from knowledge.document import DocumentType, ParsedDocument


EXTENSION_TYPES: dict[str, DocumentType] = {
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
    ".txt": DocumentType.TXT,
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".html": DocumentType.HTML,
    ".htm": DocumentType.HTML,
    ".json": DocumentType.JSON,
    ".csv": DocumentType.CSV,
    ".py": DocumentType.PYTHON,
}


class MetadataExtractor:
    """Extracts file metadata without interpreting document content."""

    def detect_type(self, path: Path) -> DocumentType:
        """Detect a document type from its extension."""
        return EXTENSION_TYPES.get(path.suffix.lower(), DocumentType.UNKNOWN)

    def title_for_path(self, path: Path) -> str:
        """Return a human-readable title for a path."""
        return path.stem.replace("_", " ").replace("-", " ").strip() or path.name

    def build_parsed_document(
        self,
        path: Path,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> ParsedDocument:
        """Create a parsed document envelope from file metadata and text."""
        stat = path.stat()
        document_type = self.detect_type(path)
        return ParsedDocument(
            title=self.title_for_path(path),
            path=path,
            document_type=document_type,
            content=content,
            created_at=self._datetime_from_timestamp(stat.st_ctime),
            modified_at=self._datetime_from_timestamp(stat.st_mtime),
            author=None,
            language="python" if document_type is DocumentType.PYTHON else "en",
            metadata={
                "size_bytes": stat.st_size,
                "extension": path.suffix.lower(),
                **dict(metadata or {}),
            },
        )

    def _datetime_from_timestamp(self, value: float):
        from datetime import datetime, timezone

        return datetime.fromtimestamp(value, tz=timezone.utc)

