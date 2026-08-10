"""Provider-neutral protocol for safe agent metadata handlers."""

from __future__ import annotations

from typing import Protocol

from .models import AgentRequest, AgentResult


class AgentProtocol(Protocol):
    """An agent handler receives a governed request and returns a bounded result."""

    @property
    def name(self) -> str: ...

    def handle(self, request: AgentRequest) -> AgentResult: ...

