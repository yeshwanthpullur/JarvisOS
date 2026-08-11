"""Truthful specialist agent metadata for current and future JARVIS systems."""

from __future__ import annotations

from .models import AgentCapability as C, AgentCapabilityType as T, AgentRegistryEntry as E, AgentRiskLevel as R, AgentStatus as S
from .registry import AgentRegistry


def _cap(name: str, kind: T, description: str, *, risk: R = R.LOW, approval: bool = False, side_effects: tuple[str, ...] = (), permissions: tuple[str, ...] = (), limitations: tuple[str, ...] = ()) -> C:
    return C(name, kind, description, side_effects=side_effects, required_permissions=permissions, risk_level=risk, requires_approval=approval, enabled=not bool(limitations and "future" in limitations), limitations=limitations)


def _entry(name: str, description: str, capabilities: tuple[C, ...], *, ready: bool, health: str, reason: str) -> E:
    return E(name, name.replace("_", " ").title(), description, status=S.READY if ready else S.UNAVAILABLE, capabilities=capabilities, enabled=ready, health=health, reason=reason, owner_subsystem=name.removesuffix("_agent"))


def specialist_entries(*, vision_ready: bool = False) -> tuple[E, ...]:
    current = (
        _entry("conversation_agent", "Bounded Conversation Intelligence responses.", (_cap("conversation", T.CONVERSATION, "Conversation, clarification, follow-up handling, and summaries."),), ready=True, health="ready", reason="Conversation Intelligence is implemented."),
        _entry("memory_agent", "Read-only memory retrieval and lifecycle diagnostics.", (_cap("memory", T.MEMORY, "Memory status, search, retrieval, and lifecycle diagnostics."),), ready=True, health="ready", reason="Persistent Memory is implemented; mutation remains command-authorized."),
        _entry("vision_agent", "Local-only image analysis without hidden camera access.", (_cap("vision", T.VISION, "Image analysis, description, and vision status.", limitations=("No hidden camera access.",)),), ready=vision_ready, health="ready" if vision_ready else "partial", reason="A local Ollama vision route is ready." if vision_ready else "Vision foundation exists, but a ready local model was not detected for this runtime."),
        _entry("image_agent", "Image workflow validation and dry-run planning.", (_cap("image", T.IMAGE, "Image prompt validation, safety review, and workflow planning."),), ready=True, health="workflow_foundation", reason="The image workflow planner is available; real generation requires a configured provider."),
        _entry("video_agent", "Non-destructive video workflow validation and planning.", (_cap("video", T.VIDEO, "Video input validation, safety review, and dry-run planning."),), ready=True, health="workflow_foundation", reason="The video workflow planner is available; real editing requires a configured provider/tool."),
        _entry("web_agent", "Policy-controlled read-only public web inspection.", (_cap("web", T.WEB, "Read-only web status and safe page inspection.", permissions=("browser_read",), limitations=("No login, forms, purchases, or browser writes.",)),), ready=True, health="partial_read_only", reason="Read-only web inspection is implemented."),
        _entry("sync_agent", "Local queue status and diagnostics.", (_cap("sync", T.SYNC, "Local sync queue status and bounded diagnostics."),), ready=True, health="partial_local_queue", reason="The local queue foundation works; no remote backend exists."),
        _entry("voice_agent", "Explicit voice input/output status and controls.", (_cap("voice", T.CONVERSATION, "Explicit voice status, listen, speech output, and playback controls.", permissions=("explicit_microphone_command",), limitations=("No hidden listening or wake word.",)),), ready=True, health="partial_local", reason="Local voice foundations are implemented; runtime hardware/model availability varies."),
        _entry("project_agent", "Project health, roadmap, and status diagnostics.", (_cap("project_status", T.SYSTEM, "Bounded project and roadmap status."),), ready=True, health="ready", reason="Project tracking commands are implemented."),
        _entry("limitations_agent", "Limitations register diagnostics.", (_cap("limitations", T.SYSTEM, "Bounded limitation status and evidence."),), ready=True, health="ready", reason="The limitations register is implemented."),
        _entry("research_agent", "Read-only research planning and bounded evidence summaries.", (_cap("research", T.RESEARCH, "Research planning, evidence requirements, and bounded summaries.", limitations=("Read-only and plan-first; evidence retrieval is limited when read-only web access is unavailable.",)),), ready=True, health="partial_research", reason="Research planning is ready; source retrieval remains bounded by the existing read-only web and approved document foundations."),
        _entry("coding_agent", "Read-only repository diagnostics and plan-only coding support.", (
            _cap("repo_inspection", T.CODING, "Bounded branch, HEAD, status, and file-list inspection."),
            _cap("coding_planning", T.CODING, "Plan coding changes and tests without modifying files."),
            _cap("diff_review", T.CODING, "Review bounded diff metadata without copying full source."),
            _cap("test_planning", T.CODING, "Recommend focused and regression tests."),
            _cap("release_review", T.CODING, "Plan release verification without tagging or pushing."),
        ), ready=True, health="plan_only", reason="Coding planning and read-only repository diagnostics are implemented; writes, commands, commits, and pushes remain disabled."),
        _entry("document_agent", "Explicit bounded local document planning and safe text extraction.", (
            _cap("documents", T.DOCUMENTS, "Document planning, metadata, bounded text extraction, summary, and Q&A foundation.", risk=R.MEDIUM, approval=True, permissions=("read_explicit_document",), limitations=("PDF/Office/OCR parsers remain unavailable.",)),
        ), ready=True, health="text_only_foundation", reason="Safe explicit text-file extraction works; PDF, Office, OCR, bulk ingestion, and cloud parsing remain disabled."),
        _entry("browser_agent", "Read-only browser/source planning without interactive side effects.", (
            _cap("browser_read", T.WEB, "Read-only webpage/source planning and bounded summary foundation.", permissions=("browser_read",), limitations=("Login, forms, purchases, downloads, cookies, and sessions are disabled.",)),
        ), ready=True, health="read_only_foundation", reason="Read-only planning is ready; interactive browser execution is disabled."),
        _entry("scheduler_agent", "Schedule and recurrence planning without an active runner.", (
            _cap("scheduler_planning", T.SCHEDULER, "One-time, recurring, and condition-watch schedule validation and planning.", limitations=("No background runner, OS cron, Task Scheduler, or notifications.",)),
        ), ready=True, health="plan_only", reason="Schedule planning and validation are ready; no task is installed or executed."),
        _entry("communication_agent", "Communication planning with optional governed Telegram, Discord, email, and Slack text connectors.", (
            _cap("communication_drafting", T.COMMUNICATION, "Draft messages, email, and notification plans without sending."),
            _cap("telegram_text", T.COMMUNICATION, "Validate authorized Telegram text and plan exact approved delivery.", risk=R.HIGH, approval=True, side_effects=("external_text_send",), permissions=("send_message","network_access"), limitations=("Available only when Telegram is explicitly configured, paired, and Broker-approved.",)),
            _cap("external_text_send",T.COMMUNICATION,"Validate and send Discord, email, or Slack text after exact approval.",risk=R.HIGH,approval=True,side_effects=("external_text_send",),permissions=("provider_specific_send","network_access"),limitations=("Available only when the selected provider is explicitly configured and Broker-approved.",)),
        ), ready=True, health="connectors_optional", reason="Four text connectors are implemented; all external runtimes are disabled and unconfigured by default."),
        _entry("adapter_agent", "Manifest-only MCP and external plugin planning.", (
            _cap("adapter_planning", T.ADAPTER, "Adapter manifests, permission review, and MCP/plugin integration planning.", risk=R.MEDIUM, approval=True, permissions=("manifest_read",), limitations=("MCP runtime, plugin installation/execution, credentials, and network are disabled.",)),
        ), ready=True, health="manifest_only", reason="Manifest and permission planning are ready; no adapter executes."),
        _entry("evaluation_agent", "Local-only routing, safety, truthfulness, and observability checks.", (
            _cap("evaluation", T.EVALUATION, "Run bounded deterministic local evaluation and metadata-only observability checks."),
        ), ready=True, health="local_only", reason="Local evaluation and observability foundations are available; telemetry and remote logging are disabled."),
        _entry("model_agent", "Provider-neutral model route diagnostics.", (_cap("model_routing", T.SYSTEM, "Model status, provider metadata, and route planning."),), ready=True, health="foundation", reason="The Phase 3 model router foundation is available."),
        _entry("system_agent", "Non-invasive local system diagnostics.", (_cap("system_diagnostics", T.SYSTEM, "Safe hardware and runtime metadata only."),), ready=True, health="partial_diagnostics", reason="Only bounded diagnostics are enabled; system modification is not."),
        _entry("execution_agent", "Controlled local execution policy and dedicated executor routing.", (_cap("controlled_execution", T.EXECUTION, "Policy, risk, permission, approval, broker, and dedicated local executor routing.", risk=R.HIGH, approval=True, side_effects=("approved_local_action",), permissions=("action_specific",)),), ready=True, health="approved_scoped", reason="Scoped file, command, Git, browser-read, notification, and manual scheduler executors are approval-gated."),
        _entry("approval_agent", "Explicit, expiring, scope-bound approval management; never execution.", (_cap("approval_management", T.APPROVAL, "Create, approve, deny, cancel, revoke, expire, and validate bounded approvals."),), ready=True, health="management_only", reason="Explicit approval management is implemented and cannot execute actions."),
        _entry("broker_agent", "Central policy, approval, permission, and capability validation.", (_cap("execution_broker", T.EXECUTION, "Plan, validate, dry-run, and dispatch to dedicated executors.", risk=R.MEDIUM),), ready=True, health="validation_and_dispatch", reason="The broker gates all Phase 4 executors."),
        _entry("notification_agent", "Local-only approved notification delivery.", (_cap("local_notification", T.NOTIFICATION, "Bounded local display with anti-spam controls.", risk=R.MEDIUM, approval=True, side_effects=("local_visible_notification",), permissions=("send_notification",)),), ready=True, health="console_local", reason="A truthful local console provider is available; external notification providers remain disabled."),
    )
    future = (
        _entry("mcp_gateway_agent", "Future executable MCP gateway coordinator.", (_cap("tools", T.TOOLS, "Future MCP runtime and connector execution.", risk=R.HIGH, approval=True, permissions=("network_access",), limitations=("future",)),), ready=False, health="future", reason="MCP runtime remains disabled; adapter_agent provides manifest-only planning."),
        _entry("workflow_agent", "Future scheduled workflow executor.", (_cap("workflow", T.WORKFLOW, "Future scheduler execution.", risk=R.HIGH, approval=True, side_effects=("scheduled_execution",), permissions=("execute_commands",), limitations=("future",)),), ready=False, health="future", reason="Scheduled execution remains disabled; scheduler_agent provides planning only."),
        _entry("robotics_agent", "Future robotics planning specialist.", (_cap("robotics", T.ROBOTICS, "Future robotics planning and embedded reasoning.", risk=R.HIGH, approval=True, side_effects=("hardware",), permissions=("hardware_write",), limitations=("future",)),), ready=False, health="future", reason="No approved hardware interface is configured."),
        _entry("drone_agent", "Future drone project planning specialist.", (_cap("drone", T.DRONE, "Future drone planning; physical control is blocked.", risk=R.CRITICAL, approval=True, side_effects=("physical_control",), permissions=("hardware_write",), limitations=("future",)),), ready=False, health="future", reason="Drone control is critical-risk and blocked without a future approved hardware interface."),
        _entry("social_media_agent", "Future social content workflow specialist.", (_cap("social_post", T.COMMUNICATION, "Future social posting workflow.", risk=R.HIGH, approval=True, side_effects=("external_post",), permissions=("social_post",), limitations=("future",)),), ready=False, health="future", reason="No account connector exists and posting is disabled."),
    )
    return current + future


def register_specialist_agents(registry: AgentRegistry, *, vision_ready: bool = False) -> AgentRegistry:
    for entry in specialist_entries(vision_ready=vision_ready):
        if registry.get_agent(entry.name) is None:
            registry.register_agent(entry)
    return registry
