"""Shared Phase 6 metadata runtime."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from .environment import ToolEnvironmentRegistry, build_tool_environment_registry
from .models import LocalModelCatalog
from .web import WebControlPlane
from .documents import DocumentPipeline
from .memory import MemoryRetrievalControlPlane
from .modalities import VoiceAdapterRouter, VisionControlPlane
from .coding_tools import ExternalCodingControlPlane
from .automation import LocalAutomationControlPlane
from .connectors import ConnectorRegistry
from .observability import ObservabilityRuntime
from .integration import Phase6CandidateReport, evaluate_candidate


class Phase6Runtime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or Path.cwd()).resolve()
        self.environments: ToolEnvironmentRegistry = build_tool_environment_registry()
        self.models = LocalModelCatalog()
        self.web = WebControlPlane()
        self.documents = DocumentPipeline(self.root)
        self.memory = MemoryRetrievalControlPlane()
        self.voice = VoiceAdapterRouter(self.environments)
        self.vision = VisionControlPlane()
        self.coding = ExternalCodingControlPlane(self.root, self.environments)
        self.automation = LocalAutomationControlPlane(self.root)
        self.connectors = ConnectorRegistry()
        self.observability = ObservabilityRuntime()
        self.execution_authority = False
        self.local_only = True

    def status(self) -> dict[str, object]:
        return {"phase": 6, "mode": "controlled_local_first", "execution_authority": self.execution_authority, "environment": self.environments.summary(), "models": self.models.summary(), "web": self.web.status(), "documents": self.documents.status(), "memory": self.memory.status(), "voice": self.voice.status(), "vision": self.vision.status(), "coding": self.coding.status(), "automation": self.automation.status(), "connectors": self.connectors.summary(), "observability": self.observability.snapshot()}

    def candidate_report(self, *, probe_provider: bool = False) -> Phase6CandidateReport:
        return evaluate_candidate(self, probe_provider=probe_provider)


_runtime: Phase6Runtime | None = None
_lock = Lock()


def get_phase6_runtime(root: Path | None = None) -> Phase6Runtime:
    global _runtime
    with _lock:
        if _runtime is None:
            _runtime = Phase6Runtime(root)
        return _runtime
