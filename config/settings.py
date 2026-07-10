"""Centralized application configuration loading."""

from __future__ import annotations

import copy
import os
import warnings
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from config.defaults import DEFAULT_CONFIG
from config.schema import (
    AgentsConfig,
    AppSettings,
    AutomationConfig,
    BrainConfig,
    DesktopConfig,
    DownloadsConfig,
    GeneralConfig,
    LoggingConfig,
    MemoryConfig,
    MobileConfig,
    ModelsConfig,
    PluginsConfig,
    ProvidersConfig,
    SecurityConfig,
)


BASE_DIR: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_FILE: Final[Path] = BASE_DIR / "config.yaml"
DEFAULT_ENV_FILE: Final[Path] = BASE_DIR / ".env"
VALID_LOG_LEVELS: Final[set[str]] = {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
}

ENV_OVERRIDES: Final[dict[str, tuple[str, ...]]] = {
    "JARVIS_APP_NAME": ("general", "app_name"),
    "JARVIS_ENVIRONMENT": ("general", "environment"),
    "JARVIS_DEBUG": ("general", "debug"),
    "JARVIS_LOG_LEVEL": ("logging", "level"),
    "JARVIS_LOG_DIR": ("logging", "log_dir"),
    "JARVIS_LOG_FILE": ("logging", "log_file"),
    "JARVIS_MEMORY_ENABLED": ("memory", "enabled"),
    "JARVIS_MEMORY_STORAGE_DIR": ("memory", "storage_dir"),
    "JARVIS_TASK_STORE_DIR": ("memory", "task_store_dir"),
    "JARVIS_BRAIN_ENABLED": ("brain", "enabled"),
    "JARVIS_OBSIDIAN_VAULT_PATH": ("brain", "vault_path"),
    "JARVIS_OBSIDIAN_VAULT_NAME": ("brain", "vault_name"),
    "JARVIS_OBSIDIAN_AUTO_CREATE": ("brain", "auto_create_vault"),
    "JARVIS_DEFAULT_MODEL": ("models", "default_model"),
    "JARVIS_FALLBACK_MODEL": ("models", "fallback_model"),
    "JARVIS_DEFAULT_PROVIDER": ("providers", "default_provider"),
    "JARVIS_PROVIDER_TIMEOUT_SECONDS": ("providers", "timeout_seconds"),
    "JARVIS_PROVIDER_MAX_RETRIES": ("providers", "max_retries"),
    "JARVIS_PLUGINS_ENABLED": ("plugins", "enabled"),
    "JARVIS_PLUGIN_DIR": ("plugins", "plugin_dir"),
    "JARVIS_PLUGINS_AUTO_DISCOVER": ("plugins", "auto_discover"),
    "JARVIS_PLUGINS_AUTO_ENABLE": ("plugins", "auto_enable"),
    "JARVIS_DOWNLOAD_DIR": ("downloads", "download_dir"),
    "JARVIS_AUTOMATION_ENABLED": ("automation", "enabled"),
    "JARVIS_ALLOW_SHELL_EXECUTION": ("security", "allow_shell_execution"),
    "JARVIS_ALLOW_NETWORK_ACCESS": ("security", "allow_network_access"),
    "JARVIS_DESKTOP_ENABLED": ("desktop", "enabled"),
    "JARVIS_MOBILE_ENABLED": ("mobile", "enabled"),
}


def load_settings(
    config_file: Path | None = None,
    env_file: Path | None = None,
) -> AppSettings:
    """Load settings from defaults, config.yaml, .env, and environment variables.

    Precedence from lowest to highest:
    defaults, config.yaml, .env, process environment variables.
    """
    raw_config = copy.deepcopy(DEFAULT_CONFIG)
    yaml_config = _read_yaml_file(config_file or DEFAULT_CONFIG_FILE)
    _deep_merge(raw_config, yaml_config)

    env_values = _read_env_file(env_file or DEFAULT_ENV_FILE)
    _apply_env_overrides(raw_config, env_values)

    log_level = str(raw_config["logging"]["level"]).upper()
    if log_level not in VALID_LOG_LEVELS:
        valid_values = ", ".join(sorted(VALID_LOG_LEVELS))
        raise ValueError(f"JARVIS_LOG_LEVEL must be one of: {valid_values}")
    raw_config["logging"]["level"] = log_level

    return AppSettings(
        base_dir=BASE_DIR,
        general=GeneralConfig(
            app_name=str(raw_config["general"]["app_name"]),
            environment=str(raw_config["general"]["environment"]),
            debug=_coerce_bool(raw_config["general"]["debug"]),
        ),
        logging=LoggingConfig(
            level=str(raw_config["logging"]["level"]),
            log_dir=_resolve_path(raw_config["logging"]["log_dir"]),
            log_file=str(raw_config["logging"]["log_file"]),
            max_bytes=int(raw_config["logging"]["max_bytes"]),
            backup_count=int(raw_config["logging"]["backup_count"]),
        ),
        memory=MemoryConfig(
            enabled=_coerce_bool(raw_config["memory"]["enabled"]),
            storage_dir=_resolve_path(raw_config["memory"]["storage_dir"]),
            task_store_dir=_resolve_path(raw_config["memory"]["task_store_dir"]),
            vector_index_dir=_resolve_path(raw_config["memory"]["vector_index_dir"]),
        ),
        brain=BrainConfig(
            enabled=_coerce_bool(raw_config["brain"]["enabled"]),
            vault_path=_resolve_path(raw_config["brain"]["vault_path"]),
            vault_name=str(raw_config["brain"]["vault_name"]),
            auto_create_vault=_coerce_bool(raw_config["brain"]["auto_create_vault"]),
            daily_note_format=str(raw_config["brain"]["daily_note_format"]),
        ),
        models=ModelsConfig(
            default_model=str(raw_config["models"]["default_model"]),
            fallback_model=str(raw_config["models"]["fallback_model"]),
            allow_local_models=_coerce_bool(raw_config["models"]["allow_local_models"]),
        ),
        providers=ProvidersConfig(
            default_provider=str(raw_config["providers"]["default_provider"]),
            enabled_providers=tuple(raw_config["providers"]["enabled_providers"]),
            timeout_seconds=int(raw_config["providers"]["timeout_seconds"]),
            max_retries=int(raw_config["providers"]["max_retries"]),
            track_costs=_coerce_bool(raw_config["providers"]["track_costs"]),
            definitions=_freeze_mapping(raw_config["providers"]["definitions"]),
        ),
        agents=AgentsConfig(
            enabled=_coerce_bool(raw_config["agents"]["enabled"]),
            max_concurrent_agents=int(raw_config["agents"]["max_concurrent_agents"]),
            workspace_dir=_resolve_path(raw_config["agents"]["workspace_dir"]),
        ),
        plugins=PluginsConfig(
            enabled=_coerce_bool(raw_config["plugins"]["enabled"]),
            plugin_dir=_resolve_path(raw_config["plugins"]["plugin_dir"]),
            allow_user_plugins=_coerce_bool(raw_config["plugins"]["allow_user_plugins"]),
            auto_discover=_coerce_bool(raw_config["plugins"]["auto_discover"]),
            auto_enable=_coerce_bool(raw_config["plugins"]["auto_enable"]),
            compatibility_version=str(raw_config["plugins"]["compatibility_version"]),
        ),
        downloads=DownloadsConfig(
            download_dir=_resolve_path(raw_config["downloads"]["download_dir"]),
            max_concurrent_downloads=int(
                raw_config["downloads"]["max_concurrent_downloads"]
            ),
            verify_integrity=_coerce_bool(raw_config["downloads"]["verify_integrity"]),
        ),
        automation=AutomationConfig(
            enabled=_coerce_bool(raw_config["automation"]["enabled"]),
            queue_dir=_resolve_path(raw_config["automation"]["queue_dir"]),
            max_concurrent_jobs=int(raw_config["automation"]["max_concurrent_jobs"]),
        ),
        security=SecurityConfig(
            secrets_dir=_resolve_path(raw_config["security"]["secrets_dir"]),
            allow_shell_execution=_coerce_bool(
                raw_config["security"]["allow_shell_execution"]
            ),
            allow_network_access=_coerce_bool(
                raw_config["security"]["allow_network_access"]
            ),
            require_confirmation_for_installers=_coerce_bool(
                raw_config["security"]["require_confirmation_for_installers"]
            ),
        ),
        desktop=DesktopConfig(
            enabled=_coerce_bool(raw_config["desktop"]["enabled"]),
            platform=str(raw_config["desktop"]["platform"]),
            downloads_folder=_optional_path(raw_config["desktop"]["downloads_folder"]),
        ),
        mobile=MobileConfig(
            enabled=_coerce_bool(raw_config["mobile"]["enabled"]),
            api_enabled=_coerce_bool(raw_config["mobile"]["api_enabled"]),
        ),
    )


def _read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        import yaml
    except ImportError:
        warnings.warn(
            "PyYAML is not installed; config.yaml was skipped. "
            "Install requirements.txt for full YAML configuration support.",
            RuntimeWarning,
            stacklevel=2,
        )
        return {}

    content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(content, dict):
        raise ValueError("config.yaml must contain a mapping at the top level.")

    return content


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def _apply_env_overrides(config: dict[str, Any], env_values: dict[str, str]) -> None:
    for env_key, path in ENV_OVERRIDES.items():
        value = os.getenv(env_key) or env_values.get(env_key)
        if value is None:
            continue

        _set_nested_value(config, path, value)


def _set_nested_value(config: dict[str, Any], path: tuple[str, ...], value: str) -> None:
    cursor = config
    for key in path[:-1]:
        cursor = cursor.setdefault(key, {})
    cursor[path[-1]] = value


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def _resolve_path(value: object) -> Path:
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path
    return BASE_DIR / path


def _optional_path(value: object) -> Path | None:
    if value is None or str(value).strip() == "":
        return None
    return _resolve_path(value)


def _freeze_mapping(value: object) -> MappingProxyType[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("providers.definitions must be a mapping.")
    return MappingProxyType(dict(value))
