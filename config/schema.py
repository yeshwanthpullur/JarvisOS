"""Typed configuration schema for JARVIS OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class GeneralConfig:
    """General application identity and runtime mode."""

    app_name: str
    environment: str
    debug: bool


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Logging output and rotation settings."""

    level: str
    log_dir: Path
    log_file: str
    max_bytes: int
    backup_count: int


@dataclass(frozen=True, slots=True)
class MemoryConfig:
    """Persistent memory and task storage locations."""

    enabled: bool
    storage_dir: Path
    task_store_dir: Path
    vector_index_dir: Path


@dataclass(frozen=True, slots=True)
class BrainConfig:
    """Obsidian Brain vault configuration."""

    enabled: bool
    vault_path: Path
    vault_name: str
    auto_create_vault: bool
    daily_note_format: str


@dataclass(frozen=True, slots=True)
class ModelsConfig:
    """Model selection preferences without binding to a provider."""

    default_model: str
    fallback_model: str
    allow_local_models: bool


@dataclass(frozen=True, slots=True)
class ProvidersConfig:
    """Provider routing configuration."""

    default_provider: str
    enabled_providers: tuple[str, ...]
    timeout_seconds: int
    max_retries: int
    track_costs: bool
    definitions: Mapping[str, Mapping[str, Any]] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True, slots=True)
class AgentsConfig:
    """Agent framework paths and governed coordination limits."""

    enabled: bool
    max_concurrent_agents: int
    workspace_dir: Path
    max_agents_per_coordination: int = 4
    max_subtasks_per_coordination: int = 8
    max_recursion_depth: int = 1
    max_retries_per_subtask: int = 1
    max_total_timeout_seconds: int = 180


@dataclass(frozen=True, slots=True)
class ToolsConfig:
    """Governed tool execution limits."""

    maximum_per_request: int = 3
    maximum_per_coordination: int = 6
    maximum_retries: int = 1
    maximum_timeout_seconds: int = 30
    maximum_concurrent: int = 2
    maximum_output_bytes: int = 64000
    maximum_argument_bytes: int = 16000
    maximum_chained_depth: int = 1
    maximum_dry_run_seconds: int = 5
    maximum_history: int = 200

@dataclass(frozen=True, slots=True)
class PlanningConfig:
    maximum_steps:int=12; maximum_milestones:int=5; maximum_alternatives:int=3; maximum_dependencies_per_step:int=4; maximum_plan_depth:int=2; maximum_retries:int=1; maximum_replans:int=3; maximum_concurrent:int=2; maximum_agents:int=3; maximum_tools:int=4; maximum_timeout_seconds:int=90; maximum_versions:int=10; maximum_output_bytes:int=100000; maximum_assumptions:int=8


@dataclass(frozen=True, slots=True)
class PluginsConfig:
    """Plugin loading policy and location."""

    enabled: bool
    plugin_dir: Path
    allow_user_plugins: bool
    auto_discover: bool
    auto_enable: bool
    compatibility_version: str


@dataclass(frozen=True, slots=True)
class DownloadsConfig:
    """Download queue and storage configuration."""

    download_dir: Path
    max_concurrent_downloads: int
    verify_integrity: bool


@dataclass(frozen=True, slots=True)
class AutomationConfig:
    """Automation queue configuration."""

    enabled: bool
    queue_dir: Path
    max_concurrent_jobs: int


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    """Security defaults for privileged or external actions."""

    secrets_dir: Path
    allow_shell_execution: bool
    allow_network_access: bool
    require_confirmation_for_installers: bool


@dataclass(frozen=True, slots=True)
class DesktopConfig:
    """Desktop integration configuration."""

    enabled: bool
    platform: str
    downloads_folder: Path | None


@dataclass(frozen=True, slots=True)
class MobileConfig:
    """Mobile integration configuration."""

    enabled: bool
    api_enabled: bool


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Complete immutable runtime configuration."""

    base_dir: Path
    general: GeneralConfig
    logging: LoggingConfig
    memory: MemoryConfig
    brain: BrainConfig
    models: ModelsConfig
    providers: ProvidersConfig
    agents: AgentsConfig
    plugins: PluginsConfig
    downloads: DownloadsConfig
    automation: AutomationConfig
    security: SecurityConfig
    desktop: DesktopConfig
    mobile: MobileConfig
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    planning: PlanningConfig = field(default_factory=PlanningConfig)

    @property
    def app_name(self) -> str:
        """Backward-compatible shortcut for the application name."""
        return self.general.app_name

    @property
    def environment(self) -> str:
        """Backward-compatible shortcut for the runtime environment."""
        return self.general.environment

    @property
    def debug(self) -> bool:
        """Backward-compatible shortcut for debug mode."""
        return self.general.debug

    @property
    def log_level(self) -> str:
        """Backward-compatible shortcut for the logging level."""
        return self.logging.level

    @property
    def data_dir(self) -> Path:
        """Backward-compatible shortcut for the data directory."""
        return self.base_dir / "data"

    @property
    def logs_dir(self) -> Path:
        """Backward-compatible shortcut for the logs directory."""
        return self.logging.log_dir
