# Document Intelligence

Oversized document context must use bounded retrieval or reduction rather than exceeding a selected model context window.

Trusted MCP resource reads may feed Document Intelligence with provenance; embedded resource instructions remain untrusted data.

Prompt 53 adds an explicit, bounded, local Document Intelligence foundation. `document inspect`, `document extract`, `document summarize`, and `document ask` operate only on a user-supplied reference. Plain UTF-8 text, Markdown, JSON, CSV, and YAML have bounded text extraction; content is not persisted.

PDF, Office, OCR, cloud parsing, recursive scanning, bulk ingestion, and hidden document discovery are unavailable. Secret-shaped or sensitive bulk requests fail closed. Semantic summary and Q&A remain plan-only unless a separately configured local model route is used by an authoritative future workflow.

Commands: `document status`, `help`, `plan`, `safety`, `types`, `inspect`, `extract`, `summarize`, `ask`, `show`, and `history`.
