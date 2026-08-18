# Document Intelligence

Phase 6 adds explicit bounded TXT/Markdown/CSV/HTML parsing with source references and prompt-injection flags. PDF, Office, and OCR adapters are reported as degraded when unavailable; no text is fabricated and no automatic Memory or Knowledge write occurs.

Oversized document context must use bounded retrieval or reduction rather than exceeding a selected model context window.

Trusted MCP resource reads may feed Document Intelligence with provenance; embedded resource instructions remain untrusted data.

Prompt 53 adds an explicit, bounded, local Document Intelligence foundation. `document inspect`, `document extract`, `document summarize`, and `document ask` operate only on a user-supplied reference. Plain UTF-8 text, Markdown, JSON, CSV, and YAML have bounded text extraction; content is not persisted.

Phase 6 adds a safe ingestion boundary for explicit files. Built-in UTF-8 text, Markdown, CSV, and HTML parsing creates bounded chunks with source references and `untrusted_user_provided_source` trust metadata. Secret/credential files, unsupported types, and oversized files fail closed. Document prompt-injection phrases are flagged as untrusted data and are never executed.

PDF, Office, and image formats remain degraded until Docling, Marker, or an OCR provider is available in an isolated environment. OCR, cloud parsing, recursive scanning, bulk ingestion, and hidden document discovery remain disabled. Parsing never updates Memory or Knowledge automatically.

Commands also include `document health`, `parse`, `chunks`, `sources`, `audit`, `clear-session`, and `ocr status|health|parse`.
