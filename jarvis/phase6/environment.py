"""Passive tool-environment discovery without installation or execution authority."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from importlib import metadata
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EnvironmentStatus(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    MISSING = "missing"
    INCOMPATIBLE = "incompatible"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ToolEnvironmentRecord:
    tool_id: str
    tool_name: str
    category: str
    primary_or_backup: str
    environment_name: str
    recommended_python: str
    package_name: str = ""
    import_name: str = ""
    executable_name: str = ""
    adapter_type: str = "subprocess"
    enabled: bool = False
    network_allowed: bool = False
    file_write_allowed: bool = False
    command_execution_allowed: bool = False
    approval_required: bool = True
    timeout_seconds: int = 30
    max_input_bytes: int = 16_000
    max_output_bytes: int = 64_000
    install_status: str = "not_checked"
    detected_version: str = ""
    health_status: EnvironmentStatus = EnvironmentStatus.UNKNOWN
    last_checked_at: str = ""
    last_error: str = ""
    fallback: str = "unavailable"

    @property
    def permission_profile(self) -> tuple[str, ...]:
        permissions = ["metadata_read"]
        if self.network_allowed:
            permissions.append("network_access")
        if self.file_write_allowed:
            permissions.append("write_files")
        if self.command_execution_allowed:
            permissions.append("execute_commands")
        return tuple(permissions)


@dataclass(frozen=True, slots=True)
class DependencyAudit:
    python_version: str
    implementation: str
    environment: str
    isolated: bool
    pip_available: bool
    pip_check_status: str
    installed_packages_checked: int
    detected_tools: int
    incompatible_tools: tuple[str, ...]
    warnings: tuple[str, ...]
    checked_at: str = field(default_factory=_now)


def _specs() -> tuple[ToolEnvironmentRecord, ...]:
    def item(tool_id: str, name: str, category: str, role: str, env: str, py: str, package: str = "", import_name: str = "", executable: str = "", **kwargs: object) -> ToolEnvironmentRecord:
        return ToolEnvironmentRecord(tool_id, name, category, role, env, py, package, import_name, executable, **kwargs)

    return (
        item("playwright", "Playwright", "browser", "backup", "tools/browser/.venv", "3.11-3.12", "playwright", "playwright", "playwright", network_allowed=True, fallback="read-only HTTP"),
        item("browser_use", "Browser Use", "browser", "primary", "tools/browser/.venv", "3.11-3.12", "browser-use", "browser_use", network_allowed=True, fallback="Playwright/read-only HTTP"),
        item("crawl4ai", "Crawl4AI", "research", "primary", "tools/research/.venv", "3.11-3.12", "crawl4ai", "crawl4ai", network_allowed=True, fallback="bounded read-only web"),
        item("firecrawl", "Firecrawl", "research", "backup", "tools/research/.venv", "3.11-3.12", "firecrawl-py", "firecrawl", network_allowed=True, fallback="Crawl4AI/read-only web"),
        item("docling", "Docling", "documents", "primary", "tools/documents/.venv", "3.11-3.12", "docling", "docling", fallback="plain-text parser"),
        item("marker", "Marker", "documents", "backup", "tools/documents/.venv", "3.11-3.12", "marker-pdf", "marker", fallback="Docling/plain-text parser"),
        item("langchain", "LangChain", "framework", "optional", "tools/research/.venv", "3.11-3.12", "langchain", "langchain", fallback="native JARVIS orchestration"),
        item("llama_index", "LlamaIndex", "framework", "optional", "tools/documents/.venv", "3.11-3.12", "llama-index", "llama_index", fallback="native knowledge index"),
        item("chromadb", "ChromaDB", "memory", "backup", "tools/memory/.venv", "3.11-3.12", "chromadb", "chromadb", fallback="lexical retrieval"),
        item("qdrant", "Qdrant Client", "memory", "primary", "tools/memory/.venv", "3.11-3.12", "qdrant-client", "qdrant_client", fallback="lexical retrieval"),
        item("faiss", "FAISS", "memory", "backup", "tools/memory/.venv", "3.11-3.12", "faiss-cpu", "faiss", fallback="lexical retrieval"),
        item("mem0", "Mem0", "memory", "optional", "tools/memory/.venv", "3.11-3.12", "mem0ai", "mem0", fallback="JARVIS persistent memory"),
        item("graphiti", "Graphiti", "memory", "optional", "tools/memory/.venv", "3.11-3.12", "graphiti-core", "graphiti_core", fallback="bounded relation metadata"),
        item("faster_whisper", "Faster Whisper", "voice", "primary", "tools/voice/.venv", "3.11", "faster-whisper", "faster_whisper", fallback="Vosk"),
        item("vosk", "Vosk", "voice", "backup", "tools/voice/.venv", "3.11-3.12", "vosk", "vosk", fallback="text input"),
        item("piper", "Piper", "voice", "primary", "tools/voice/.venv", "3.11", "piper-tts", "piper", "piper", fallback="Windows SAPI"),
        item("coqui_xtts", "Coqui XTTS", "voice", "experimental", "tools/voice/.venv", "3.11", "TTS", "TTS", fallback="Piper/Windows SAPI"),
        item("litellm", "LiteLLM", "models", "gateway", "tools/models/.venv", "3.11-3.12", "litellm", "litellm", "litellm", network_allowed=False, fallback="native provider registry"),
        item("aider", "Aider", "coding", "backup", "tools/coding/.venv", "3.11", "aider-chat", "aider", "aider", command_execution_allowed=False, file_write_allowed=False, fallback="Coding Agent plan-only"),
        item("open_interpreter", "Open Interpreter", "coding", "experimental", "tools/coding/.venv", "3.11", "open-interpreter", "interpreter", "interpreter", command_execution_allowed=False, file_write_allowed=False, fallback="Coding Agent plan-only"),
        item("ollama", "Ollama", "models", "primary", "tools/models", "native", executable="ollama", approval_required=False, fallback="llama.cpp"),
        item("llama_cpp", "llama.cpp", "models", "backup", "tools/models/llama.cpp", "native", executable="llama-cli", fallback="Ollama"),
        item("vllm", "vLLM", "models", "deferred", "Linux/CUDA", "3.10-3.12", "vllm", "vllm", fallback="Ollama", last_error="Deferred on Windows; Linux/CUDA runtime required."),
        item("open_webui", "Open WebUI", "experimental", "deferred", "tools/experimental/.venv", "3.11-3.12", "open-webui", "open_webui", fallback="CLI", last_error="Docker or a supported isolated deployment is required."),
    )


class ToolEnvironmentRegistry:
    """Records passive availability; it never creates environments or executes tools."""

    def __init__(self, records: tuple[ToolEnvironmentRecord, ...] = ()) -> None:
        self._records: dict[str, ToolEnvironmentRecord] = {}
        for record in records:
            self.register(record)

    def register(self, record: ToolEnvironmentRecord) -> None:
        if record.tool_id in self._records:
            raise ValueError(f"duplicate_tool_environment:{record.tool_id}")
        self._records[record.tool_id] = record

    def list(self) -> tuple[ToolEnvironmentRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def get(self, tool_id: str) -> ToolEnvironmentRecord | None:
        return self._records.get(tool_id)

    def inspect(self, tool_id: str) -> ToolEnvironmentRecord | None:
        record = self.get(tool_id)
        if record is None:
            return None
        version = ""
        installed = False
        error = record.last_error
        try:
            if record.package_name:
                version = metadata.version(record.package_name)
                installed = True
        except metadata.PackageNotFoundError:
            pass
        except Exception as exc:
            error = f"Package metadata check failed: {type(exc).__name__}."
        executable = shutil.which(record.executable_name) if record.executable_name else None
        installed = installed or bool(executable)
        current = sys.version_info[:2]
        incompatible = current >= (3, 13) and record.recommended_python not in {"native", "3.13"} and installed
        status = EnvironmentStatus.INCOMPATIBLE if incompatible else EnvironmentStatus.DEGRADED if error and installed else EnvironmentStatus.DISABLED if installed and not record.enabled else EnvironmentStatus.MISSING if not installed else EnvironmentStatus.READY
        if incompatible:
            error = f"Detected in Python {current[0]}.{current[1]}; use isolated {record.environment_name} with Python {record.recommended_python}."
        return replace(record, install_status="installed" if installed else "missing", detected_version=version, health_status=status, last_checked_at=_now(), last_error=error[:300])

    def refresh(self) -> tuple[ToolEnvironmentRecord, ...]:
        for key in tuple(self._records):
            checked = self.inspect(key)
            if checked is not None:
                self._records[key] = checked
        return self.list()

    def audit(self, *, run_pip_check: bool = False) -> DependencyAudit:
        records = self.refresh()
        pip_available = bool(shutil.which("pip")) or any(dist.metadata.get("Name", "").lower() == "pip" for dist in metadata.distributions())
        pip_status = "not_run"
        warnings: list[str] = []
        if run_pip_check:
            try:
                result = subprocess.run((sys.executable, "-m", "pip", "check"), capture_output=True, text=True, timeout=20, check=False)
                pip_status = "ok" if result.returncode == 0 else "conflicts"
                if result.returncode:
                    warnings.append("pip check reported dependency conflicts; no packages were changed.")
            except (OSError, subprocess.SubprocessError):
                pip_status = "unavailable"
                warnings.append("pip check could not be completed.")
        isolated = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
        if not isolated:
            warnings.append("Current Python is not an isolated virtual environment.")
        if sys.version_info >= (3, 13):
            warnings.append("Python 3.13 can be incompatible with several optional AI tools; use per-tool Python 3.11/3.12 environments.")
        return DependencyAudit(
            platform.python_version(), platform.python_implementation(), "virtualenv" if isolated else "global_or_bundled", isolated,
            pip_available, pip_status, sum(1 for _ in metadata.distributions()),
            sum(item.install_status == "installed" for item in records),
            tuple(item.tool_id for item in records if item.health_status is EnvironmentStatus.INCOMPATIBLE), tuple(warnings[:12]),
        )

    def summary(self) -> dict[str, object]:
        records = self.refresh()
        return {
            "total": len(records),
            "detected": sum(item.install_status == "installed" for item in records),
            "enabled": sum(item.enabled for item in records),
            "ready": sum(item.health_status is EnvironmentStatus.READY for item in records),
            "disabled": sum(item.health_status is EnvironmentStatus.DISABLED for item in records),
            "missing": sum(item.health_status is EnvironmentStatus.MISSING for item in records),
            "incompatible": sum(item.health_status is EnvironmentStatus.INCOMPATIBLE for item in records),
            "execution_authority": False,
        }


def build_tool_environment_registry() -> ToolEnvironmentRegistry:
    return ToolEnvironmentRegistry(_specs())
