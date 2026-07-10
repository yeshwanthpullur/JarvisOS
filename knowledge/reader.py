"""Knowledge source reader."""

from __future__ import annotations

import logging
from pathlib import Path

from knowledge.metadata import MetadataExtractor
from knowledge.parser import DocumentParser
from knowledge.document import ParsedDocument


class KnowledgeReader:
    """Reads local files into parsed document envelopes."""

    def __init__(
        self,
        parser: DocumentParser | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._parser = parser or DocumentParser()
        self._metadata = metadata_extractor or MetadataExtractor()
        self._logger = logger or logging.getLogger(__name__)

    def read_file(self, path: Path) -> ParsedDocument:
        """Read a supported local file."""
        resolved = path.expanduser().resolve()
        if not resolved.exists() or not resolved.is_file():
            raise FileNotFoundError(f"Knowledge source not found: {resolved}")

        document_type = self._metadata.detect_type(resolved)
        content = self._parser.parse(resolved, document_type)
        parsed = self._metadata.build_parsed_document(
            resolved,
            content,
            metadata={"parser": "standard-library"},
        )
        self._logger.info(
            "knowledge_file_read path=%s type=%s",
            resolved,
            parsed.document_type.value,
        )
        return parsed

