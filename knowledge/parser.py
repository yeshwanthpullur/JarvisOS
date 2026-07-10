"""Document parsers for the Knowledge Engine."""

from __future__ import annotations

import csv
import json
import re
import zipfile
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from xml.etree import ElementTree

from knowledge.document import DocumentType


class _HTMLTextExtractor(HTMLParser):
    """Minimal HTML-to-text extractor."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        """Return extracted text."""
        return "\n".join(self.parts)


class DocumentParser:
    """Parses supported local document files into plain text."""

    def parse(self, path: Path, document_type: DocumentType) -> str:
        """Parse a path according to its document type."""
        if document_type in {
            DocumentType.MARKDOWN,
            DocumentType.TXT,
            DocumentType.PYTHON,
        }:
            return path.read_text(encoding="utf-8", errors="replace")
        if document_type is DocumentType.JSON:
            return self._parse_json(path)
        if document_type is DocumentType.CSV:
            return self._parse_csv(path)
        if document_type is DocumentType.HTML:
            return self._parse_html(path)
        if document_type is DocumentType.DOCX:
            return self._parse_docx(path)
        if document_type is DocumentType.PDF:
            return self._parse_pdf_best_effort(path)
        return path.read_text(encoding="utf-8", errors="replace")

    def _parse_json(self, path: Path) -> str:
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, indent=2, sort_keys=True)

    def _parse_csv(self, path: Path) -> str:
        output = StringIO()
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                output.write(" | ".join(row))
                output.write("\n")
        return output.getvalue()

    def _parse_html(self, path: Path) -> str:
        parser = _HTMLTextExtractor()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        return parser.text()

    def _parse_docx(self, path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            xml_content = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml_content)
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs: list[str] = []
        for paragraph in root.iter(f"{namespace}p"):
            text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
            if text.strip():
                paragraphs.append(text)
        return "\n".join(paragraphs)

    def _parse_pdf_best_effort(self, path: Path) -> str:
        raw = path.read_bytes()
        text = raw.decode("latin-1", errors="ignore")
        candidates = re.findall(r"\(([^()]*)\)", text)
        if candidates:
            return "\n".join(candidate.strip() for candidate in candidates if candidate.strip())
        return "".join(char if char.isprintable() else " " for char in text)

