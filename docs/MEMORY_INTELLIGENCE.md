# Memory Intelligence

Prompt 79 knowledge candidates are TTL-bound recommendations with provenance and `memory_write_allowed=false`. Promotion still requires explicit Persistent Memory authority.

Prompt 80 keeps external knowledge in a separate index. Retrieval and persistence never create or update authoritative user memory.

JARVIS OS keeps durable personal context in a local SQLite-backed memory engine. Prompt 38 adds a higher-level memory intelligence layer that makes that store usable from the CLI without turning it into a catch-all archive.

## What Works

- Explicit memory commands for status, help, list, search, show, remember, forget, update, archive, recent, preferences, projects, audit, cleanup, and consolidate.
- Bounded local retrieval for chat context.
- Safe automatic session summaries when enabled in configuration.
- Secret-aware storage policy that refuses obvious credential-like content.
- Bounded audit metadata without full transcript or prompt storage.

## What It Does Not Do

- It does not sync memory to any remote backend.
- It does not store hidden reasoning.
- It does not store raw secrets, credentials, or private environment values.
- It does not replace the authority of the command, conversation, or context engines.
- It does not let Mem0, Qdrant, ChromaDB, FAISS, Graphiti, or an embedding provider write authoritative memory directly.

## Phase 6 Retrieval Adapters

Mem0 is the planned memory-framework adapter, Qdrant the primary persistent vector backend, ChromaDB the backup, FAISS the temporary in-process option, and Graphiti the temporal graph adapter. They are currently unconfigured and truthfully reported as degraded. Bounded lexical retrieval remains the fallback.

All retrieval is namespace-scoped and context-budgeted. Durable records require provenance. Sensitive credential-shaped content is rejected. Explicit user correction and authoritative verified state supersede older records without erasing history. Backend failure never deletes authoritative memory metadata.

## CLI Examples

```text
memory status
memory help
memory remember Favorite snack | I like dark chocolate.
memory search dark chocolate
memory recent
memory cleanup
```

## Privacy Rules

- Store only useful, user-approved, local context.
- Block obvious secret-shaped content.
- Keep automatic summaries bounded.
- Prefer summaries and references over copying full conversation logs.

## Configuration

- `memory.local_only`
- `memory.auto_remember`
- `memory.auto_session_summary`
- `memory.max_records`
- `memory.max_search_results`
- `memory.max_context_items`
- `memory.max_context_chars`
- `memory.audit_enabled`
- `memory.audit_retention`
- `memory.default_retention_days`
- `memory.sensitive_storage_enabled`
- `memory.consolidation_enabled`
- `memory.secret_detection_enabled`

## Troubleshooting

- If memory status says unavailable, confirm `python main.py` started cleanly and the local storage directory exists.
- If a memory write is refused, check whether the content looks like a secret or sensitive record.
- If context retrieval feels too broad, lower the context item and character limits in configuration.
