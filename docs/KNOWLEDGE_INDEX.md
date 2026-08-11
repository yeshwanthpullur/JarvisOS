# Knowledge Index

The provider-neutral index contract stores sources, records, and bounded chunks with stable SHA-256 checksums, provenance, trust, privacy scope, freshness, and embedding state. Normalization preserves text structure; deterministic paragraph-aware chunks have finite size and overlap. Identical source content is deduplicated.

Runtime indexes belong under ignored `data/knowledge/`; user documents, pages, repository snapshots, embeddings, and vector databases must never be committed. Source removal deletes only records/chunks owned by that source and immediately excludes them from active retrieval.
