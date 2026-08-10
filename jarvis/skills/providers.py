"""Conceptual providers for native and future external skill metadata."""

from __future__ import annotations

from typing import Protocol

from .models import SkillManifest


class ExternalToolProvider(Protocol):
    def manifests(self) -> tuple[SkillManifest, ...]: ...


class NativeSkillProvider(Protocol):
    def manifests(self) -> tuple[SkillManifest, ...]: ...


class MCPToolProvider(Protocol):
    """Future-only MCP manifest provider; no server is started in Phase 3."""

    def manifests(self) -> tuple[SkillManifest, ...]: ...

