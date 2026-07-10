"""Execution strategy definitions for intelligent provider routing."""

from __future__ import annotations

from enum import StrEnum


class ExecutionStrategy(StrEnum):
    """Provider execution strategies supported by the architecture."""

    DIRECT = "direct"
    MEMORY_FIRST = "memory_first"
    KNOWLEDGE_FIRST = "knowledge_first"
    TASK_FIRST = "task_first"
    PLUGIN_FIRST = "plugin_first"
    SINGLE_PROVIDER = "single_provider"
    MULTI_PROVIDER = "multi_provider"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    FALLBACK = "fallback"
    RECOVERY = "recovery"
    LOCAL_FIRST = "local_first"
    CLOUD_FIRST = "cloud_first"
    HYBRID = "hybrid"


class FallbackAction(StrEnum):
    """Fallback actions recorded for future execution recovery."""

    RETRY_SAME_MODEL = "retry_same_model"
    RETRY_DIFFERENT_MODEL = "retry_different_model"
    RETRY_DIFFERENT_PROVIDER = "retry_different_provider"
    LOCAL_PROVIDER = "local_provider"
    CLOUD_PROVIDER = "cloud_provider"
    RECOVERY_QUEUE = "recovery_queue"
    GRACEFUL_FAILURE = "graceful_failure"
    DIAGNOSTICS = "diagnostics"
