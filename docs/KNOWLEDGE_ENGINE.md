# Knowledge Engine

The Knowledge Engine imports local files into structured, searchable knowledge.

It currently supports:

- Markdown
- TXT
- PDF, using best-effort standard-library text extraction
- DOCX, using standard-library ZIP/XML parsing
- HTML
- JSON
- CSV
- Python files

Future source types include YouTube, GitHub, images, videos, and audio.

## Responsibilities

- Read files through `KnowledgeReader`.
- Extract metadata through `MetadataExtractor`.
- Parse file content through `DocumentParser`.
- Create `KnowledgeDocument` objects.
- Create searchable `KnowledgeChunk` objects.
- Store documents and chunks in SQLite through `KnowledgeStore`.
- Link imported documents to Memory Engine records through `RelationshipBuilder`.
- Expose future summarization through `KnowledgeSummarizer`.

## Non-Goals

The current implementation does not perform AI summarization, embeddings, semantic search, OCR, audio transcription, video analysis, or remote fetching.

## Startup

The application initializes `KnowledgeManager` after `MemoryManager`, so imported documents can be linked to memory records. The startup summary displays `Knowledge Engine Ready` with document and chunk counts.

## Retrieval

The Retrieval Engine may query the Knowledge Engine, but it does not change storage behavior. Knowledge remains the storage and indexing layer, while retrieval decides how to select the exact knowledge needed for a request.

The Research Intelligence layer can prepare knowledge updates and learning plans from findings, but it does not replace the Knowledge Engine or duplicate storage.

The Research Intelligence layer can prepare knowledge updates and learning plans from findings, but it does not replace the Knowledge Engine or duplicate storage.
