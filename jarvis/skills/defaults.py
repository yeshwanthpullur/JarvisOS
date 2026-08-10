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
        _ready("image_workflow_skill", "image", "image_workflow", "Validate and plan image workflows only."),
        _ready("video_workflow_skill", "video", "video_workflow", "Validate and plan video workflows only."),
        _ready("web_read_only_skill", "web", "web_read", "Read public web metadata under policy.", permissions=(P.BROWSER_READ,)),
        _ready("sync_status_skill", "sync", "sync_status", "Read local sync queue status."),
        _ready("voice_status_skill", "conversation", "voice_status", "Read voice subsystem status."),
    )
    future = (
        _future("academic_search_skill", "research", P.NETWORK_ACCESS), _future("citation_manager_skill", "research", P.READ_CONTEXT), _future("external_search_api_skill", "research", P.NETWORK_ACCESS),
        _future("mcp_gateway_skill", "developer", P.NETWORK_ACCESS), _future("telegram_skill", "communication", P.SEND_MESSAGE), _future("discord_skill", "communication", P.SEND_MESSAGE),
        _future("email_skill", "email", P.SEND_EMAIL), _future("calendar_skill", "calendar", P.CALENDAR_WRITE),
        _future("browser_write_skill", "browser", P.BROWSER_WRITE), _future("coding_agent_skill", "coding", P.WRITE_FILES),
        _future("research_agent_skill", "research", P.NETWORK_ACCESS), _future("document_intelligence_skill", "documents", P.READ_FILES),
        _future("robotics_skill", "robotics", P.HARDWARE_WRITE), _future("drone_skill", "drone", P.HARDWARE_WRITE),
        _future("social_media_skill", "social", P.SOCIAL_POST),
        _future("scheduler_skill", "workflow", P.EXECUTE_COMMANDS),
    )
    return SkillRegistry(builtins + future)
