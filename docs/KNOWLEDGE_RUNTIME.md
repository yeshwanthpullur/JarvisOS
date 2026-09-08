# Knowledge Runtime

Knowledge records are evidence with provenance, not execution or memory authority. Phase 6 document, research, vector, and graph adapters can propose bounded evidence packages, but the authoritative Knowledge Runtime decides whether an item is admitted, indexed, updated, or removed.

Document instructions remain untrusted. Web claims require traceable sources. Backend failure degrades to bounded lexical retrieval and never deletes authoritative metadata or silently rebuilds indexes.

Roadmap Steps 47-51 add the canonical local RAG path. Canonical documents and explicitly retained research evidence are chunked deterministically, persisted with source/version/provenance metadata, retrieved lexically or through an available local vector backend, reranked within a fixed budget, and assembled into bounded context. Claims and citations must resolve to retrieved source records. Stale versions, conflicting chunks, deleted sources, and unavailable vector backends remain visible rather than being silently hidden.

Qdrant is the preferred vector contract, with Chroma and FAISS as explicit fallbacks. The router never downloads packages, starts servers, contacts cloud services, or migrates data silently. When optional packages are absent, lexical retrieval remains available and vector status is `unconfigured`.
