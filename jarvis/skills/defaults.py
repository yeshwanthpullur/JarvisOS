"""Built-in and future skill manifests for safe discovery."""

from __future__ import annotations

from .models import SkillCapability as C, SkillExecutionMode as E, SkillManifest as M, SkillPermission as P, SkillRiskLevel as R, SkillStatus as S
from .registry import SkillRegistry


def _ready(skill_id: str, category: str, capability: str, description: str, *, permissions: tuple[P, ...] = ()) -> M:
    approval = bool(permissions)
    return M(skill_id, skill_id.replace("_", " ").title(), description, "1.0", "JARVIS OS", category, S.READY, (C(capability, description, category, requires_approval=approval),), required_permissions=permissions, requires_approval=approval, enabled=True, execution_mode=E.DRY_RUN if approval else E.PLAN_ONLY, limitations=("Metadata-only Phase 3 registration; existing subsystem authority remains authoritative.",))


def _future(skill_id: str, category: str, permission: P | None = None) -> M:
    permissions = (permission,) if permission else ()
    return M(skill_id, skill_id.replace("_", " ").title(), "Future integration placeholder; no external connector or execution is configured.", "0.0", "JARVIS OS", category, S.FUTURE, (C(category, "Future plan-only capability.", category, risk_level=R.HIGH if permission else R.LOW, requires_approval=bool(permission)),), required_permissions=permissions, requires_approval=bool(permission), risk_level=R.HIGH if permission else R.LOW, enabled=False, execution_mode=E.DISABLED, limitations=("Unavailable in Phase 3.",))


def build_default_skill_registry() -> SkillRegistry:
    builtins = (
        _ready("conversation_skill", "conversation", "conversation", "Safe conversation metadata."),
        _ready("memory_status_skill", "memory", "memory_status", "Read bounded memory status."),
        _ready("memory_search_skill", "memory", "memory_search", "Search memory through existing authority.", permissions=(P.READ_MEMORY_REFS,)),
        _ready("project_status_skill", "system", "project_status", "Read bounded project health.", permissions=(P.SYSTEM_STATUS,)),
        _ready("limitations_skill", "system", "limitations", "Read bounded limitation metadata.", permissions=(P.SYSTEM_STATUS,)),
        _ready("vision_status_skill", "vision", "vision_status", "Read local vision status."),
        _ready("research_planning_skill", "research", "research_planning", "Plan bounded research requests."),
        _ready("evidence_summary_skill", "research", "evidence_summary", "Summarize bounded evidence."),
        _ready("source_policy_skill", "research", "source_policy", "Explain safe source policy."),
        _ready("project_research_skill", "research", "project_research", "Plan repo and project research."),
        _ready("web_research_skill", "research", "web_research", "Plan read-only web research.", permissions=(P.BROWSER_READ,)),
        _ready("coding_planning_skill", "coding", "coding_planning", "Plan bounded code changes without editing files."),
        _ready("repo_inspection_skill", "coding", "repo_inspection", "Read bounded Git repository metadata.", permissions=(P.GIT_READ,)),
        _ready("diff_review_skill", "coding", "diff_review", "Review bounded tracked diff metadata.", permissions=(P.GIT_READ,)),
        _ready("test_planning_skill", "coding", "test_planning", "Plan focused and regression test coverage."),
        _ready("release_review_skill", "coding", "release_review", "Review release prerequisites without tagging or pushing.", permissions=(P.GIT_READ,)),
        _ready("document_planning_skill", "documents", "document_planning", "Plan explicit bounded document work."),
        _ready("document_text_extraction_skill", "documents", "document_text_extraction", "Extract bounded text from approved safe text files.", permissions=(P.READ_FILES,)),
        _ready("document_summary_skill", "documents", "document_summary", "Create bounded local extractive summaries."),
        _ready("document_qa_planning_skill", "documents", "document_question_answering", "Plan evidence-linked document Q&A."),
        _ready("browser_planning_skill", "browser", "browser_planning", "Plan read-only browser tasks."),
        _ready("browser_source_policy_skill", "browser", "browser_source_policy", "Explain read-only source policy."),
        _ready("browser_summary_skill", "browser", "browser_summarization", "Plan bounded webpage summaries.", permissions=(P.BROWSER_READ,)),
        _ready("scheduler_planning_skill", "workflow", "scheduler_planning", "Plan bounded schedules without creating active jobs."),
        _ready("schedule_validation_skill", "workflow", "schedule_validation", "Validate cadence and recurrence policy."),
        _ready("communication_drafting_skill", "communication", "communication_drafting", "Create bounded unsent drafts."),
        _ready("communication_provider_status_skill", "communication", "communication_provider_status", "Show disabled provider metadata."),
        _ready("anti_spam_policy_skill", "communication", "anti_spam_policy", "Block abuse and bulk messaging."),
        _ready("communication_provider_health_skill", "communication", "communication_provider_health", "Inspect side-effect-free provider health metadata."),
        _ready("destination_validation_skill", "communication", "destination_validation", "Validate an explicit bounded destination."),
        _ready("external_message_planning_skill", "communication", "external_message_planning", "Plan an external message without sending."),
        _ready("external_message_safety_skill", "communication", "external_message_safety", "Classify outbound content and block secrets."),
        _ready("external_data_egress_skill", "communication", "external_data_egress", "Classify external message data egress."),
        _ready("outbound_rate_limit_skill", "communication", "outbound_rate_limit", "Inspect bounded outbound rate policy."),
        _ready("duplicate_send_protection_skill", "communication", "duplicate_send_protection", "Plan content-free duplicate suppression."),
        _ready("telegram_provider_status_skill", "communication", "telegram_provider_status", "Inspect Telegram readiness without exposing credentials."),
        _ready("telegram_identity_skill", "communication", "telegram_identity", "Verify bounded Telegram bot identity metadata.", permissions=(P.NETWORK_ACCESS,)),
        _ready("telegram_pairing_skill", "communication", "telegram_pairing", "Create expiring single-use private-chat pairing."),
        _ready("telegram_destination_validation_skill", "communication", "telegram_destination_validation", "Validate explicit Telegram chat references."),
        _ready("telegram_text_receive_skill", "communication", "telegram_text_receive", "Normalize authorized text-only Telegram updates.", permissions=(P.NETWORK_ACCESS,)),
        _ready("telegram_text_send_skill", "communication", "telegram_text_send", "Send bounded text only through approval and Broker.", permissions=(P.SEND_MESSAGE,P.NETWORK_ACCESS)),
        _ready("telegram_polling_skill", "communication", "telegram_polling", "Run explicit bounded long-poll cycles.", permissions=(P.NETWORK_ACCESS,)),
        _ready("communication_attachment_validation_skill", "communication", "communication_attachment_validation", "Validate attachment metadata with upload disabled."),
        _ready("adapter_planning_skill", "developer", "adapter_planning", "Plan disabled adapters and integrations."),
        _ready("adapter_manifest_skill", "developer", "adapter_manifest", "Inspect bounded adapter manifests."),
        _ready("adapter_permission_review_skill", "developer", "adapter_permission_review", "Review ungranted adapter permissions."),
        _ready("mcp_planning_skill", "developer", "mcp_planning", "Plan MCP integrations without starting servers."),
        _ready("advanced_model_planning_skill", "system", "advanced_model_planning", "Plan advanced providers without installation or startup."),
        _ready("model_provider_comparison_skill", "system", "model_provider_comparison", "Compare provider metadata without benchmarks."),
        _ready("hardware_capability_planning_skill", "system", "hardware_capability_planning", "Show broad safe hardware categories."),
        _ready("evaluation_routing_skill", "system", "evaluation_routing", "Run deterministic local routing fixtures."),
        _ready("capability_truthfulness_skill", "system", "capability_truthfulness", "Verify disabled capabilities are not reported ready."),
        _ready("local_observability_skill", "system", "local_observability", "Create bounded local metadata snapshots."),
        _ready("image_workflow_skill", "image", "image_workflow", "Validate and plan image workflows only."),
        _ready("video_workflow_skill", "video", "video_workflow", "Validate and plan video workflows only."),
        _ready("web_read_only_skill", "web", "web_read", "Read public web metadata under policy.", permissions=(P.BROWSER_READ,)),
        _ready("sync_status_skill", "sync", "sync_status", "Read local sync queue status."),
        _ready("voice_status_skill", "conversation", "voice_status", "Read voice subsystem status."),
        _ready("execution_policy_skill", "system", "execution_policy", "Classify controlled execution policy and risk."),
        _ready("approval_request_skill", "system", "approval_request", "Manage explicit scope-bound approvals."),
        _ready("broker_validation_skill", "tools", "broker_validation", "Validate policy, approval, permissions, and capabilities."),
        _ready("file_write_execution_skill", "files", "approved_file_write", "Execute scoped approved text-file operations.", permissions=(P.WRITE_FILES,)),
        _ready("approved_command_execution_skill", "coding", "approved_command_execution", "Run allowlisted approved commands with shell disabled.", permissions=(P.EXECUTE_COMMANDS,)),
        _ready("git_commit_skill", "coding", "approved_git_commit", "Create an approved normal Git commit after protected-file scans.", permissions=(P.GIT_WRITE,)),
        _ready("git_push_skill", "coding", "approved_git_push", "Push an exact approved branch to an allowed remote.", permissions=(P.GIT_WRITE,)),
        _ready("browser_public_read_skill", "browser", "approved_public_read", "Fetch bounded public text with SSRF protection.", permissions=(P.BROWSER_READ,P.NETWORK_ACCESS)),
        _ready("local_notification_execution_skill", "communication", "approved_local_notification", "Display a bounded local-only notification.", permissions=(P.SEND_MESSAGE,)),
        _ready("scheduler_manual_runner_skill", "workflow", "approved_manual_scheduler", "Manually run bounded due local notification jobs.", permissions=(P.EXECUTE_COMMANDS,)),
    )
    future = (
        _future("academic_search_skill", "research", P.NETWORK_ACCESS), _future("citation_manager_skill", "research", P.READ_CONTEXT), _future("external_search_api_skill", "research", P.NETWORK_ACCESS),
        _future("mcp_gateway_skill", "developer", P.NETWORK_ACCESS), _future("telegram_skill", "communication", P.SEND_MESSAGE), _future("telegram_attachment_skill", "communication", P.SEND_MESSAGE), _future("telegram_voice_skill", "communication", P.MICROPHONE_ACCESS), _future("telegram_video_skill", "communication", P.SEND_MESSAGE), _future("telegram_group_skill", "communication", P.SEND_MESSAGE), _future("telegram_channel_post_skill", "communication", P.SEND_MESSAGE), _future("telegram_scheduled_send_skill", "communication", P.SEND_MESSAGE), _future("telegram_webhook_skill", "communication", P.NETWORK_ACCESS), _future("discord_skill", "communication", P.SEND_MESSAGE),
        _future("email_skill", "email", P.SEND_EMAIL), _future("calendar_skill", "calendar", P.CALENDAR_WRITE),
        _future("slack_send_skill", "communication", P.SEND_MESSAGE), _future("whatsapp_send_skill", "communication", P.SEND_MESSAGE), _future("external_attachment_send_skill", "communication", P.SEND_MESSAGE), _future("scheduled_external_send_skill", "communication", P.SEND_MESSAGE), _future("bulk_message_skill", "communication", P.SEND_MESSAGE),
        _future("browser_write_skill", "browser", P.BROWSER_WRITE), _future("code_edit_skill", "coding", P.WRITE_FILES),
        _future("command_execution_skill", "coding", P.EXECUTE_COMMANDS), _future("auto_commit_skill", "coding", P.GIT_WRITE),
        _future("auto_push_skill", "coding", P.GIT_WRITE), _future("dependency_install_skill", "coding", P.EXECUTE_COMMANDS),
        _future("research_agent_skill", "research", P.NETWORK_ACCESS), _future("document_intelligence_skill", "documents", P.READ_FILES),
        _future("robotics_skill", "robotics", P.HARDWARE_WRITE), _future("drone_skill", "drone", P.HARDWARE_WRITE),
        _future("social_media_skill", "social", P.SOCIAL_POST),
        _future("scheduler_skill", "workflow", P.EXECUTE_COMMANDS),
        _future("document_ocr_skill", "documents", P.READ_FILES), _future("document_cloud_parser_skill", "documents", P.NETWORK_ACCESS),
        _future("browser_login_skill", "browser", P.BROWSER_WRITE), _future("browser_form_skill", "browser", P.BROWSER_WRITE), _future("browser_purchase_skill", "browser", P.BROWSER_WRITE),
        _future("scheduler_runtime_skill", "workflow", P.EXECUTE_COMMANDS), _future("notification_send_skill", "communication", P.SEND_MESSAGE),
        _future("mcp_runtime_skill", "developer", P.EXECUTE_COMMANDS), _future("plugin_install_skill", "developer", P.EXECUTE_COMMANDS), _future("external_tool_execution_skill", "developer", P.EXECUTE_COMMANDS),
        _future("nemotron_runtime_skill", "system", P.EXECUTE_COMMANDS), _future("nvidia_nim_runtime_skill", "system", P.EXECUTE_COMMANDS), _future("vllm_runtime_skill", "system", P.EXECUTE_COMMANDS), _future("llama_cpp_runtime_skill", "system", P.EXECUTE_COMMANDS), _future("model_download_skill", "system", P.NETWORK_ACCESS),
    )
    return SkillRegistry(builtins + future, max_skills=128)
