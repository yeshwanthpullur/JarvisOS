"""Document parser adapters with optional Docling/Marker and safe built-in fallbacks."""

from __future__ import annotations

from dataclasses import replace
from enum import StrEnum
import importlib.util
import io
import re
from typing import Callable, Protocol
from xml.etree import ElementTree
import zipfile

from .canonical import BlockType, CanonicalDocument, DocumentPage, DocumentProvenance, DocumentSection, DocumentTable, block


class ParserState(StrEnum): READY = "ready"; DEGRADED = "degraded"; UNAVAILABLE = "unavailable"; ERROR = "error"


class DocumentParser(Protocol):
    parser_id: str
    def detect(self) -> dict[str, object]: ...
    def supports(self, media_type: str) -> bool: ...
    def parse(self, document: CanonicalDocument, data: bytes, *, max_chars: int = 100_000) -> CanonicalDocument: ...
    def cancel(self) -> None: ...


ParserFunction = Callable[[bytes, str], dict[str, object]]


class StructuredParserAdapter:
    def __init__(self, parser_id: str, module_name: str, supported: tuple[str, ...], parser: ParserFunction | None = None) -> None:
        self.parser_id = parser_id; self.module_name = module_name; self.supported = supported; self.parser = parser; self.cancelled = False

    def detect(self) -> dict[str, object]:
        installed = importlib.util.find_spec(self.module_name) is not None
        ready = self.parser is not None
        return {"parser": self.parser_id, "installed": installed, "state": "ready" if ready else "degraded" if installed else "unavailable", "version": "injected_test_adapter" if self.parser else "detected_adapter_unconfigured" if installed else "not_installed"}
    def health(self) -> dict[str, object]: return self.detect()
    def supports(self, media_type: str) -> bool: return media_type in self.supported
    def cancel(self) -> None: self.cancelled = True
    def parse(self, document: CanonicalDocument, data: bytes, *, max_chars: int = 100_000) -> CanonicalDocument:
        if self.cancelled: raise ValueError("parser_cancelled")
        if not self.supports(document.source.media_type): raise ValueError("unsupported_document_type")
        if self.parser is None: raise ValueError("parser_unavailable")
        try: raw = self.parser(data, document.source.media_type)
        except Exception as exc: raise ValueError("parser_failed") from exc
        blocks = []; sections = []; tables = []
        for index, item in enumerate(tuple(raw.get("blocks", ()))[:5000]):
            blocks.append(block(BlockType(str(item.get("type", "unknown"))), str(item.get("text", ""))[:max_chars], index, page=item.get("page"), backend=self.parser_id))
            if blocks[-1].block_type is BlockType.HEADING: sections.append(DocumentSection(f"section-{index}", blocks[-1].text, len(sections), (blocks[-1].block_id,)))
        for index, item in enumerate(tuple(raw.get("tables", ()))[:200]):
            tables.append(DocumentTable(f"table-{index}", tuple(tuple(str(cell)[:500] for cell in row[:50]) for row in item.get("rows", ())[:200]), index, item.get("page")))
        pages = tuple(DocumentPage(page, tuple(item.block_id for item in blocks if item.page_number == page), tuple(item.table_id for item in tables if item.page_number == page)) for page in sorted({item.page_number for item in blocks + tables if item.page_number}))
        return replace(document, pages=pages, sections=tuple(sections), blocks=tuple(blocks), tables=tuple(tables), provenance=(DocumentProvenance(document.source.source_id, self.parser_id, self.detect()["version"]),))


class DoclingAdapter(StructuredParserAdapter):
    def __init__(self, parser: ParserFunction | None = None) -> None: super().__init__("docling", "docling", ("application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation"), parser)


class MarkerAdapter(StructuredParserAdapter):
    def __init__(self, parser: ParserFunction | None = None) -> None: super().__init__("marker", "marker", ("application/pdf",), parser)


class BuiltinDocumentParser:
    parser_id = "builtin_safe"
    SUPPORTED = {"text/plain", "text/markdown", "application/json", "text/csv", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
    def detect(self) -> dict[str, object]: return {"parser": self.parser_id, "installed": True, "state": "ready", "version": "1"}
    def health(self) -> dict[str, object]: return self.detect()
    def supports(self, media_type: str) -> bool: return media_type in self.SUPPORTED
    def cancel(self) -> None: pass
    def parse(self, document: CanonicalDocument, data: bytes, *, max_chars: int = 100_000) -> CanonicalDocument:
        media = document.source.media_type
        if not data: raise ValueError("document_empty")
        if media == "application/pdf": return self._pdf(document, data, max_chars)
        if "wordprocessingml" in media: return self._office(document, data, "word/document.xml", max_chars, "docx")
        if "presentationml" in media: return self._pptx(document, data, max_chars)
        text = data.decode("utf-8", errors="replace")[:max_chars]
        blocks = tuple(block(BlockType.HEADING if line.startswith("#") else BlockType.PARAGRAPH, line.lstrip("# "), index, backend=self.parser_id) for index, line in enumerate(text.splitlines()) if line.strip())
        return replace(document, blocks=blocks, sections=tuple(DocumentSection(f"section-{i}", b.text, i, (b.block_id,)) for i,b in enumerate(blocks) if b.block_type is BlockType.HEADING), provenance=(DocumentProvenance(document.source.source_id, self.parser_id, "1"),))
    def _pdf(self, document: CanonicalDocument, data: bytes, max_chars: int) -> CanonicalDocument:
        if b"/Encrypt" in data: raise ValueError("document_encrypted")
        text = data.decode("latin-1", errors="ignore")
        matches = [value.replace("\\(", "(").replace("\\)", ")") for value in re.findall(r"\((.*?)(?<!\\)\)\s*T[Jj]", text, flags=re.S)]
        if not matches: raise ValueError("parser_failed")
        blocks = tuple(block(BlockType.PARAGRAPH, value[:max_chars], i, page=1, backend=self.parser_id) for i,value in enumerate(matches))
        return replace(document, pages=(DocumentPage(1, tuple(item.block_id for item in blocks)),), blocks=blocks, provenance=(DocumentProvenance(document.source.source_id, self.parser_id, "1", "Optional structured parsers unavailable."),))
    def _office(self, document: CanonicalDocument, data: bytes, member: str, max_chars: int, kind: str) -> CanonicalDocument:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive: xml = archive.read(member)
            root = ElementTree.fromstring(xml)
        except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc: raise ValueError("document_malformed") from exc
        paragraphs=[]; tables=[]
        for element in root.iter():
            local = element.tag.rsplit("}",1)[-1]
            if local in {"p", "tr"}:
                cells=[] if local == "tr" else None
                if cells is not None:
                    for child in element:
                        if child.tag.rsplit("}",1)[-1] == "tc": cells.append(" ".join(t.text or "" for t in child.iter() if t.tag.rsplit("}",1)[-1] == "t"))
                    if cells: tables.append(tuple(cells))
                else:
                    value=" ".join(t.text or "" for t in element.iter() if t.tag.rsplit("}",1)[-1] == "t").strip()
                    if value: paragraphs.append(value)
        blocks=tuple(block(BlockType.PARAGRAPH, value, i, backend=kind) for i,value in enumerate(paragraphs))
        table_items=(DocumentTable("table-0", tuple(tables), len(blocks)),) if tables else ()
        return replace(document, blocks=blocks, tables=table_items, provenance=(DocumentProvenance(document.source.source_id, kind, "builtin_zip_xml"),))
    def _pptx(self, document: CanonicalDocument, data: bytes, max_chars: int) -> CanonicalDocument:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                members=sorted(name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name))
                xmls=[archive.read(name) for name in members]
        except zipfile.BadZipFile as exc: raise ValueError("document_malformed") from exc
        blocks=[]; pages=[]
        for page, xml in enumerate(xmls,1):
            try: root=ElementTree.fromstring(xml)
            except ElementTree.ParseError as exc: raise ValueError("document_malformed") from exc
            refs=[]
            for node in root.iter():
                if node.tag.rsplit("}",1)[-1] == "t" and (node.text or "").strip():
                    item=block(BlockType.PARAGRAPH, node.text or "", len(blocks), page=page, backend="pptx"); blocks.append(item); refs.append(item.block_id)
            pages.append(DocumentPage(page, tuple(refs)))
        return replace(document, pages=tuple(pages), blocks=tuple(blocks), provenance=(DocumentProvenance(document.source.source_id, "pptx", "builtin_zip_xml"),))


class ParserRegistry:
    def __init__(self, parsers: tuple[DocumentParser, ...] = ()) -> None: self.parsers = {item.parser_id:item for item in parsers}
    def get(self, parser_id: str) -> DocumentParser | None: return self.parsers.get(parser_id)
    def status(self) -> tuple[dict[str, object], ...]: return tuple(self.parsers[key].detect() for key in sorted(self.parsers))
