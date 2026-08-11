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
    local_only: bool = True
    auto_remember: bool = False
    auto_session_summary: bool = True
    max_records: int = 2000
    max_search_results: int = 12
    max_context_items: int = 8
    max_context_chars: int = 6000
    audit_enabled: bool = True
    audit_retention: int = 100
    default_retention_days: int = 3650
    sensitive_storage_enabled: bool = False
    consolidation_enabled: bool = True
    secret_detection_enabled: bool = True


@dataclass(frozen=True, slots=True)
class ConversationIntelligenceConfig:
    """Bounded in-memory conversation intelligence settings."""

    enabled: bool = True
    max_turns: int = 12
    max_topics: int = 6
    summary_threshold: int = 8
    reference_resolution: bool = True
    clarification_enabled: bool = True
    max_context_chars: int = 6000


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
    enabled: bool = True
    local_only_default: bool = True
    allow_cloud_providers: bool = False
    default_chat_provider: str = "ollama_text"
    default_reasoning_provider: str = "ollama_text"
    default_coding_provider: str = "ollama_text"
    default_vision_provider: str = "ollama_vision"
    max_providers: int = 32
    max_models_per_provider: int = 32
    max_route_explanations: int = 8
    hardware_discovery_enabled: bool = True
    runtime_enabled: bool = True
    runtime_default_policy: str = "local_preferred"
    runtime_prefer_local: bool = True
    runtime_allow_remote: bool = False
    runtime_allow_paid: bool = False
    runtime_allow_auto_start: bool = False
    runtime_allow_auto_download: bool = False
    runtime_max_concurrent: int = 2
    runtime_default_timeout_seconds: int = 60
    runtime_health_cache_seconds: int = 60
    runtime_max_fallbacks: int = 2
    runtime_resource_reserve_ratio: float = 0.2
    runtime_save_history: bool = True
    runtime_redact_sensitive_values: bool = True


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
    default_mode: str = "plan_only"
    max_agents: int = 64
    max_capabilities_per_agent: int = 32
    max_output_chars: int = 8000
    require_approval_for_high_risk: bool = True
    local_only_default: bool = True
    register_future_placeholders: bool = True
    show_future_agents: bool = True
    max_diagnostic_agents: int = 25
    max_diagnostic_capabilities: int = 40
    default_specialist_mode: str = "plan_only"
    block_critical_future_agents: bool = True


@dataclass(frozen=True, slots=True)
class PrimeConfig:
    enabled: bool = True
    default_execution_mode: str = "plan_only"
    max_plan_steps: int = 8
    max_reason_chars: int = 600
    max_fallbacks: int = 3
    require_approval_for_high_risk: bool = True
    block_critical_risk: bool = True
    local_only: bool = True


@dataclass(frozen=True, slots=True)
class SkillsConfig:
    enabled: bool = True
    allow_external_plugins: bool = False
    allow_mcp: bool = False
    default_execution_mode: str = "plan_only"
    max_skills: int = 512
    max_capabilities_per_skill: int = 32
    max_output_chars: int = 8000
    require_approval_for_side_effects: bool = True
    block_secrets_access: bool = True


@dataclass(frozen=True, slots=True)
class ResearchConfig:
    """Local-first, bounded Research Agent settings."""

    enabled: bool = True
    default_depth: str = "standard"
    max_plan_steps: int = 5
    max_evidence_items: int = 5
    max_snippet_chars: int = 320
    max_summary_chars: int = 1200
    allow_web_read_only: bool = True
    allow_external_search_api: bool = False
    save_history: bool = True
    local_only: bool = True
    require_citations_for_web_claims: bool = True
    allow_external_search: bool = False
    allow_browser_retrieval: bool = True
    allow_github: bool = True
    allow_mcp: bool = True
    allow_plugins: bool = True
    prefer_primary_sources: bool = True
    enable_counterevidence: bool = True
    max_queries_quick: int = 2
    max_queries_standard: int = 5
    max_queries_deep: int = 8
    max_sources_quick: int = 4
    max_sources_standard: int = 8
    max_sources_deep: int = 12
    max_pages_per_domain: int = 3
    max_chars_per_source: int = 6000
    max_total_chars: int = 24000
    max_followup_rounds: int = 2
    search_timeout_seconds: int = 20
    retrieval_timeout_seconds: int = 20
    total_timeout_seconds: int = 120
    max_concurrent_requests: int = 2
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    max_history_items: int = 25
    redact_sensitive_values: bool = True


@dataclass(frozen=True, slots=True)
class CodingConfig:
    """Read-only and plan-only Coding Agent settings."""

    enabled: bool = True
    default_mode: str = "plan_only"
    max_plan_steps: int = 6
    max_files_listed: int = 20
    max_diff_chars: int = 4000
    max_history_items: int = 25
    allow_write_operations: bool = False
    allow_command_execution: bool = False
    require_approval_for_write: bool = True
    require_approval_for_push: bool = True
    block_secrets_access: bool = True

@dataclass(frozen=True, slots=True)
class KnowledgeConfig:
    enabled: bool=True; default_retrieval_mode:str="auto"; allow_persistent_index:bool=True; allow_remote_embeddings:bool=False; allow_remote_reranking:bool=False; auto_admit_research:bool=False; max_sources:int=100; max_records:int=1000; max_chunks_per_record:int=50; max_chunk_chars:int=800; chunk_overlap_chars:int=80; max_results:int=5; max_context_chunks:int=5; max_context_chars:int=4000; prefer_fresh:bool=True; prefer_primary_sources:bool=True; enable_lexical:bool=True; enable_semantic:bool=False; enable_hybrid:bool=False; enable_reranking:bool=False; save_history:bool=True; redact_sensitive_values:bool=True

@dataclass(frozen=True, slots=True)
class OrchestratorConfig:
    enabled:bool=True;max_parallel_agents:int=2;max_sessions:int=25;default_timeout_seconds:int=180;max_retry_count:int=1;enable_parallel_execution:bool=True;enable_partial_results:bool=True;enable_recovery:bool=True;enable_event_log:bool=True;enable_metrics:bool=True;enable_audit:bool=True;max_context_versions:int=10;max_event_history:int=200;max_message_history:int=100;max_delegation_depth:int=3


@dataclass(frozen=True, slots=True)
class DocumentsConfig:
    enabled: bool = True; default_mode: str = "plan_only"; max_file_bytes: int = 1000000; max_extract_chars: int = 4000; max_history_items: int = 25; allow_pdf: bool = False; allow_office: bool = False; allow_ocr: bool = False; allow_cloud_parsing: bool = False; allow_bulk_ingestion: bool = False; save_history: bool = True; store_extracted_content: bool = False; local_only: bool = True

@dataclass(frozen=True, slots=True)
class BrowserAgentConfig:
    enabled: bool = True; default_mode: str = "read_only"; allow_interactive: bool = False; allow_login: bool = False; allow_forms: bool = False; allow_purchases: bool = False; allow_downloads: bool = False; allow_cookies: bool = False; allow_sessions: bool = False; allow_external_automation: bool = False; max_history_items: int = 25; save_history: bool = True; local_only: bool = True

@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    enabled: bool = True; default_mode: str = "plan_only"; allow_background_runner: bool = False; allow_os_cron: bool = False; allow_task_scheduler: bool = False; allow_notifications: bool = False; minimum_cadence_minutes: int = 60; max_runs: int = 100; max_history_items: int = 25; save_history: bool = True; local_only: bool = True

@dataclass(frozen=True, slots=True)
class CommunicationConfig:
    enabled: bool = True; default_mode: str = "draft_only"; allow_sending: bool = False; allow_external_providers: bool = False; allow_contact_access: bool = False; allow_bulk_messages: bool = False; allow_social_posting: bool = False; allow_credentials_access: bool = False; max_history_items: int = 25; save_history: bool = True; local_only: bool = True; external_enabled: bool = True; external_require_approval: bool = True; external_allow_attachments: bool = False; external_allow_scheduled_send: bool = False; external_max_message_chars: int = 4000; external_max_attachments: int = 0; external_max_sends_per_window: int = 3; external_rate_window_seconds: int = 60; external_max_retries: int = 1; external_duplicate_protection: bool = True; external_redact_sensitive_values: bool = True; external_block_secrets: bool = True

@dataclass(frozen=True, slots=True)
class AdaptersConfig:
    enabled: bool = True; default_mode: str = "plan_only"; allow_mcp_runtime: bool = False; allow_plugin_install: bool = False; allow_external_tool_execution: bool = False; allow_network_connectors: bool = False; allow_webhooks: bool = False; allow_command_execution: bool = False; allow_file_writes: bool = False; allow_message_sending: bool = False; allow_background_servers: bool = False; allow_credentials_access: bool = False; max_plan_steps: int = 8; max_manifests_listed: int = 25; max_history_items: int = 25; save_history: bool = True; redact_sensitive_values: bool = True

@dataclass(frozen=True, slots=True)
class AdvancedModelsConfig:
    enabled: bool = True; default_mode: str = "planning_only"; local_first: bool = True; allow_cloud_providers: bool = False; allow_provider_install: bool = False; allow_model_download: bool = False; allow_runtime_start: bool = False; allow_docker: bool = False; allow_gpu_diagnostics: bool = False; allow_credentials_access: bool = False; max_plan_steps: int = 8; max_providers_listed: int = 25; max_history_items: int = 25; save_history: bool = True; redact_sensitive_values: bool = True; block_cloud_without_approval: bool = True; require_approval_for_runtime: bool = True; require_approval_for_downloads: bool = True

@dataclass(frozen=True, slots=True)
class EvaluationConfig:
    enabled: bool = True; default_mode: str = "local_only"; allow_cloud_telemetry: bool = False; allow_remote_logging: bool = False; allow_background_runner: bool = False; save_history: bool = True; max_cases_per_suite: int = 100; max_output_chars: int = 8000; max_history_items: int = 25; redact_sensitive_values: bool = True; block_private_paths: bool = True; require_local_only: bool = True; fail_on_truthfulness_mismatch: bool = True; fail_on_secret_leakage: bool = True; fail_on_path_leakage: bool = True

@dataclass(frozen=True, slots=True)
class ReleaseReadinessConfig:
    enabled: bool = True; validation_only: bool = True; require_all_blocking_gates: bool = True; allow_tag_creation: bool = False; allow_release_creation: bool = False; allow_deployment: bool = False; require_clean_repository: bool = True; require_origin_match: bool = True; require_vercel_status_only: bool = True; max_gates: int = 50; max_output_chars: int = 8000

@dataclass(frozen=True, slots=True)
class ExternalIntegrationsConfig:
    enabled: bool = True; default_mode: str = "metadata_only"; allow_remote_providers: bool = False; allow_paid_providers: bool = False; allow_external_execution: bool = False; require_approval_for_external_actions: bool = True; block_secret_egress: bool = True; max_providers: int = 32; max_history_items: int = 50; health_cache_seconds: int = 60; max_retries: int = 1

@dataclass(frozen=True, slots=True)
class ExternalProviderFlagsConfig:
    telegram_enabled: bool = False; discord_enabled: bool = False; email_smtp_enabled: bool = False; email_api_enabled: bool = False; slack_enabled: bool = False; matrix_enabled: bool = False; whatsapp_enabled: bool = False; github_enabled: bool = False; mcp_local_enabled: bool = False; mcp_remote_enabled: bool = False; external_plugins_enabled: bool = False; nvidia_nim_enabled: bool = False; openai_compatible_enabled: bool = False

@dataclass(frozen=True, slots=True)
class TelegramConfig:
    enabled:bool=False; transport:str="long_polling"; polling_enabled:bool=False; webhook_enabled:bool=False; require_authorized_chat:bool=True; allow_inbound_text:bool=True; allow_outbound_text:bool=True; allow_commands:bool=True; allow_media:bool=False; allow_documents:bool=False; allow_voice:bool=False; allow_group_chats:bool=False; allow_channel_posts:bool=False; allow_scheduled_send:bool=False; require_approval_for_send:bool=True; max_message_chars:int=3900; max_updates_per_poll:int=20; poll_timeout_seconds:int=10; max_retries:int=2; rate_limit_window:int=60; max_sends_per_window:int=5; save_history:bool=True; redact_sensitive_values:bool=True

@dataclass(frozen=True,slots=True)
class DiscordConfig:
 enabled:bool=False;transport:str="bot_api";allow_send:bool=False;allow_inbound:bool=False;allow_webhook:bool=False;allow_attachments:bool=False;require_approval:bool=True;max_message_chars:int=1900;max_sends_per_window:int=3;max_retries:int=1
@dataclass(frozen=True,slots=True)
class EmailConnectorConfig:
 smtp_enabled:bool=False;api_enabled:bool=False;allow_send:bool=False;allow_read:bool=False;allow_html:bool=False;allow_attachments:bool=False;allow_cc:bool=False;allow_bcc:bool=False;allow_bulk:bool=False;require_approval:bool=True;max_recipients:int=1;max_body_chars:int=10000;max_retries:int=1
@dataclass(frozen=True,slots=True)
class SlackConfig:
 enabled:bool=False;allow_send:bool=False;allow_inbound:bool=False;allow_attachments:bool=False;require_approval:bool=True;max_message_chars:int=3900;max_sends_per_window:int=3;max_retries:int=1

@dataclass(frozen=True,slots=True)
class GitHubProviderConfig:
 enabled:bool=False;transport:str="gh_cli";allow_read:bool=True;allow_issue_write:bool=False;allow_pr_write:bool=False;allow_release_write:bool=False;allow_merge:bool=False;allow_workflow_execute:bool=False;allow_admin:bool=False;allowed_repositories:tuple[str,...]=("yeshwanthpullur/JarvisOS",);require_approval_for_writes:bool=True;max_results:int=20;max_body_chars:int=4000;max_retries:int=1;health_cache_seconds:int=60;save_history:bool=True;redact_sensitive_values:bool=True

@dataclass(frozen=True,slots=True)
class MCPConfig:
 enabled:bool=True;allow_local_stdio:bool=True;allow_local_http:bool=True;allow_remote_http:bool=False;allow_tool_execution:bool=False;allow_resource_read:bool=True;allow_prompts:bool=False;allow_installation:bool=False;allow_scheduled_execution:bool=False;require_approval_for_side_effects:bool=True;max_servers:int=16;max_tools_per_server:int=50;max_resources_per_server:int=50;max_result_chars:int=8000;max_concurrent_calls:int=2;startup_timeout_seconds:int=10;call_timeout_seconds:int=30;max_retries:int=1;health_cache_seconds:int=60;save_history:bool=True;max_history_items:int=100;redact_sensitive_values:bool=True

@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    enabled: bool = True; default_mode: str = "plan_only"; local_first: bool = True; allow_file_writes: bool = True; allow_command_execution: bool = True; allow_git_writes: bool = True; allow_browser_read: bool = True; allow_browser_actions: bool = False; allow_notifications: bool = True; allow_scheduler_runner: bool = True; allow_communication_send: bool = False; allow_mcp_execution: bool = False; allow_model_runtime_start: bool = False; allow_external_network: bool = False; allow_background_execution: bool = False; allow_secrets_access: bool = False; allow_credentials_access: bool = False; require_approval_for_side_effects: bool = True; block_critical_actions: bool = True; max_plan_steps: int = 8; max_history_items: int = 50; save_history: bool = True; redact_sensitive_values: bool = True; block_private_paths: bool = True
@dataclass(frozen=True, slots=True)
class ApprovalsConfig:
    enabled: bool = True; default_mode: str = "explicit_only"; require_explicit_approval: bool = True; allow_implied_approval: bool = False; allow_broad_approval: bool = False; allow_permanent_approval: bool = False; allow_secret_access_approval: bool = False; allow_critical_action_approval: bool = False; default_ttl_seconds: int = 900; max_pending: int = 50; max_history_items: int = 100; save_history: bool = True; redact_sensitive_values: bool = True; block_private_paths: bool = True; require_resource_scope: bool = True; require_permission_scope: bool = True
@dataclass(frozen=True, slots=True)
class BrokerConfig:
    enabled: bool = True; default_mode: str = "dry_run"; allow_actual_execution: bool = True; allow_unapproved_execution: bool = False; require_policy_check: bool = True; require_approval_for_side_effects: bool = True; require_permission_scope: bool = True; allow_external_tools: bool = False; allow_network_tools: bool = False; allow_background_tools: bool = False; block_critical_actions: bool = True; max_plan_steps: int = 8; max_history_items: int = 50; save_history: bool = True; redact_sensitive_values: bool = True; block_private_paths: bool = True; store_payloads: bool = False


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

@dataclass(frozen=True,slots=True)
class VoiceConfig:
 enabled:bool=False; mode:str="off"; language:str="en-US"; local_only:bool=True; privacy_mode:str="standard"; input_enabled:bool=False; output_enabled:bool=False; input_backend:str="offline-stt"; output_backend:str="windows-sapi"; input_device:str|None=None; output_device:str|None=None; confidence_threshold:float=.75; confirmation_threshold:float=.6; max_capture_seconds:int=30; silence_timeout_seconds:int=3; max_audio_size:int=20000000; max_transcript_length:int=4000; max_spoken_response_length:int=500; max_auto_speech_chars:int=12000; rate:int=0; volume:int=100; raw_audio_persistence:bool=False; retention_limit:int=0; temp_audio_lifetime_seconds:int=300; voice_input_audit_retention:int=50; stt_model_path:Path|None=None; stt_executable:Path|None=None; wake_word_enabled:bool=False; wake_word_backend:str|None=None; activation_phrase:str="jarvis"; interruption_enabled:bool=True; temp_directory:Path|None=None; allowed_audio_directories:tuple[Path,...]=()

@dataclass(frozen=True,slots=True)
class VisionConfig:
 enabled:bool=True; local_only:bool=True; privacy_mode:str="standard"; provider:str="ollama"; model:str="llava"; ollama_host:str="http://127.0.0.1:11434"; max_image_size:int=20000000; timeout_seconds:int=60; audit_enabled:bool=True; audit_retention:int=100; store_image_content:bool=False; allowed_directories:tuple[Path,...]=()

@dataclass(frozen=True, slots=True)
class ImageGenerationConfig:
    enabled: bool = False
    default_provider: str = "unavailable"
    local_only: bool = True
    output_dir: Path | None = None
    max_prompt_chars: int = 600
    max_negative_prompt_chars: int = 300
    save_metadata: bool = True
    allow_overwrite: bool = False
    safety_filter_enabled: bool = True


@dataclass(frozen=True, slots=True)
class VideoEditingConfig:
    enabled: bool = False
    default_provider: str = "unavailable"
    local_only: bool = True
    output_dir: Path | None = None
    max_prompt_chars: int = 600
    max_source_media_items: int = 12
    save_metadata: bool = True
    allow_overwrite: bool = False
    safety_filter_enabled: bool = True

@dataclass(frozen=True, slots=True)
class SyncConfig:
    enabled: bool = False
    mode: str = "off"
    adapter: str = "local-queue"
    automatic_sync: bool = False
    remote_endpoint: str | None = None
    maximum_item_size: int = 8192
    maximum_queue_items: int = 100
    maximum_batch_size: int = 10
    maximum_attempts: int = 3
    completed_retention_count: int = 25
    audit_retention_count: int = 100
    maximum_nested_depth: int = 4
    maximum_string_length: int = 1000
    conflict_strategy: str = "manual"
    encryption_required: bool = True
    sync_raw_audio: bool = False
    sync_raw_images: bool = False
    sync_raw_documents: bool = False
    sync_conversations: bool = False
    sync_secrets: bool = False

@dataclass(frozen=True, slots=True)
class WebAutomationConfig:
    enabled: bool = True
    mode: str = "read_only"
    adapter: str = "read-only-http"
    allow_local_targets: bool = False
    allow_http: bool = False
    audit_retention: int = 100
    action_timeout_seconds: int = 8
    maximum_redirects: int = 5
    maximum_response_bytes: int = 524288
    maximum_preview_characters: int = 2000
    store_page_content: bool = False
    store_screenshots: bool = False


@dataclass(frozen=True, slots=True)
class InterfaceConfig:
    """Local desktop interface security, display, and bounded API settings."""

    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8765
    open_browser: bool = True
    theme: str = "system"
    default_view: str = "chat"
    event_transport: str = "sse"
    max_request_size: int = 65536
    max_response_size: int = 262144
    max_log_entries: int = 200
    max_activity_entries: int = 200
    max_history_messages: int = 200
    request_timeout: int = 120
    event_timeout: int = 30
    allow_remote: bool = False
    allowed_origins: tuple[str, ...] = (
        "http://127.0.0.1:8765",
        "http://localhost:8765",
    )
    session_token_lifetime: int = 14400
    safe_markdown: bool = True
    show_provider_metadata: bool = True
    show_activity_panel: bool = True
    compact_mode: bool = False


@dataclass(frozen=True, slots=True)
class PluginsConfig:
    """Plugin loading policy and location."""

    enabled: bool
    plugin_dir: Path
    allow_user_plugins: bool
    auto_discover: bool
    auto_enable: bool
    compatibility_version: str
    allow_external: bool = True
    allow_local_development: bool = True
    allow_inprocess_external: bool = False
    allow_subprocess: bool = False
    allow_network: bool = False
    allow_filesystem_write: bool = False
    allow_installation: bool = False
    allow_updates: bool = False
    allow_uninstall: bool = False
    require_integrity_check: bool = True
    require_approval_for_enable: bool = True
    require_approval_for_side_effects: bool = True
    max_registered: int = 64
    max_enabled: int = 8
    max_output_chars: int = 8000
    execution_timeout_seconds: int = 30
    max_concurrent: int = 1
    save_history: bool = True
    max_history_items: int = 100
    redact_sensitive_values: bool = True


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
    automation_enabled: bool = True
    automation_mode: str = "planning_only"
    automation_adapter: str = "planning-only"
    audit_retention: int = 100
    live_control_enabled: bool = False
    store_private_data: bool = False


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
    prime: PrimeConfig = field(default_factory=PrimeConfig)
    skills: SkillsConfig = field(default_factory=SkillsConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    coding: CodingConfig = field(default_factory=CodingConfig)
    knowledge_index: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    documents: DocumentsConfig = field(default_factory=DocumentsConfig)
    browser: BrowserAgentConfig = field(default_factory=BrowserAgentConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    communication: CommunicationConfig = field(default_factory=CommunicationConfig)
    adapters: AdaptersConfig = field(default_factory=AdaptersConfig)
    advanced_models: AdvancedModelsConfig = field(default_factory=AdvancedModelsConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    release_readiness: ReleaseReadinessConfig = field(default_factory=ReleaseReadinessConfig)
    external_integrations: ExternalIntegrationsConfig = field(default_factory=ExternalIntegrationsConfig)
    external_provider_flags: ExternalProviderFlagsConfig = field(default_factory=ExternalProviderFlagsConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    email_connector: EmailConnectorConfig = field(default_factory=EmailConnectorConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    github_provider: GitHubProviderConfig = field(default_factory=GitHubProviderConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    approvals: ApprovalsConfig = field(default_factory=ApprovalsConfig)
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    conversation: ConversationIntelligenceConfig = field(default_factory=ConversationIntelligenceConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    planning: PlanningConfig = field(default_factory=PlanningConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    image_generation: ImageGenerationConfig = field(default_factory=ImageGenerationConfig)
    video_editing: VideoEditingConfig = field(default_factory=VideoEditingConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    web_automation: WebAutomationConfig = field(default_factory=WebAutomationConfig)
    interface: InterfaceConfig = field(default_factory=InterfaceConfig)

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
