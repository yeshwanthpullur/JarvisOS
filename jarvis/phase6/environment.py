"""Passive tool-environment discovery without installation or execution authority."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from importlib import metadata
from pathlib import Path
import os
import platform
import re
import shutil
import subprocess
import sys


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _package_key(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


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
    environment_key: str = ""
    directory_name: str = ""
    native_detector: str = ""
    runtime_only_detection: bool = False
    requires_core_environment: bool = False
    configured: bool = False
    integrated: bool = False
    enabled: bool = False
    execution_authorized: bool = False
    network_allowed: bool = False
    file_write_allowed: bool = False
    command_execution_allowed: bool = False
    approval_required: bool = True
    timeout_seconds: int = 30
    max_input_bytes: int = 16_000
    max_output_bytes: int = 64_000
    install_status: str = "not_checked"
    detected: bool = False
    detected_version: str = ""
    discovery_source: str = ""
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
    def item(tool_id: str, name: str, category: str, role: str, env_key: str, py: str, package: str = "", import_name: str = "", executable: str = "", **kwargs: object) -> ToolEnvironmentRecord:
        environment_name = f"uv_tool:{env_key.split('/', 1)[1]}" if env_key.startswith("uv/") else f"installations/{env_key}/.venv" if env_key else "system_or_tool_managed"
        return ToolEnvironmentRecord(
            tool_id=tool_id,
            tool_name=name,
            category=category,
            primary_or_backup=role,
            environment_name=environment_name,
            recommended_python=py,
            package_name=package,
            import_name=import_name,
            executable_name=executable,
            environment_key=env_key,
            **kwargs,
        )

    return (
        item("playwright", "Playwright", "browser", "backup", "browser", "3.11-3.12", "playwright", "playwright", "playwright", network_allowed=True, fallback="read-only HTTP"),
        item("browser_use", "Browser Use", "browser", "primary", "browser", "3.11-3.12", "browser-use", "browser_use", network_allowed=True, fallback="Playwright/read-only HTTP"),
        item("playwright_mcp", "Playwright MCP", "browser", "governed_adapter", "playwright-mcp", "Node", executable="npx.cmd", configured=True, integrated=True, enabled=True, runtime_only_detection=True, network_allowed=True, fallback="Playwright metadata adapter"),
        item("crawl4ai", "Crawl4AI", "research", "primary", "research", "3.11-3.12", "crawl4ai", "crawl4ai", network_allowed=True, fallback="bounded read-only web"),
        item("firecrawl", "Firecrawl", "research", "backup", "research", "3.11-3.12", "firecrawl-py", "firecrawl", network_allowed=True, fallback="Crawl4AI/read-only web"),
        item("docling", "Docling", "documents", "primary", "documents", "3.11-3.12", "docling", "docling", fallback="plain-text parser"),
        item("marker", "Marker", "documents", "backup", "documents", "3.11-3.12", "marker-pdf", "marker", fallback="Docling/plain-text parser"),
        item("langchain", "LangChain", "framework", "optional", "runtimes", "3.11-3.12", "langchain", "langchain", fallback="native JARVIS orchestration"),
        item("langchain_community", "LangChain Community", "framework", "optional", "runtimes", "3.11-3.12", "langchain-community", "langchain_community", fallback="native JARVIS integrations"),
        item("llama_index", "LlamaIndex", "framework", "optional", "runtimes", "3.11-3.12", "llama-index", "llama_index", fallback="native knowledge index"),
        item("chromadb", "ChromaDB", "memory", "backup", "memory", "3.11-3.12", "chromadb", "chromadb", fallback="lexical retrieval"),
        item("qdrant", "Qdrant Client", "memory", "primary", "memory", "3.11-3.12", "qdrant-client", "qdrant_client", fallback="lexical retrieval"),
        item("faiss", "FAISS", "memory", "backup", "memory", "3.11-3.12", "faiss-cpu", "faiss", fallback="lexical retrieval"),
        item("mem0", "Mem0", "memory", "optional", "memory", "3.11-3.12", "mem0ai", "mem0", fallback="JARVIS persistent memory"),
        item("graphiti", "Graphiti", "memory", "optional", "memory", "3.11-3.12", "graphiti-core", "graphiti_core", fallback="bounded relation metadata"),
        item("faster_whisper", "Faster Whisper", "voice", "primary_candidate", "voice", "3.11", "faster-whisper", "faster_whisper", fallback="Vosk"),
        item("vosk", "Vosk", "voice", "active_stt", "voice", "3.11-3.12", "vosk", "vosk", configured=True, integrated=True, enabled=True, requires_core_environment=True, approval_required=False, fallback="text input"),
        item("sounddevice", "SoundDevice", "voice", "capture_dependency", "voice", "3.11-3.12", "sounddevice", "sounddevice", configured=True, integrated=True, enabled=True, requires_core_environment=True, approval_required=False, fallback="no microphone capture"),
        item("piper", "Piper", "voice", "primary_candidate", "voice", "3.11", "piper-tts", "piper", "piper", fallback="Windows SAPI"),
        item("coqui_xtts", "Coqui XTTS", "voice", "experimental", "voice", "3.11", "TTS", "TTS", fallback="Piper/Windows SAPI"),
        item("windows_sapi", "Windows SAPI", "voice", "active_tts", "", "native", native_detector="windows_sapi", configured=True, integrated=True, enabled=True, approval_required=False, fallback="text-only output"),
        item("litellm", "LiteLLM", "models", "optional_gateway", "runtimes", "3.11-3.12", "litellm", "litellm", "litellm", fallback="native provider registry"),
        item("aider", "Aider", "coding", "backup", "uv/aider-chat", "3.11", "aider-chat", "aider", "aider", fallback="Coding Agent plan-only"),
        item("open_interpreter", "Open Interpreter", "coding", "experimental", "open-interpreter", "3.11", "open-interpreter", "interpreter", "interpreter", fallback="Coding Agent plan-only"),
        item("agent_reach", "Agent Reach", "agent", "optional", "agent-reach", "3.11-3.12", "agent-reach", "agent_reach", fallback="Research Agent planning"),
        item("yt_dlp", "yt-dlp", "research", "optional", "agent-reach", "3.11-3.12", "yt-dlp", "yt_dlp", "yt-dlp", network_allowed=True, fallback="read-only source metadata"),
        item("github_cli", "GitHub CLI", "coding", "external_cli", "", "native", executable="gh", fallback="local git metadata"),
        item("mcporter", "mcporter", "agent", "external_gateway", "", "Node", executable="mcporter.cmd", fallback="native MCP registry"),
        item("exa_mcp", "Exa MCP", "research", "external_config", "", "external", directory_name="exa", fallback="read-only web foundation", last_error="External configuration is not imported into JARVIS automatically."),
        item("hermes_agent", "Hermes Agent", "agent", "governed_external", "hermes-agent", "external", directory_name="hermes-agent", fallback="Prime Agent", last_error="External agent remains non-authoritative and execution-disabled."),
        item("ollama", "Ollama", "models", "primary", "", "native", executable="ollama", configured=True, integrated=True, enabled=True, approval_required=False, fallback="llama.cpp"),
        item("llama_cpp", "llama.cpp", "models", "backup", "models", "native", executable="llama-cli", fallback="Ollama"),
        item("vllm", "vLLM", "models", "deferred", "runtimes", "3.10-3.12", "vllm", "vllm", fallback="Ollama", last_error="Deferred on Windows; Linux/CUDA runtime required."),
        item("open_webui", "Open WebUI", "experimental", "deferred", "runtimes", "3.11-3.12", "open-webui", "open_webui", fallback="CLI", last_error="Docker or a supported isolated deployment is required."),
    )


def _installation_roots(repo_root: Path) -> tuple[Path, ...]:
    candidates: list[Path] = []
    override = os.environ.get("JARVIS_INSTALLATIONS_ROOTS", "")
    candidates.extend(Path(value).expanduser() for value in override.split(os.pathsep) if value.strip())
    candidates.append(repo_root / "installations")
    if os.name == "nt":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            candidate = Path(f"{letter}:") / "installations"
            if candidate.is_dir():
                candidates.append(candidate)
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            key = os.path.normcase(str(candidate.resolve()))
        except OSError:
            continue
        if key not in seen and candidate.is_dir():
            seen.add(key)
            unique.append(candidate)
    return tuple(unique[:8])


class ToolEnvironmentRegistry:
    """Records passive availability; it never creates environments or executes tools."""

    def __init__(self, records: tuple[ToolEnvironmentRecord, ...] = (), *, root: Path | None = None) -> None:
        self._records: dict[str, ToolEnvironmentRecord] = {}
        self.root = (root or Path.cwd()).resolve()
        self.installation_roots = _installation_roots(self.root)
        self._package_cache: dict[str, dict[str, str]] = {}
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

    def _environment_dirs(self, key: str) -> tuple[Path, ...]:
        if not key:
            return ()
        if key.startswith("uv/"):
            tool_name = key.split("/", 1)[1]
            bases = (
                Path(os.environ.get("APPDATA", "")) / "uv" / "tools",
                Path(os.environ.get("LOCALAPPDATA", "")) / "uv" / "tools",
                Path.home() / ".local" / "share" / "uv" / "tools",
            )
            return tuple(base / tool_name for base in bases if str(base) and (base / tool_name).is_dir())
        return tuple(root / key for root in self.installation_roots if (root / key).is_dir())

    def _inventory(self, environment_dir: Path) -> dict[str, str]:
        cache_key = os.path.normcase(str(environment_dir))
        if cache_key in self._package_cache:
            return self._package_cache[cache_key]
        inventory: dict[str, str] = {}
        site_candidates = (
            environment_dir / ".venv" / "Lib" / "site-packages",
            environment_dir / "venv" / "Lib" / "site-packages",
            environment_dir / "Lib" / "site-packages",
        )
        for site in site_candidates:
            if not site.is_dir():
                continue
            try:
                for entry in site.glob("*.dist-info"):
                    match = re.match(r"^(.+?)-(\d[^/]*)\.dist-info$", entry.name, re.IGNORECASE)
                    if match:
                        inventory[_package_key(match.group(1))] = match.group(2)
            except OSError:
                continue
        self._package_cache[cache_key] = inventory
        return inventory

    def inspect(self, tool_id: str) -> ToolEnvironmentRecord | None:
        record = self.get(tool_id)
        if record is None:
            return None
        version = ""
        detected = False
        source = ""
        error = record.last_error
        try:
            if record.package_name:
                version = metadata.version(record.package_name)
                detected = True
                source = "core_environment"
        except metadata.PackageNotFoundError:
            pass
        except Exception as exc:
            error = f"Package metadata check failed: {type(exc).__name__}."

        if record.package_name and not detected:
            package_key = _package_key(record.package_name)
            for environment_dir in self._environment_dirs(record.environment_key):
                inventory = self._inventory(environment_dir)
                if package_key in inventory:
                    detected = True
                    version = inventory[package_key]
                    source = f"isolated_environment:{record.environment_key}"
                    break

        executable = shutil.which(record.executable_name) if record.executable_name else None
        if executable and not detected:
            detected = True
            source = "executable_path"

        if record.native_detector == "windows_sapi" and platform.system() == "Windows":
            detected = True
            source = "native_windows"

        if record.directory_name and not detected:
            for root in self.installation_roots:
                if (root / record.directory_name).is_dir():
                    detected = True
                    source = f"source_checkout:{record.directory_name}"
                    break

        current = sys.version_info[:2]
        incompatible = current >= (3, 13) and record.recommended_python not in {"native", "external", "Node", "3.13"} and source == "core_environment"
        if incompatible:
            status = EnvironmentStatus.INCOMPATIBLE
            error = f"Detected in core Python {current[0]}.{current[1]}; use its isolated environment with Python {record.recommended_python}."
        elif not detected:
            status = EnvironmentStatus.MISSING
        elif record.runtime_only_detection:
            status = EnvironmentStatus.DEGRADED
            error = error or "The launcher runtime is detected; use MCP discovery to verify the configured package."
        elif record.requires_core_environment and source != "core_environment":
            status = EnvironmentStatus.DEGRADED
            error = "Installed in an isolated environment, but the current in-process adapter cannot import it."
        elif record.integrated and record.configured and record.enabled:
            status = EnvironmentStatus.READY
        elif record.integrated and record.configured:
            status = EnvironmentStatus.DEGRADED
        else:
            status = EnvironmentStatus.DISABLED
        return replace(
            record,
            install_status="runtime_detected" if detected and record.runtime_only_detection else "installed" if detected else "missing",
            detected=detected,
            detected_version=version,
            discovery_source=source,
            health_status=status,
            last_checked_at=_now(),
            last_error=error[:300],
        )

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
            sum(item.detected for item in records),
            tuple(item.tool_id for item in records if item.health_status is EnvironmentStatus.INCOMPATIBLE), tuple(warnings[:12]),
        )

    def summary(self) -> dict[str, object]:
        records = self.refresh()
        return {
            "total": len(records),
            "detected": sum(item.detected for item in records),
            "configured": sum(item.configured for item in records),
            "integrated": sum(item.integrated for item in records),
            "enabled": sum(item.enabled for item in records),
            "ready": sum(item.health_status is EnvironmentStatus.READY for item in records),
            "disabled": sum(item.health_status is EnvironmentStatus.DISABLED for item in records),
            "missing": sum(item.health_status is EnvironmentStatus.MISSING for item in records),
            "incompatible": sum(item.health_status is EnvironmentStatus.INCOMPATIBLE for item in records),
            "execution_authority": False,
        }


def build_tool_environment_registry(root: Path | None = None) -> ToolEnvironmentRegistry:
    return ToolEnvironmentRegistry(_specs(), root=root)
