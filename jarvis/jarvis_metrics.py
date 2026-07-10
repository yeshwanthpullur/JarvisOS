"""Metrics model for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class JarvisMetrics:
    """In-memory metrics counters for the executive foundation."""

    startup_count: int = 0
    requests: int = 0
    conversations: int = 0
    goals: int = 0
    plans: int = 0
    delegations: int = 0
    agents: int = 0
    providers: int = 0
    tools: int = 0
    skills: int = 0
    plugins: int = 0
    departments: int = 0
    workflows: int = 0
    failures: int = 0
    recoveries: int = 0
    health_score: float = 1.0
    future_cost: float = 0.0
    future_token_usage: int = 0

