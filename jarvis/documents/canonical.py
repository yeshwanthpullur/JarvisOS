"""Versioned canonical representation shared by document parsers and OCR."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = 1


class BlockType(StrEnum):
    HEADING = "heading"; PARAGRAPH = "paragraph"; LIST = "list"; LIST_ITEM = "list_item"
    TABLE = "table"; TABLE_CELL = "table_cell"; IMAGE = "image"; CAPTION = "caption"
    CODE = "code"; EQUATION = "equation"; FOOTNOTE = "footnote"; HEADER = "header"
    FOOTER = "footer"; OCR_TEXT = "ocr_text"; UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> "BlockType":
        del value
        return cls.UNKNOWN


def _bound(value: object, limit: int = 4000) -> str:
    text = str(value or "").replace("\x00", " ").strip()
    return text if len(text) <= limit else text[:limit - 3] + "..."


@dataclass(frozen=True, slots=True)
class DocumentSource:
    source_id: str
    display_name: str
    source_type: str
    media_type: str
    immutable_digest: str
    raw_reference: str


@dataclass(frozen=True, slots=True)
class DocumentProvenance:
    source_id: str
    backend: str
    backend_version: str = "unknown"
    fallback_reason: str = ""
    confidence: float | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("invalid_document_confidence")


@dataclass(frozen=True, slots=True)
class DocumentBlock:
    block_id: str
    block_type: BlockType
    text: str
    order: int
    page_number: int | None = None
    parent_ref: str = ""
    location_ref: str = ""
    confidence: float | None = None
    backend: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", _bound(self.text))
        if self.order < 0 or self.page_number is not None and self.page_number < 1: raise ValueError("invalid_document_block_location")


@dataclass(frozen=True, slots=True)
class DocumentTable:
    table_id: str
    rows: tuple[tuple[str, ...], ...]
    order: int
    page_number: int | None = None
    location_ref: str = ""

    def __post_init__(self) -> None:
        if len(self.rows) > 200 or any(len(row) > 50 for row in self.rows): raise ValueError("document_table_too_large")


@dataclass(frozen=True, slots=True)
class DocumentImage:
    image_id: str
    order: int
    page_number: int | None = None
    source_ref: str = ""
    caption: str = ""
    semantic_analysis: bool = False


@dataclass(frozen=True, slots=True)
class DocumentPage:
    page_number: int
    block_refs: tuple[str, ...] = ()
    table_refs: tuple[str, ...] = ()
    image_refs: tuple[str, ...] = ()
    native_text: bool = True


@dataclass(frozen=True, slots=True)
class DocumentSection:
    section_id: str
    title: str
    order: int
    block_refs: tuple[str, ...]
    parent_section_ref: str = ""


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    title: str = ""
    author: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    language: str | None = None
    encrypted: bool = False
    scanned: bool = False
    mixed_content: bool = False


@dataclass(frozen=True, slots=True)
class CanonicalDocument:
    document_id: str
    version_id: str
    source: DocumentSource
    metadata: DocumentMetadata
    pages: tuple[DocumentPage, ...]
    sections: tuple[DocumentSection, ...]
    blocks: tuple[DocumentBlock, ...]
    tables: tuple[DocumentTable, ...]
    images: tuple[DocumentImage, ...]
    provenance: tuple[DocumentProvenance, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION: raise ValueError("unsupported_document_schema")
        orders = [item.order for item in self.blocks]
        if orders != sorted(orders) or len(self.blocks) > 5000: raise ValueError("invalid_document_reading_order")

    @classmethod
    def create(cls, display_name: str, media_type: str, data: bytes, *, source_type: str = "explicit_local_file", raw_reference: str = "") -> "CanonicalDocument":
        document_id = f"document-{uuid4().hex[:12]}"; source_id = f"source-{uuid4().hex[:12]}"
        source = DocumentSource(source_id, _bound(display_name, 240), source_type, media_type, hashlib.sha256(data).hexdigest(), _bound(raw_reference or display_name, 240))
        return cls(document_id, f"version-{uuid4().hex[:12]}", source, DocumentMetadata(title=display_name), (), (), (), (), (), ())

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=True)

    @classmethod
    def from_json(cls, value: str) -> "CanonicalDocument":
        raw = json.loads(value); source = DocumentSource(**raw["source"]); metadata = DocumentMetadata(**raw["metadata"])
        pages = tuple(DocumentPage(**item) for item in raw["pages"]); sections = tuple(DocumentSection(**item) for item in raw["sections"])
        blocks = tuple(DocumentBlock(**{**item, "block_type": BlockType(item["block_type"])}) for item in raw["blocks"])
        tables = tuple(DocumentTable(**{**item, "rows": tuple(tuple(row) for row in item["rows"])}) for item in raw["tables"])
        images = tuple(DocumentImage(**item) for item in raw["images"]); provenance = tuple(DocumentProvenance(**item) for item in raw["provenance"])
        return cls(raw["document_id"], raw["version_id"], source, metadata, pages, sections, blocks, tables, images, provenance, raw["schema_version"])


def block(block_type: BlockType, text: str, order: int, *, page: int | None = None, backend: str = "") -> DocumentBlock:
    return DocumentBlock(f"block-{uuid4().hex[:12]}", block_type, text, order, page, location_ref=f"page:{page}" if page else f"order:{order}", backend=backend)
