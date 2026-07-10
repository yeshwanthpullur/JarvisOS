"""Research strategy definitions."""

from __future__ import annotations

from enum import Enum


class ResearchStrategy(str, Enum):
    SINGLE_SOURCE = "single_source"
    MULTI_SOURCE = "multi_source"
    COMPARATIVE = "comparative"
    CHRONOLOGICAL = "chronological"
    EVIDENCE_BASED = "evidence_based"
    REFERENCE_DRIVEN = "reference_driven"
    KNOWLEDGE_FIRST = "knowledge_first"
    MEMORY_FIRST = "memory_first"
    HYBRID = "hybrid"
    FUTURE_PROVIDER_ASSISTED = "future_provider_assisted"
