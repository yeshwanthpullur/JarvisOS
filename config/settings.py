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
    CodingConfig,
    DesktopConfig,
    DownloadsConfig,
    GeneralConfig,
    LoggingConfig,
    MemoryConfig,
    ConversationIntelligenceConfig,
    MobileConfig,
    ModelsConfig,
    PluginsConfig,
    PrimeConfig,
    ProvidersConfig,
    ResearchConfig,
    SecurityConfig,
    SkillsConfig,
    ToolsConfig,
    PlanningConfig,
    VoiceConfig,
    VisionConfig,
    VideoEditingConfig,
    SyncConfig,
    WebAutomationConfig,
    InterfaceConfig,
    ImageGenerationConfig,
    ExternalIntegrationsConfig,
    ExternalProviderFlagsConfig,
    TelegramConfig,
    DiscordConfig,EmailConnectorConfig,SlackConfig,
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
    "JARVIS_MEMORY_LOCAL_ONLY": ("memory", "local_only"),
    "JARVIS_MEMORY_AUTO_REMEMBER": ("memory", "auto_remember"),
    "JARVIS_MEMORY_AUTO_SESSION_SUMMARY": ("memory", "auto_session_summary"),
    "JARVIS_MEMORY_MAX_RECORDS": ("memory", "max_records"),
    "JARVIS_MEMORY_MAX_SEARCH_RESULTS": ("memory", "max_search_results"),
    "JARVIS_MEMORY_MAX_CONTEXT_ITEMS": ("memory", "max_context_items"),
    "JARVIS_MEMORY_MAX_CONTEXT_CHARS": ("memory", "max_context_chars"),
    "JARVIS_MEMORY_AUDIT_ENABLED": ("memory", "audit_enabled"),
    "JARVIS_MEMORY_AUDIT_RETENTION": ("memory", "audit_retention"),
    "JARVIS_MEMORY_DEFAULT_RETENTION_DAYS": ("memory", "default_retention_days"),
    "JARVIS_MEMORY_SENSITIVE_STORAGE_ENABLED": ("memory", "sensitive_storage_enabled"),
    "JARVIS_MEMORY_CONSOLIDATION_ENABLED": ("memory", "consolidation_enabled"),
    "JARVIS_MEMORY_SECRET_DETECTION_ENABLED": ("memory", "secret_detection_enabled"),
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
            local_only=_coerce_bool(raw_config["memory"]["local_only"]),
            auto_remember=_coerce_bool(raw_config["memory"]["auto_remember"]),
            auto_session_summary=_coerce_bool(raw_config["memory"]["auto_session_summary"]),
            max_records=int(raw_config["memory"]["max_records"]),
            max_search_results=int(raw_config["memory"]["max_search_results"]),
            max_context_items=int(raw_config["memory"]["max_context_items"]),
            max_context_chars=int(raw_config["memory"]["max_context_chars"]),
            audit_enabled=_coerce_bool(raw_config["memory"]["audit_enabled"]),
            audit_retention=int(raw_config["memory"]["audit_retention"]),
            default_retention_days=int(raw_config["memory"]["default_retention_days"]),
            sensitive_storage_enabled=_coerce_bool(raw_config["memory"]["sensitive_storage_enabled"]),
            consolidation_enabled=_coerce_bool(raw_config["memory"]["consolidation_enabled"]),
            secret_detection_enabled=_coerce_bool(raw_config["memory"]["secret_detection_enabled"]),
        ),
        conversation=ConversationIntelligenceConfig(
            enabled=_coerce_bool(raw_config["conversation"]["enabled"]),
            max_turns=int(raw_config["conversation"]["max_turns"]),
            max_topics=int(raw_config["conversation"]["max_topics"]),
            summary_threshold=int(raw_config["conversation"]["summary_threshold"]),
            reference_resolution=_coerce_bool(raw_config["conversation"]["reference_resolution"]),
            clarification_enabled=_coerce_bool(raw_config["conversation"]["clarification_enabled"]),
            max_context_chars=int(raw_config["conversation"]["max_context_chars"]),
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
            enabled=_coerce_bool(raw_config["models"]["enabled"]),
            local_only_default=_coerce_bool(raw_config["models"]["local_only_default"]),
            allow_cloud_providers=_coerce_bool(raw_config["models"]["allow_cloud_providers"]),
            default_chat_provider=str(raw_config["models"]["default_chat_provider"]),
            default_reasoning_provider=str(raw_config["models"]["default_reasoning_provider"]),
            default_coding_provider=str(raw_config["models"]["default_coding_provider"]),
            default_vision_provider=str(raw_config["models"]["default_vision_provider"]),
            max_providers=int(raw_config["models"]["max_providers"]),
            max_models_per_provider=int(raw_config["models"]["max_models_per_provider"]),
            max_route_explanations=int(raw_config["models"]["max_route_explanations"]),
            hardware_discovery_enabled=_coerce_bool(raw_config["models"]["hardware_discovery_enabled"]),
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
            max_agents_per_coordination=int(raw_config["agents"]["max_agents_per_coordination"]),
            max_subtasks_per_coordination=int(raw_config["agents"]["max_subtasks_per_coordination"]),
            max_recursion_depth=int(raw_config["agents"]["max_recursion_depth"]),
            max_retries_per_subtask=int(raw_config["agents"]["max_retries_per_subtask"]),
            max_total_timeout_seconds=int(raw_config["agents"]["max_total_timeout_seconds"]),
            default_mode=str(raw_config["agents"]["default_mode"]),
            max_agents=int(raw_config["agents"]["max_agents"]),
            max_capabilities_per_agent=int(raw_config["agents"]["max_capabilities_per_agent"]),
            max_output_chars=int(raw_config["agents"]["max_output_chars"]),
            require_approval_for_high_risk=_coerce_bool(raw_config["agents"]["require_approval_for_high_risk"]),
            local_only_default=_coerce_bool(raw_config["agents"]["local_only_default"]),
            register_future_placeholders=_coerce_bool(raw_config["agents"]["register_future_placeholders"]),
            show_future_agents=_coerce_bool(raw_config["agents"]["show_future_agents"]),
            max_diagnostic_agents=int(raw_config["agents"]["max_diagnostic_agents"]),
            max_diagnostic_capabilities=int(raw_config["agents"]["max_diagnostic_capabilities"]),
            default_specialist_mode=str(raw_config["agents"]["default_specialist_mode"]),
            block_critical_future_agents=_coerce_bool(raw_config["agents"]["block_critical_future_agents"]),
        ),
        prime=PrimeConfig(
            enabled=_coerce_bool(raw_config["prime"]["enabled"]),
            default_execution_mode=str(raw_config["prime"]["default_execution_mode"]),
            max_plan_steps=int(raw_config["prime"]["max_plan_steps"]),
            max_reason_chars=int(raw_config["prime"]["max_reason_chars"]),
            max_fallbacks=int(raw_config["prime"]["max_fallbacks"]),
            require_approval_for_high_risk=_coerce_bool(raw_config["prime"]["require_approval_for_high_risk"]),
            block_critical_risk=_coerce_bool(raw_config["prime"]["block_critical_risk"]),
            local_only=_coerce_bool(raw_config["prime"]["local_only"]),
        ),
        skills=SkillsConfig(
            enabled=_coerce_bool(raw_config["skills"]["enabled"]),
            allow_external_plugins=_coerce_bool(raw_config["skills"]["allow_external_plugins"]),
            allow_mcp=_coerce_bool(raw_config["skills"]["allow_mcp"]),
            default_execution_mode=str(raw_config["skills"]["default_execution_mode"]),
            max_skills=int(raw_config["skills"]["max_skills"]),
            max_capabilities_per_skill=int(raw_config["skills"]["max_capabilities_per_skill"]),
            max_output_chars=int(raw_config["skills"]["max_output_chars"]),
            require_approval_for_side_effects=_coerce_bool(raw_config["skills"]["require_approval_for_side_effects"]),
            block_secrets_access=_coerce_bool(raw_config["skills"]["block_secrets_access"]),
        ),
        research=ResearchConfig(
            enabled=_coerce_bool(raw_config["research"]["enabled"]),
            default_depth=str(raw_config["research"]["default_depth"]),
            max_plan_steps=int(raw_config["research"]["max_plan_steps"]),
            max_evidence_items=int(raw_config["research"]["max_evidence_items"]),
            max_snippet_chars=int(raw_config["research"]["max_snippet_chars"]),
            max_summary_chars=int(raw_config["research"]["max_summary_chars"]),
            allow_web_read_only=_coerce_bool(raw_config["research"]["allow_web_read_only"]),
            allow_external_search_api=_coerce_bool(raw_config["research"]["allow_external_search_api"]),
            save_history=_coerce_bool(raw_config["research"]["save_history"]),
            local_only=_coerce_bool(raw_config["research"]["local_only"]),
            require_citations_for_web_claims=_coerce_bool(raw_config["research"]["require_citations_for_web_claims"]),
        ),
        coding=CodingConfig(
            enabled=_coerce_bool(raw_config["coding"]["enabled"]),
            default_mode=str(raw_config["coding"]["default_mode"]),
            max_plan_steps=int(raw_config["coding"]["max_plan_steps"]),
            max_files_listed=int(raw_config["coding"]["max_files_listed"]),
            max_diff_chars=int(raw_config["coding"]["max_diff_chars"]),
            max_history_items=int(raw_config["coding"]["max_history_items"]),
            allow_write_operations=_coerce_bool(raw_config["coding"]["allow_write_operations"]),
            allow_command_execution=_coerce_bool(raw_config["coding"]["allow_command_execution"]),
            require_approval_for_write=_coerce_bool(raw_config["coding"]["require_approval_for_write"]),
            require_approval_for_push=_coerce_bool(raw_config["coding"]["require_approval_for_push"]),
            block_secrets_access=_coerce_bool(raw_config["coding"]["block_secrets_access"]),
        ),
        external_integrations=ExternalIntegrationsConfig(**raw_config["external_integrations"]),
        external_provider_flags=ExternalProviderFlagsConfig(**raw_config["external_provider_flags"]),
        telegram=TelegramConfig(**raw_config["telegram"]),
        discord=DiscordConfig(**raw_config["discord"]),
        email_connector=EmailConnectorConfig(**raw_config["email_connector"]),
        slack=SlackConfig(**raw_config["slack"]),
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
            automation_enabled=_coerce_bool(raw_config["mobile"]["automation_enabled"]),
            automation_mode=str(raw_config["mobile"]["automation_mode"]),
            automation_adapter=str(raw_config["mobile"]["automation_adapter"]),
            audit_retention=int(raw_config["mobile"]["audit_retention"]),
            live_control_enabled=_coerce_bool(raw_config["mobile"]["live_control_enabled"]),
            store_private_data=_coerce_bool(raw_config["mobile"]["store_private_data"]),
        ),
        tools=ToolsConfig(**{key: int(value) for key, value in raw_config["tools"].items()}),
        planning=PlanningConfig(**{key: int(value) for key, value in raw_config["planning"].items()}),
        voice=VoiceConfig(**{**raw_config["voice"],"enabled":_coerce_bool(raw_config["voice"]["enabled"]),"local_only":_coerce_bool(raw_config["voice"]["local_only"]),"input_enabled":_coerce_bool(raw_config["voice"]["input_enabled"]),"output_enabled":_coerce_bool(raw_config["voice"]["output_enabled"]),"raw_audio_persistence":_coerce_bool(raw_config["voice"]["raw_audio_persistence"]),"wake_word_enabled":_coerce_bool(raw_config["voice"]["wake_word_enabled"]),"interruption_enabled":_coerce_bool(raw_config["voice"]["interruption_enabled"]),"temp_directory":_optional_path(raw_config["voice"]["temp_directory"]),"stt_model_path":_optional_path(raw_config["voice"].get("stt_model_path")),"stt_executable":_optional_path(raw_config["voice"].get("stt_executable")),"allowed_audio_directories":tuple(_resolve_path(x) for x in raw_config["voice"]["allowed_audio_directories"])}),
        vision=VisionConfig(**{**raw_config["vision"],"enabled":_coerce_bool(raw_config["vision"]["enabled"]),"local_only":_coerce_bool(raw_config["vision"]["local_only"]),"audit_enabled":_coerce_bool(raw_config["vision"]["audit_enabled"]),"store_image_content":_coerce_bool(raw_config["vision"]["store_image_content"]),"allowed_directories":tuple(_resolve_path(x) for x in raw_config["vision"]["allowed_directories"])}),
        image_generation=ImageGenerationConfig(
            **{
                **raw_config["image_generation"],
                "enabled": _coerce_bool(raw_config["image_generation"]["enabled"]),
                "local_only": _coerce_bool(raw_config["image_generation"]["local_only"]),
                "output_dir": _optional_path(raw_config["image_generation"]["output_dir"]),
                "save_metadata": _coerce_bool(raw_config["image_generation"]["save_metadata"]),
                "allow_overwrite": _coerce_bool(raw_config["image_generation"]["allow_overwrite"]),
                "safety_filter_enabled": _coerce_bool(raw_config["image_generation"]["safety_filter_enabled"]),
            }
        ),
        video_editing=VideoEditingConfig(
            **{
                **raw_config["video_editing"],
                "enabled": _coerce_bool(raw_config["video_editing"]["enabled"]),
                "local_only": _coerce_bool(raw_config["video_editing"]["local_only"]),
                "output_dir": _optional_path(raw_config["video_editing"]["output_dir"]),
                "save_metadata": _coerce_bool(raw_config["video_editing"]["save_metadata"]),
                "allow_overwrite": _coerce_bool(raw_config["video_editing"]["allow_overwrite"]),
                "safety_filter_enabled": _coerce_bool(raw_config["video_editing"]["safety_filter_enabled"]),
            }
        ),
        sync=SyncConfig(**{
            **raw_config["sync"],
            "enabled": _coerce_bool(raw_config["sync"]["enabled"]),
            "automatic_sync": _coerce_bool(raw_config["sync"]["automatic_sync"]),
            "encryption_required": _coerce_bool(raw_config["sync"]["encryption_required"]),
            "sync_raw_audio": _coerce_bool(raw_config["sync"]["sync_raw_audio"]),
            "sync_raw_images": _coerce_bool(raw_config["sync"]["sync_raw_images"]),
            "sync_raw_documents": _coerce_bool(raw_config["sync"]["sync_raw_documents"]),
            "sync_conversations": _coerce_bool(raw_config["sync"]["sync_conversations"]),
            "sync_secrets": _coerce_bool(raw_config["sync"]["sync_secrets"]),
        }),
        web_automation=WebAutomationConfig(**{
            **raw_config["web_automation"],
            "enabled": _coerce_bool(raw_config["web_automation"]["enabled"]),
            "allow_local_targets": _coerce_bool(raw_config["web_automation"]["allow_local_targets"]),
            "allow_http": _coerce_bool(raw_config["web_automation"]["allow_http"]),
            "store_page_content": _coerce_bool(raw_config["web_automation"]["store_page_content"]),
            "store_screenshots": _coerce_bool(raw_config["web_automation"]["store_screenshots"]),
        }),
        interface=InterfaceConfig(**{
            **raw_config["interface"],
            "enabled": _coerce_bool(raw_config["interface"]["enabled"]),
            "open_browser": _coerce_bool(raw_config["interface"]["open_browser"]),
            "allow_remote": _coerce_bool(raw_config["interface"]["allow_remote"]),
            "safe_markdown": _coerce_bool(raw_config["interface"]["safe_markdown"]),
            "show_provider_metadata": _coerce_bool(raw_config["interface"]["show_provider_metadata"]),
            "show_activity_panel": _coerce_bool(raw_config["interface"]["show_activity_panel"]),
            "compact_mode": _coerce_bool(raw_config["interface"]["compact_mode"]),
            "allowed_origins": tuple(str(item) for item in raw_config["interface"]["allowed_origins"]),
        }),
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
