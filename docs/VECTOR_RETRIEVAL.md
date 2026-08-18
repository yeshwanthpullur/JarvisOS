# Vector Retrieval

Qdrant is the planned primary persistent vector store, ChromaDB is the local backup, and FAISS is reserved for temporary in-process indexes. All are optional isolated adapters and are currently unconfigured. Lexical retrieval remains available when vector backends are absent.

Retrieval is namespace-scoped and bounded by result and context budgets. Embedding model/version/dimensions must accompany indexed vectors; incompatible dimensions are rejected and re-indexing is explicit. Vector storage cannot create authoritative memory directly.
