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
        _entry("model_agent", "Provider-neutral model route diagnostics.", (_cap("model_routing", T.SYSTEM, "Model status, provider metadata, and route planning."),), ready=True, health="foundation", reason="The Phase 3 model router foundation is available."),
        _entry("system_agent", "Non-invasive local system diagnostics.", (_cap("system_diagnostics", T.SYSTEM, "Safe hardware and runtime metadata only."),), ready=True, health="partial_diagnostics", reason="Only bounded diagnostics are enabled; system modification is not."),
    )
    future = (
        _entry("mcp_gateway_agent", "Future MCP gateway coordinator.", (_cap("tools", T.TOOLS, "Future MCP gateway planning and connector diagnostics.", risk=R.MEDIUM, approval=True, permissions=("network_access",), limitations=("future",)),), ready=False, health="future", reason="MCP gateway integration is planned for a later milestone."),
        _entry("document_agent", "Future document understanding specialist.", (_cap("documents", T.DOCUMENTS, "Future document parsing and Q&A.", risk=R.MEDIUM, approval=True, permissions=("read_files",), limitations=("future",)),), ready=False, health="future", reason="Document workflow integration is not configured."),
        _entry("browser_agent", "Future approval-gated interactive browser specialist.", (_cap("browser_write", T.WEB, "Future browser interaction.", risk=R.HIGH, approval=True, side_effects=("browser",), permissions=("browser_write",), limitations=("future",)),), ready=False, health="future", reason="Interactive browser actions remain disabled; use web_agent for read-only inspection."),
        _entry("communication_agent", "Future communication connector coordinator.", (_cap("communication", T.COMMUNICATION, "Future message, email, and connector planning.", risk=R.HIGH, approval=True, side_effects=("communication",), permissions=("send_message",), limitations=("future",)),), ready=False, health="future", reason="No Telegram, Discord, email, or social connector is configured."),
        _entry("workflow_agent", "Future scheduled workflow coordinator.", (_cap("workflow", T.WORKFLOW, "Future scheduler and workflow execution.", risk=R.HIGH, approval=True, side_effects=("scheduled_execution",), permissions=("execute_commands",), limitations=("future",)),), ready=False, health="future", reason="Scheduled execution is not enabled in Phase 3."),
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
