"""Default configuration values for JARVIS OS."""

from __future__ import annotations

from typing import Any, Final


DEFAULT_CONFIG: Final[dict[str, Any]] = {
    "general": {
        "app_name": "JARVIS OS",
        "environment": "development",
        "debug": False,
    },
    "logging": {
        "level": "INFO",
        "log_dir": "logs",
        "log_file": "jarvis-os.log",
        "max_bytes": 1_048_576,
        "backup_count": 5,
    },
    "memory": {
        "enabled": True,
        "storage_dir": "memory",
        "task_store_dir": "data/tasks",
        "vector_index_dir": "data/vector-indexes",
    },
    "brain": {
        "enabled": True,
        "vault_path": "data/obsidian-vault",
        "vault_name": "Jarvis Brain",
        "auto_create_vault": True,
        "daily_note_format": "%Y-%m-%d",
    },
    "models": {
        "default_model": "",
        "fallback_model": "",
        "allow_local_models": True,
    },
    "providers": {
        "default_provider": "",
        "enabled_providers": [],
        "timeout_seconds": 30,
        "max_retries": 2,
        "track_costs": True,
        "definitions": {},
    },
    "agents": {
        "enabled": True,
        "max_concurrent_agents": 4,
        "workspace_dir": "data/agent-workspaces",
    },
    "plugins": {
        "enabled": True,
        "plugin_dir": "plugins",
        "allow_user_plugins": False,
        "auto_discover": True,
        "auto_enable": True,
        "compatibility_version": "0.1",
    },
    "downloads": {
        "download_dir": "data/downloads",
        "max_concurrent_downloads": 3,
        "verify_integrity": True,
    },
    "automation": {
        "enabled": False,
        "queue_dir": "data/automation-queue",
        "max_concurrent_jobs": 2,
    },
    "security": {
        "secrets_dir": "data/secrets",
        "allow_shell_execution": False,
        "allow_network_access": True,
        "require_confirmation_for_installers": True,
    },
    "desktop": {
        "enabled": True,
        "platform": "windows",
        "downloads_folder": "",
    },
    "mobile": {
        "enabled": False,
        "api_enabled": False,
    },
}
