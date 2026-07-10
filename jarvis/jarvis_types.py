"""Typed enums used by the Executive JARVIS Core."""

from __future__ import annotations

from enum import StrEnum


class JarvisIntentType(StrEnum):
    """Intent labels produced by the intent engine."""

    CONVERSATION = "conversation"
    QUESTION = "question"
    RESEARCH = "research"
    PLANNING = "planning"
    TASK = "task"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    CODING = "coding"
    ENGINEERING = "engineering"
    LEARNING = "learning"
    AUTOMATION = "automation"
    PROVIDER = "provider"
    PLUGIN = "plugin"
    TOOL = "tool"
    WORKFLOW = "workflow"
    AGENT_CREATION = "agent_creation"
    MULTI_INTENT = "multi_intent"
    UNKNOWN = "unknown"


class ExecutionStrategy(StrEnum):
    """Execution strategies selected by the decision engine."""

    DIRECT = "direct"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TASK = "task"
    PLUGIN = "plugin"
    TOOL = "tool"
    AGENT = "agent"
    MULTI_AGENT = "multi_agent"
    PLANNING = "planning"
    RESEARCH = "research"
    WORKFLOW = "workflow"
    HYBRID = "hybrid"
    FALLBACK = "fallback"
    RECOVERY = "recovery"


class JarvisComplexity(StrEnum):
    """Request complexity labels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    UNKNOWN = "unknown"


class SessionType(StrEnum):
    """Executive session types."""

    CONVERSATION = "conversation"
    TASK = "task"
    PLANNING = "planning"
    WORKFLOW = "workflow"
    PROVIDER = "provider"
    PLUGIN = "plugin"
    AGENT = "agent"
    RECOVERY = "recovery"


class DelegationType(StrEnum):
    """Delegation models supported by the dispatcher architecture."""

    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    PIPELINE = "pipeline"
    HIERARCHICAL = "hierarchical"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    WORKFLOW = "workflow"
    FALLBACK = "fallback"
    RECOVERY = "recovery"

