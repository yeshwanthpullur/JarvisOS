"""Shared Phase 6 metadata runtime."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from .environment import ToolEnvironmentRegistry, build_tool_environment_registry
from .models import LocalModelCatalog
from .web import WebControlPlane
from .documents import DocumentPipeline
from .memory import MemoryRetrievalControlPlane


class Phase6Runtime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or Path.cwd()).resolve()
        self.environments: ToolEnvironmentRegistry = build_tool_environment_registry()
        self.models = LocalModelCatalog()
        self.web = WebControlPlane()
        self.documents = DocumentPipeline(self.root)
        self.memory = MemoryRetrievalControlPlane()
        self.execution_authority = False
        self.local_only = True

    def status(self) -> dict[str, object]:
        return {"phase": 6, "mode": "controlled_local_first", "execution_authority": self.execution_authority, "environment": self.environments.summary(), "models": self.models.summary(), "web": self.web.status(), "documents": self.documents.status(), "memory": self.memory.status()}


_runtime: Phase6Runtime | None = None
_lock = Lock()


def get_phase6_runtime(root: Path | None = None) -> Phase6Runtime:
    global _runtime
    with _lock:
        if _runtime is None:
            _runtime = Phase6Runtime(root)
        return _runtime
