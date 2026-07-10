"""Retrieval strategy definitions."""

from __future__ import annotations

from enum import StrEnum


class RetrievalStrategy(StrEnum):
    MEMORY_FIRST = "memory_first"
    KNOWLEDGE_FIRST = "knowledge_first"
    HYBRID = "hybrid"
    RECENT_FIRST = "recent_first"
    PRIORITY_FIRST = "priority_first"
    SIMILARITY = "similarity"
    EXACT_MATCH = "exact_match"
    METADATA_SEARCH = "metadata_search"
    REFERENCE_SEARCH = "reference_search"
    FUTURE_SEMANTIC_SEARCH = "future_semantic_search"
    FUTURE_VECTOR_SEARCH = "future_vector_search"
