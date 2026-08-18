"""Phase 6 local runtime discovery and integration control surfaces."""

from .environment import (
    DependencyAudit,
    EnvironmentStatus,
    ToolEnvironmentRecord,
    ToolEnvironmentRegistry,
    build_tool_environment_registry,
)
from .models import LocalModelCatalog, ModelRecord, ProviderSnapshot
from .integration import CheckState, ComponentCheck, Phase6CandidateReport, evaluate_candidate
from .runtime import Phase6Runtime, get_phase6_runtime
from .cli import render_phase6_command

__all__ = (
    "DependencyAudit",
    "EnvironmentStatus",
    "ToolEnvironmentRecord",
    "ToolEnvironmentRegistry",
    "build_tool_environment_registry",
    "LocalModelCatalog",
    "ModelRecord",
    "ProviderSnapshot",
    "CheckState",
    "ComponentCheck",
    "Phase6CandidateReport",
    "evaluate_candidate",
    "Phase6Runtime",
    "get_phase6_runtime",
    "render_phase6_command",
)
