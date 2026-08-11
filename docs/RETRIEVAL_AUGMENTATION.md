# Retrieval Augmentation

Lexical retrieval uses deterministic token overlap plus bounded freshness preference. Relevance score is a ranking signal, never truth probability. `auto` falls back to lexical when semantic embeddings are unavailable. Semantic, hybrid, and reranking interfaces are provider-neutral and must report unavailable rather than simulate vectors.

Retrieval enforces source and privacy scopes, optional trust/freshness filters, finite results, source diversity, and context character/chunk limits. Every result links chunk to record to source for citation integration.
