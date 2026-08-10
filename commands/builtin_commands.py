"""Built-in command registration for JARVIS OS."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from commands.command_context import CommandContext
from commands.command_permissions import CommandPermission
from commands.command_registry import CommandRecord, CommandRegistry
from conversation.conversation_response import ConversationResponse
from providers import ProviderRequest
from jarvis.project_limitations import LimitationsRegister, LimitationsRegisterError
from jarvis.agents import AgentRegistry, PrimeAgent, register_specialist_agents, render_agent_command, render_prime_command, ResearchAgent, render_research_command
from jarvis.models import AdvancedModelPlanner, ModelProviderRegistry, ModelRouter, build_default_model_registry, render_advanced_model_command, render_model_command
from jarvis.skills import SkillRegistry, build_default_skill_registry, render_skill_command
from jarvis.coding import CodingAgent, CodingHistoryStore, CodingPlanner, DiffReviewer, RepoInspector, render_coding_command
from jarvis.documents import DocumentAgent, render_document_command
from jarvis.browser import BrowserAgent, render_browser_command
from jarvis.scheduler import SchedulerAgent, render_scheduler_command
from jarvis.communication import CommunicationAgent, render_communication_command
from jarvis.adapters import AdapterAgent, render_adapter_command
from jarvis.evaluation import EvaluationRunner, render_evaluation_command
from jarvis.execution.cli import get_phase4_runtime, render_phase4_command
from jarvis.release_readiness import ReleaseReadinessEvaluator, render_release_command
from jarvis.integrations import ExternalIntegrationControlPlane, render_external_command


def _manager(context: CommandContext):
    if hasattr(context.conversation_context, "registry"):
        return context.conversation_context
    return getattr(context.conversation_context, "command_manager", None)


def _text_response(text: str, **metadata: object) -> ConversationResponse:
    return ConversationResponse(response=text, metadata=metadata)


def _personal_manager(context: CommandContext):
    conversation = context.conversation_context
    if conversation is None:
        return None
    metadata = getattr(conversation, "metadata", {}) or {}
    return metadata.get("personal_intelligence_manager")


def _context_manager(context: CommandContext):
    conversation = context.conversation_context
    if conversation is None:
        return None
    metadata = getattr(conversation, "metadata", {}) or {}
    return metadata.get("context_intelligence_manager")


def _goal_manager(context: CommandContext):
    conversation = context.conversation_context
    if conversation is None:
        return None
    metadata = getattr(conversation, "metadata", {}) or {}
    return metadata.get("goal_intelligence_manager")


def _memory_intelligence(context: CommandContext):
    conversation = context.conversation_context
    if conversation is None:
        return None
    direct = getattr(conversation, "memory_intelligence_manager", None)
    if direct is not None:
        return direct
    metadata = getattr(conversation, "metadata", {}) or {}
    return metadata.get("memory_intelligence_manager")


def _provider_manager(context: CommandContext):
    conversation = context.conversation_context
    if conversation is None:
        return None
    direct = getattr(conversation, "provider_manager", None)
    if direct is not None:
        return direct
    metadata = getattr(conversation, "metadata", {}) or {}
    return metadata.get("provider_manager")


def _agent_manager(context: CommandContext):
    conversation = context.conversation_context
    if conversation is None:
        return None
    direct = getattr(conversation, "agent_manager", None)
    if direct is not None:
        return direct
    metadata = getattr(conversation, "metadata", {}) or {}
    return metadata.get("agent_manager")


def _existing_ollama_state(context: CommandContext) -> tuple[bool, tuple[str, ...], bool]:
    """Read already-discovered Ollama metadata without probing a provider."""
    manager = _provider_manager(context)
    records = getattr(getattr(manager, "registry", None), "all", lambda: ())()
    for record in records:
        config = getattr(record, "config", None)
        kind = getattr(getattr(config, "kind", None), "value", getattr(config, "kind", ""))
        if str(getattr(config, "provider_id", "")).lower() != "ollama" and str(kind).lower() != "ollama":
            continue
        provider = getattr(record, "provider", None)
        models = tuple(
            str(getattr(item, "model_id", ""))
            for item in getattr(provider, "_models", ())
            if getattr(item, "model_id", "")
        )
        ready = bool(provider and getattr(getattr(provider, "health", None), "available", False) and models)
        vision_ready = any(
            "llava" in model.lower()
            or any(getattr(capability, "value", str(capability)).lower() == "vision" for capability in getattr(item, "capabilities", ()))
            for item, model in zip(getattr(provider, "_models", ()), models)
        )
        return ready, models, vision_ready
    return False, (), False


def _phase3_agent_registry(context: CommandContext) -> AgentRegistry:
    conversation = context.conversation_context
    direct = getattr(conversation, "agent_registry", None) if conversation is not None else None
    if isinstance(direct, AgentRegistry):
        return direct
    metadata = getattr(conversation, "metadata", {}) or {} if conversation is not None else {}
    registry = metadata.get("agent_registry")
    if isinstance(registry, AgentRegistry):
        return registry
    _, _, vision_ready = _existing_ollama_state(context)
    return register_specialist_agents(AgentRegistry(), vision_ready=vision_ready)


def _prime_agent(context: CommandContext) -> PrimeAgent:
    conversation = context.conversation_context
    direct = getattr(conversation, "prime_agent", None) if conversation is not None else None
    if isinstance(direct, PrimeAgent):
        return direct
    metadata = getattr(conversation, "metadata", {}) or {} if conversation is not None else {}
    prime = metadata.get("prime_agent")
    if isinstance(prime, PrimeAgent):
        return prime
    _, router = _model_foundation(context)
    return PrimeAgent(_phase3_agent_registry(context), model_router=router, skill_registry=_skill_registry(context))


def _model_foundation(context: CommandContext) -> tuple[ModelProviderRegistry, ModelRouter]:
    conversation = context.conversation_context
    metadata = getattr(conversation, "metadata", {}) or {} if conversation is not None else {}
    registry = getattr(conversation, "model_registry", None) if conversation is not None else None
    router = getattr(conversation, "model_router", None) if conversation is not None else None
    registry = registry if isinstance(registry, ModelProviderRegistry) else metadata.get("model_registry")
    router = router if isinstance(router, ModelRouter) else metadata.get("model_router")
    if not isinstance(registry, ModelProviderRegistry):
        ollama_ready, models, vision_ready = _existing_ollama_state(context)
        registry = build_default_model_registry(
            ollama_ready=ollama_ready,
            ollama_models=models,
            vision_ready=vision_ready,
        )
    if not isinstance(router, ModelRouter):
        router = ModelRouter(registry)
    return registry, router


def _skill_registry(context: CommandContext) -> SkillRegistry:
    conversation = context.conversation_context
    direct = getattr(conversation, "skill_registry", None) if conversation is not None else None
    metadata = getattr(conversation, "metadata", {}) or {} if conversation is not None else {}
    registry = direct if isinstance(direct, SkillRegistry) else metadata.get("skill_registry")
    return registry if isinstance(registry, SkillRegistry) else build_default_skill_registry()

def _external_integrations(context: CommandContext) -> ExternalIntegrationControlPlane:
    conversation = context.conversation_context
    direct = getattr(conversation, "external_integrations", None) if conversation is not None else None
    metadata = getattr(conversation, "metadata", {}) or {} if conversation is not None else {}
    plane = direct if isinstance(direct, ExternalIntegrationControlPlane) else metadata.get("external_integrations")
    return plane if isinstance(plane, ExternalIntegrationControlPlane) else ExternalIntegrationControlPlane()


def _tool_manager(context: CommandContext):
    conversation = context.conversation_context
    if conversation is None:
        return None
    direct = getattr(conversation, "tool_manager", None)
    if direct is not None:
        return direct
    metadata = getattr(conversation, "metadata", {}) or {}
    return metadata.get("tool_manager")

def _planning_manager(context: CommandContext):
    conversation=context.conversation_context
    if conversation is None:return None
    return getattr(conversation,"autonomous_planning",None) or (getattr(conversation,"metadata",{}) or {}).get("autonomous_planning")
def _voice_manager(context:CommandContext):
    conversation=context.conversation_context
    return None if conversation is None else getattr(conversation,"voice_intelligence",None) or (getattr(conversation,"metadata",{}) or {}).get("voice_intelligence")
def _vision_manager(context:CommandContext):
    conversation=context.conversation_context
    return None if conversation is None else getattr(conversation,"vision_intelligence",None) or (getattr(conversation,"metadata",{}) or {}).get("vision_intelligence")
def _image_generation_manager(context:CommandContext):
    conversation=context.conversation_context
    return None if conversation is None else getattr(conversation,"image_generation",None) or (getattr(conversation,"metadata",{}) or {}).get("image_generation")
def _video_editing_manager(context:CommandContext):
    conversation=context.conversation_context
    return None if conversation is None else getattr(conversation,"video_editing",None) or (getattr(conversation,"metadata",{}) or {}).get("video_editing")
def _sync_manager(context:CommandContext):
    conversation=context.conversation_context
    return None if conversation is None else getattr(conversation,"sync_intelligence",None) or (getattr(conversation,"metadata",{}) or {}).get("sync_intelligence")
def _web_manager(context:CommandContext):
    conversation=context.conversation_context
    return None if conversation is None else getattr(conversation,"web_automation",None) or (getattr(conversation,"metadata",{}) or {}).get("web_automation")
def _mobile_manager(context:CommandContext):
    conversation=context.conversation_context
    return None if conversation is None else getattr(conversation,"mobile_automation",None) or (getattr(conversation,"metadata",{}) or {}).get("mobile_automation")
def _conversation_intelligence(context:CommandContext):
    conversation=context.conversation_context
    return None if conversation is None else (getattr(conversation,"metadata",{}) or {}).get("conversation_intelligence_manager")
def _research_agent(context: CommandContext) -> ResearchAgent:
    conversation = context.conversation_context
    direct = getattr(conversation, "research_agent", None) if conversation is not None else None
    if isinstance(direct, ResearchAgent):
        return direct
    metadata = getattr(conversation, "metadata", {}) or {} if conversation is not None else {}
    research = metadata.get("research_agent")
    if isinstance(research, ResearchAgent):
        return research
    _, _, vision_ready = _existing_ollama_state(context)
    return ResearchAgent(enabled=True, web_available=True, documents_available=True)


def _coding_agent(context: CommandContext) -> CodingAgent:
    conversation = context.conversation_context
    direct = getattr(conversation, "coding_agent", None) if conversation is not None else None
    if isinstance(direct, CodingAgent):
        return direct
    metadata = getattr(conversation, "metadata", {}) or {} if conversation is not None else {}
    coding = metadata.get("coding_agent")
    if isinstance(coding, CodingAgent):
        return coding
    root = Path(__file__).resolve().parents[1]
    return CodingAgent(RepoInspector(root), DiffReviewer(root), CodingPlanner(), CodingHistoryStore(root / "data" / "coding"))


def _foundation_instance(context: CommandContext, name: str, factory):
    conversation = context.conversation_context
    direct = getattr(conversation, name, None) if conversation is not None else None
    metadata = getattr(conversation, "metadata", {}) or {} if conversation is not None else {}
    return direct or metadata.get(name) or factory()


def _document_agent(context: CommandContext) -> DocumentAgent:
    root = Path(__file__).resolve().parents[1]
    return _foundation_instance(context, "document_agent", lambda: DocumentAgent(root))


def _browser_agent(context: CommandContext) -> BrowserAgent:
    return _foundation_instance(context, "browser_agent", BrowserAgent)


def _scheduler_agent(context: CommandContext) -> SchedulerAgent:
    return _foundation_instance(context, "scheduler_agent", SchedulerAgent)


def _communication_agent(context: CommandContext) -> CommunicationAgent:
    return _foundation_instance(context, "communication_agent", CommunicationAgent)


def _adapter_agent(context: CommandContext) -> AdapterAgent:
    return _foundation_instance(context, "adapter_agent", AdapterAgent)


def _advanced_model_planner(context: CommandContext) -> AdvancedModelPlanner:
    return _foundation_instance(context, "advanced_model_planner", AdvancedModelPlanner)


def _evaluation_runner(context: CommandContext) -> EvaluationRunner:
    return _foundation_instance(context, "evaluation_runner", lambda: EvaluationRunner(_prime_agent(context), _adapter_agent(context), _advanced_model_planner(context)))


def _release_evaluator(context: CommandContext) -> ReleaseReadinessEvaluator:
    root = Path(__file__).resolve().parents[1]
    return _foundation_instance(context, "release_readiness_evaluator", lambda: ReleaseReadinessEvaluator(root))


def _cloud_policy(session: object | None, default: str = "automatic") -> str:
    if session is None:
        return default
    metadata = getattr(session, "metadata", {}) or {}
    return str(metadata.get("execution_policy") or metadata.get("provider_policy") or default)


def _project_health_summary(context: CommandContext | None = None) -> ConversationResponse:
    docs_path = Path(__file__).resolve().parents[1] / "docs"
    path = docs_path / "project_health.json"
    try:
        health = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return _text_response("Project status unavailable: docs/project_health.json could not be read.")
    categories = tuple(health.get("categories", ()))
    working = sum(1 for item in categories if item.get("status") == "Working")
    experimental = sum(1 for item in categories if item.get("status") == "Experimental")
    try:
        limitations = json.loads((docs_path / "limitations_register.json").read_text(encoding="utf-8"))
        limitation_counts = limitations.get("counts", {})
    except (OSError, ValueError, TypeError):
        limitations = {}
        limitation_counts = {}
    fixed_limitations = int(limitation_counts.get("fixed", 0))
    open_limitations = int(limitation_counts.get("still_open", 0))
    review_counts = limitations.get("review", {}).get("category_totals", {})
    restricted_limitations = int(review_counts.get("intentionally_restricted", 0))
    blocked_limitations = int(review_counts.get("blocked_hardware_environment", 0)) + int(review_counts.get("blocked_external_service_cost", 0))
    limitation_focus = str(limitations.get("next_major_limitation_id", "unknown"))
    phase3_text = ""
    phase3_metadata: dict[str, object] = {}
    if context is not None:
        agent_registry = _phase3_agent_registry(context)
        agent_summary = agent_registry.registry_summary()
        agent_entries = agent_registry.list_agents()
        foundation_agents = sum(item.health not in {"ready", "future"} for item in agent_entries)
        future_agents = sum(item.health == "future" for item in agent_entries)
        _, model_router = _model_foundation(context)
        skill_summary = _skill_registry(context).registry_summary()
        prime_status = _prime_agent(context).status()
        research_agent = _research_agent(context)
        research_status = research_agent.status()
        coding_agent = _coding_agent(context)
        coding_status = coding_agent.status()
        document_status = _document_agent(context).status()
        browser_status = _browser_agent(context).status()
        scheduler_status = _scheduler_agent(context).status()
        communication_status = _communication_agent(context).status()
        adapter_status = _adapter_agent(context).status()
        advanced_status = _advanced_model_planner(context).status()
        evaluation_status = _evaluation_runner(context).status()
        release_status = _release_evaluator(context).evaluate()
        external_summary = _external_integrations(context).registry.summary()
        phase4 = get_phase4_runtime(Path(__file__).resolve().parents[1])
        phase3_text = (
            "phase3="
            f"agents:{agent_summary['ready_agents']}/{agent_summary['total_agents']}"
            f"/foundation:{foundation_agents}/future:{future_agents} "
            f"prime:{prime_status['status']} model_router:{model_router.router_status()['status']} "
            f"research:{research_status['status']} coding:{coding_status['status']} document:{document_status['status']} "
            f"browser:{browser_status['status']} scheduler:{scheduler_status['status']} communication:{communication_status['status']} "
            f"adapter:{adapter_status['status']} advanced_models:{advanced_status['status']} evaluation:{evaluation_status['status']} "
            f"skills:{skill_summary['ready_skills']}/{skill_summary['total_skills']} "
            f"approvals:{agent_summary['approval_required_capabilities']} "
            f"high_risk:{agent_summary['high_risk_capabilities']} "
            f"phase4=local ext:{external_summary['enabled']}/{external_summary['total']}/off p85={release_status.status.value} "
        )
        phase3_metadata = {
            "agent_system_status": "ready",
            "total_agents": agent_summary["total_agents"],
            "ready_agents": agent_summary["ready_agents"],
            "foundation_agents": foundation_agents,
            "future_agents": future_agents,
            "prime_agent_status": prime_status["status"],
            "model_router_status": model_router.router_status()["status"],
            "research_agent_status": research_status["status"],
            "research_source_policy": research_status["source_policy"],
            "coding_agent_status": coding_status["status"],
            "coding_default_mode": coding_status["default_mode"],
            "coding_write_operations": coding_status["write_operations"],
            "coding_command_execution": coding_status["command_execution"],
            "document_agent_status": document_status["status"],
            "browser_agent_status": browser_status["status"],
            "scheduler_agent_status": scheduler_status["status"],
            "communication_agent_status": communication_status["status"],
            "adapter_agent_status": adapter_status["status"],
            "advanced_model_status": advanced_status["status"],
            "evaluation_status": evaluation_status["status"],
            "skill_registry_status": "ready" if skill_summary["valid"] else "error",
            "approval_required_capabilities": agent_summary["approval_required_capabilities"],
            "high_risk_capabilities": agent_summary["high_risk_capabilities"],
            "execution_policy_status": "ready",
            "approval_system_status": "ready_explicit_only",
            "execution_broker_status": "ready",
            "file_execution_status": "approved_scoped",
            "command_execution_status": "approved_sandbox",
            "git_execution_status": "approved_controlled",
            "browser_read_execution_status": "approved_public_read",
            "notification_status": "approved_local_only",
            "scheduler_runtime_status": "manual_only",
            "background_execution": False,
            "public_execution_api": False,
            "prompt85_validation_status": release_status.status.value,
            "phase5_missing_components": len(release_status.missing_components),
            "phase6_started": False,
            "external_provider_registry_status": "ready_metadata_only" if external_summary["valid"] else "error",
            "external_providers_total": external_summary["total"],
            "external_providers_enabled": external_summary["enabled"],
            "external_execution_enabled": bool(external_summary["execution_enabled"]),
        }
    return _text_response(
        "Project status: "
        f"release={health.get('release', 'unknown')} "
        f"primary={health.get('primary_mode', 'unknown')} "
        f"MVP={health.get('overall_mvp_readiness', 0)}% "
        f"working={working} experimental={experimental} "
        f"limitations=fixed:{fixed_limitations}/open:{open_limitations}/restricted:{restricted_limitations}/blocked:{blocked_limitations} "
        f"focus={limitation_focus} "
        f"{phase3_text}"
        f"next={health.get('next_milestone', 'unknown')}. "
        "Details: docs/PROJECT_HEALTH.md and docs/LIMITATIONS_REGISTER.md",
        release=health.get("release"),
        primary_mode=health.get("primary_mode"),
        overall_mvp_readiness=health.get("overall_mvp_readiness"),
        working_categories=working,
        experimental_categories=experimental,
        fixed_limitations=fixed_limitations,
        open_limitations=open_limitations,
        restricted_limitations=restricted_limitations,
        blocked_limitations=blocked_limitations,
        limitation_focus=limitation_focus,
        next_milestone=health.get("next_milestone"),
        **phase3_metadata,
    )


def _safe_project_snapshot() -> dict[str, object] | None:
    path = Path(__file__).resolve().parents[1] / "docs" / "project_health.json"
    try:
        health = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    categories = tuple(health.get("categories", ()))
    return {
        "release": health.get("release", "unknown"),
        "commit": health.get("commit", "unknown"),
        "primary_mode": health.get("primary_mode", "unknown"),
        "overall_mvp_readiness": int(health.get("overall_mvp_readiness", 0)),
        "working_categories": sum(item.get("status") == "Working" for item in categories),
        "partial_categories": sum(item.get("status") == "Partial" for item in categories),
        "experimental_categories": sum(item.get("status") == "Experimental" for item in categories),
        "next_milestone": health.get("next_milestone", "unknown"),
        "updated_at": health.get("updated_at", "unknown"),
    }


def _is_local_provider(record: object) -> bool:
    config = getattr(record, "config", None)
    return bool(getattr(config, "local_only", False)) or str(getattr(config, "kind", "")).lower() in {
        "local",
        "ollama",
        "lm_studio",
    }


def register_builtin_commands(registry: CommandRegistry) -> None:
    """Register built-in commands."""
    commands: tuple[tuple[str, str, str, tuple[str, ...], CommandPermission], ...] = (
        ("help", "Show available commands", "utility", ("?",), CommandPermission.UTILITY),
        ("about", "Show JARVIS OS information", "system", (), CommandPermission.SYSTEM),
        ("version", "Show application version", "system", (), CommandPermission.SYSTEM),
        ("status", "Show system status", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("project status", "Show project milestone health", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("limitations status", "Show limitation counts and priority", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("limitations list", "Show limitations command help", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("limitations open", "List bounded open limitations", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("limitations fixed", "List bounded fixed limitations", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("limitations show", "Show one limitation", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("limitations category", "List limitations by review category", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("limitations next", "Show the highest-priority limitation", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("limitations summary", "Show limitation counts and priority", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("conversation status", "Show conversation state", "conversation", (), CommandPermission.CONVERSATION),
        ("conversation reset", "Clear in-memory conversation context", "conversation", (), CommandPermission.CONVERSATION),
        ("conversation summary", "Show bounded conversation summary", "conversation", (), CommandPermission.CONVERSATION),
        ("conversation mode", "Show conversation mode", "conversation", (), CommandPermission.CONVERSATION),
        ("conversation confidence", "Show conversation confidence", "conversation", (), CommandPermission.CONVERSATION),
        ("conversation topic", "Show active conversation topic", "conversation", (), CommandPermission.CONVERSATION),
        ("research status", "Show research planning readiness", "research", (), CommandPermission.DIAGNOSTIC),
        ("research help", "Show research command help", "research", (), CommandPermission.DIAGNOSTIC),
        ("research plan", "Plan a bounded research request", "research", (), CommandPermission.DIAGNOSTIC),
        ("research safety", "Evaluate research safety", "research", (), CommandPermission.DIAGNOSTIC),
        ("research sources", "Show possible source policy", "research", (), CommandPermission.DIAGNOSTIC),
        ("research summarize", "Summarize bounded research evidence", "research", (), CommandPermission.DIAGNOSTIC),
        ("research evidence", "Show research evidence metadata", "research", (), CommandPermission.DIAGNOSTIC),
        ("research show", "Show one research result", "research", (), CommandPermission.DIAGNOSTIC),
        ("research history", "Show bounded research history", "research", (), CommandPermission.DIAGNOSTIC),
        ("coding status", "Show Coding Agent readiness", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding help", "Show Coding Agent command help", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding inspect", "Inspect bounded repository metadata", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding plan", "Create a plan-only coding plan", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding risk", "Evaluate coding request risk", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding diff", "Show bounded diff metadata", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding review", "Review bounded current diff metadata", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding tests", "Plan coding test coverage", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding show", "Show one coding job", "coding", (), CommandPermission.DIAGNOSTIC),
        ("coding history", "Show bounded coding history", "coding", (), CommandPermission.DIAGNOSTIC),
        ("document status", "Show Document Intelligence status", "document", (), CommandPermission.DIAGNOSTIC),
        ("document help", "Show document command help", "document", (), CommandPermission.DIAGNOSTIC),
        ("document plan", "Plan bounded document work", "document", (), CommandPermission.DIAGNOSTIC),
        ("document safety", "Evaluate document safety", "document", (), CommandPermission.DIAGNOSTIC),
        ("document types", "Show safe document type policy", "document", (), CommandPermission.DIAGNOSTIC),
        ("document inspect", "Inspect explicit document metadata", "document", (), CommandPermission.DIAGNOSTIC),
        ("document extract", "Extract bounded safe text", "document", (), CommandPermission.DIAGNOSTIC),
        ("document summarize", "Summarize bounded safe text", "document", (), CommandPermission.DIAGNOSTIC),
        ("document ask", "Plan bounded document Q&A", "document", (), CommandPermission.DIAGNOSTIC),
        ("document show", "Show one document job", "document", (), CommandPermission.DIAGNOSTIC),
        ("document history", "Show bounded document history", "document", (), CommandPermission.DIAGNOSTIC),
        ("browser status", "Show Browser Agent status", "browser", (), CommandPermission.DIAGNOSTIC),
        ("browser help", "Show browser command help", "browser", (), CommandPermission.DIAGNOSTIC),
        ("browser plan", "Plan read-only browser work", "browser", (), CommandPermission.DIAGNOSTIC),
        ("browser safety", "Evaluate browser safety", "browser", (), CommandPermission.DIAGNOSTIC),
        ("browser capabilities", "Show browser capability policy", "browser", (), CommandPermission.DIAGNOSTIC),
        ("browser sources", "Show read-only source plan", "browser", (), CommandPermission.DIAGNOSTIC),
        ("browser summarize", "Plan bounded webpage summary", "browser", (), CommandPermission.DIAGNOSTIC),
        ("browser show", "Show one browser job", "browser", (), CommandPermission.DIAGNOSTIC),
        ("browser history", "Show bounded browser history", "browser", (), CommandPermission.DIAGNOSTIC),
        ("scheduler status", "Show Scheduler Agent status", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("scheduler help", "Show scheduler command help", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("scheduler plan", "Plan a schedule without creating it", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("scheduler safety", "Evaluate schedule safety", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("scheduler validate", "Validate bounded schedule text", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("scheduler preview", "Preview schedule metadata", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("scheduler capabilities", "Show scheduler capability policy", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("scheduler show", "Show one schedule job", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("scheduler history", "Show bounded scheduler history", "scheduler", (), CommandPermission.DIAGNOSTIC),
        ("communication status", "Show Communication Gateway status", "communication", (), CommandPermission.DIAGNOSTIC),
        ("communication help", "Show communication command help", "communication", (), CommandPermission.DIAGNOSTIC),
        ("communication providers", "List disabled communication providers", "communication", (), CommandPermission.DIAGNOSTIC),
        ("communication plan", "Plan draft-only communication", "communication", (), CommandPermission.DIAGNOSTIC),
        ("communication safety", "Evaluate communication safety", "communication", (), CommandPermission.DIAGNOSTIC),
        ("communication draft", "Create an unsent draft", "communication", (), CommandPermission.DIAGNOSTIC),
        ("communication notify-plan", "Plan an unsent notification", "communication", (), CommandPermission.DIAGNOSTIC),
        ("communication show", "Show one communication job", "communication", (), CommandPermission.DIAGNOSTIC),
        ("communication history", "Show bounded communication history", "communication", (), CommandPermission.DIAGNOSTIC),
        ("adapter status", "Show Adapter foundation status", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter help", "Show adapter command help", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter list", "List adapter manifests", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter show", "Show one adapter manifest", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter plan", "Plan an adapter without execution", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter safety", "Evaluate adapter safety", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter permissions", "Show ungranted adapter permissions", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter capabilities", "Show adapter capability policy", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter show-job", "Show one adapter job", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("adapter history", "Show bounded adapter history", "adapter", (), CommandPermission.DIAGNOSTIC),
        ("model advanced status", "Show advanced provider planning status", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced providers", "List planned advanced providers", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced show", "Show one advanced provider", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced plan", "Plan an advanced provider", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced compare", "Compare advanced provider metadata", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced hardware", "Show broad hardware categories", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced route", "Plan an advanced model route", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced safety", "Evaluate advanced model safety", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced checklist", "Show non-executing provider checklist", "provider", (), CommandPermission.DIAGNOSTIC),
        ("model advanced history", "Show bounded provider planning history", "provider", (), CommandPermission.DIAGNOSTIC),
        ("evaluation status", "Show local evaluation status", "evaluation", (), CommandPermission.DIAGNOSTIC),
        ("evaluation help", "Show evaluation command help", "evaluation", (), CommandPermission.DIAGNOSTIC),
        ("evaluation run", "Run bounded local evaluation", "evaluation", (), CommandPermission.DIAGNOSTIC),
        ("evaluation routing", "Run deterministic routing fixtures", "evaluation", (), CommandPermission.DIAGNOSTIC),
        ("evaluation safety", "Run safety fixtures", "evaluation", (), CommandPermission.DIAGNOSTIC),
        ("evaluation truthfulness", "Check capability truthfulness", "evaluation", (), CommandPermission.DIAGNOSTIC),
        ("evaluation observability", "Show local metadata snapshot", "evaluation", (), CommandPermission.DIAGNOSTIC),
        ("evaluation show", "Show one evaluation result", "evaluation", (), CommandPermission.DIAGNOSTIC),
        ("evaluation history", "Show bounded evaluation history", "evaluation", (), CommandPermission.DIAGNOSTIC),
        *((f"release-readiness {op}", f"Prompt 85 release readiness {op}", "evaluation", (), CommandPermission.DIAGNOSTIC) for op in ("status", "help", "gates", "contracts", "missing", "candidate")),
        *((f"execution {op}", f"Phase 4 execution {op}", "execution", (), CommandPermission.DIAGNOSTIC) for op in ("status","help","policy","permissions","readiness","risk","plan","capabilities","show","history")),
        *((f"approval {op}", f"Explicit approval {op}", "execution", (), CommandPermission.DIAGNOSTIC) for op in ("status","help","request","pending","list","show","approve","deny","cancel","revoke","expire","validate")),
        *((f"broker {op}", f"Execution broker {op}", "execution", (), CommandPermission.DIAGNOSTIC) for op in ("status","help","capabilities","plan","validate","dry-run","execute","show","history")),
        *((f"file-exec {op}", f"Approved file execution {op}", "execution", (), CommandPermission.DIAGNOSTIC) for op in ("status","help","policy","validate","plan","dry-run","create","write","append","mkdir","rename","move","delete","rollback","show","history")),
        *((f"command {op}", f"Approved command sandbox {op}", "execution", (), CommandPermission.DIAGNOSTIC) for op in ("status","help","policy","allowlist","validate","plan","dry-run","execute","show","history")),
        *((f"git-exec {op}", f"Approved Git execution {op}", "execution", (), CommandPermission.DIAGNOSTIC) for op in ("status","help","policy","inspect","files","validate","plan","dry-run","stage","unstage","commit","push","show","history")),
        *((f"notification {op}", f"Local notification {op}", "execution", (), CommandPermission.DIAGNOSTIC) for op in ("status","help","providers","policy","plan","validate","dry-run","send","test","show","history")),
        *((f"scheduler {op}", f"Manual scheduler runtime {op}", "scheduler", (), CommandPermission.DIAGNOSTIC) for op in ("runtime-status","jobs","due","create","run","run-due","pause","resume","cancel","runs","runtime-policy")),
        *((f"browser {op}", f"Controlled browser read {op}", "browser", (), CommandPermission.DIAGNOSTIC) for op in ("policy","validate","dry-run","read","read-show","read-history")),
        ("health", "Show health status", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("clear", "Clear the console", "utility", (), CommandPermission.UTILITY),
        ("exit", "Exit the command loop", "utility", ("quit",), CommandPermission.UTILITY),
        ("restart", "Future restart hook", "system", (), CommandPermission.SYSTEM),
        ("reload", "Future reload hook", "system", (), CommandPermission.SYSTEM),
        ("history", "Show command history", "conversation", (), CommandPermission.CONVERSATION),
        ("metrics", "Show metrics", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("diagnostics", "Show diagnostics", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("providers", "Show provider summary", "provider", (), CommandPermission.PROVIDER),
        ("provider list", "List providers", "provider", (), CommandPermission.PROVIDER),
        ("provider status", "Show provider status", "provider", (), CommandPermission.PROVIDER),
        ("provider health", "Show provider health", "provider", (), CommandPermission.PROVIDER),
        ("provider enable", "Enable a provider", "provider", (), CommandPermission.PROVIDER),
        ("provider disable", "Disable a provider", "provider", (), CommandPermission.PROVIDER),
        ("provider test", "Test a provider", "provider", (), CommandPermission.PROVIDER),
        *((name, "Show bounded external integration metadata", "provider", (), CommandPermission.DIAGNOSTIC) for name in ("provider show","provider capabilities","provider policy","provider validate","provider history","integration status","integration policy","credential status","credential required")),
        ("local", "Show local AI summary", "provider", (), CommandPermission.PROVIDER),
        ("local status", "Show local AI status", "provider", (), CommandPermission.PROVIDER),
        ("local providers", "List local providers", "provider", (), CommandPermission.PROVIDER),
        ("local models", "List local models", "provider", (), CommandPermission.PROVIDER),
        ("local refresh", "Refresh local model inventory", "provider", (), CommandPermission.PROVIDER),
        ("local use", "Select a local model", "provider", (), CommandPermission.PROVIDER),
        ("local test", "Test the selected local model", "provider", (), CommandPermission.PROVIDER),
        ("local explain-selection", "Explain local model selection", "provider", (), CommandPermission.PROVIDER),
        ("local only on", "Enable local-only mode", "provider", (), CommandPermission.PROVIDER),
        ("local only off", "Disable local-only mode", "provider", (), CommandPermission.PROVIDER),
        ("cloud", "Show cloud AI summary", "provider", (), CommandPermission.PROVIDER),
        ("cloud status", "Show cloud AI status", "provider", (), CommandPermission.PROVIDER),
        ("cloud providers", "List cloud providers", "provider", (), CommandPermission.PROVIDER),
        ("cloud models", "List cloud models", "provider", (), CommandPermission.PROVIDER),
        ("cloud refresh", "Refresh cloud model inventory", "provider", (), CommandPermission.PROVIDER),
        ("cloud use", "Select a cloud provider or model", "provider", (), CommandPermission.PROVIDER),
        ("cloud test", "Test the selected cloud provider", "provider", (), CommandPermission.PROVIDER),
        ("cloud explain-selection", "Explain cloud selection", "provider", (), CommandPermission.PROVIDER),
        ("cloud only on", "Enable cloud-only mode", "provider", (), CommandPermission.PROVIDER),
        ("cloud only off", "Disable cloud-only mode", "provider", (), CommandPermission.PROVIDER),
        ("plugins", "Show plugin summary", "plugin", (), CommandPermission.PLUGIN),
        ("plugin list", "List plugins", "plugin", (), CommandPermission.PLUGIN),
        ("plugin status", "Show plugin status", "plugin", (), CommandPermission.PLUGIN),
        ("agents", "Show agent summary", "agent", (), CommandPermission.AGENT),
        ("agent list", "List agents", "agent", (), CommandPermission.AGENT),
        ("agent status", "Show agent status", "agent", (), CommandPermission.AGENT),
        ("agent capabilities", "List governed agent capabilities", "agent", (), CommandPermission.AGENT),
        ("agent show", "Show one governed agent", "agent", (), CommandPermission.AGENT),
        ("agent find", "Find agents by capability", "agent", (), CommandPermission.AGENT),
        ("agent diagnostics", "Validate the governed agent registry", "agent", (), CommandPermission.DIAGNOSTIC),
        ("agent ready", "List ready specialist agents", "agent", (), CommandPermission.AGENT),
        ("agent unavailable", "List unavailable specialist agents", "agent", (), CommandPermission.AGENT),
        ("agent future", "List future specialist placeholders", "agent", (), CommandPermission.AGENT),
        ("agent risks", "List high-risk specialist capabilities", "agent", (), CommandPermission.DIAGNOSTIC),
        ("agent approvals", "List approval-required capabilities", "agent", (), CommandPermission.DIAGNOSTIC),
        ("prime status", "Show Prime Agent routing status", "agent", (), CommandPermission.AGENT),
        ("prime route", "Route a request without execution", "agent", (), CommandPermission.AGENT),
        ("prime plan", "Create a side-effect-free delegation plan", "agent", (), CommandPermission.AGENT),
        ("prime risk", "Classify request risk and approval needs", "agent", (), CommandPermission.AGENT),
        ("prime explain", "Explain a delegation decision", "agent", (), CommandPermission.AGENT),
        ("model status", "Show model router status", "provider", (), CommandPermission.PROVIDER),
        ("model providers", "List provider-neutral model routes", "provider", (), CommandPermission.PROVIDER),
        ("model capabilities", "List model capabilities", "provider", (), CommandPermission.PROVIDER),
        ("model route", "Plan a model route without execution", "provider", (), CommandPermission.PROVIDER),
        ("model explain", "Explain a model route", "provider", (), CommandPermission.PROVIDER),
        ("model hardware", "Show bounded local hardware hints", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("model policy", "Show model routing privacy policy", "provider", (), CommandPermission.PROVIDER),
        ("skill status", "Show controlled skill registry status", "tool", (), CommandPermission.DIAGNOSTIC),
        ("skill list", "List declarative skills", "tool", (), CommandPermission.UTILITY),
        ("skill capabilities", "List declared skill capabilities", "tool", (), CommandPermission.UTILITY),
        ("skill show", "Show one skill manifest", "tool", (), CommandPermission.UTILITY),
        ("skill find", "Find skills by capability or category", "tool", (), CommandPermission.UTILITY),
        ("skill permissions", "Show declared skill permissions", "tool", (), CommandPermission.DIAGNOSTIC),
        ("skill diagnostics", "Validate skill metadata", "tool", (), CommandPermission.DIAGNOSTIC),
        ("multiagent status", "Show multi-agent status", "agent", (), CommandPermission.AGENT),
        ("multiagent list", "List recent coordinations", "agent", (), CommandPermission.AGENT),
        ("multiagent show", "Show a coordination", "agent", (), CommandPermission.AGENT),
        ("multiagent cancel", "Cancel a coordination", "agent", (), CommandPermission.AGENT),
        ("multiagent limits", "Show coordination limits", "agent", (), CommandPermission.AGENT),
        ("multiagent mode", "Set multi-agent mode", "agent", (), CommandPermission.AGENT),
        ("tool list", "List registered tools", "tool", (), CommandPermission.UTILITY),
        ("tool show", "Show a tool definition", "tool", (), CommandPermission.UTILITY),
        ("tool health", "Show tool health", "tool", (), CommandPermission.DIAGNOSTIC),
        ("tool match", "Match a capability to a tool", "tool", (), CommandPermission.UTILITY),
        ("tool permissions", "Show tool permissions", "tool", (), CommandPermission.UTILITY),
        ("tool dry-run", "Validate without side effects", "tool", (), CommandPermission.UTILITY),
        ("tool history", "Show tool invocation history", "tool", (), CommandPermission.DIAGNOSTIC),
        ("tool invocation", "Show a tool invocation", "tool", (), CommandPermission.DIAGNOSTIC),
        ("tool cancel", "Cancel a tool invocation", "tool", (), CommandPermission.UTILITY),
        ("tool mode", "Set tool execution mode", "tool", (), CommandPermission.UTILITY),
        ("tool limits", "Show tool limits", "tool", (), CommandPermission.DIAGNOSTIC),
        ("tools status", "Show tool readiness", "tool", (), CommandPermission.DIAGNOSTIC),
        ("plan status", "Show planning status", "planning", (), CommandPermission.UTILITY),
        ("plan list", "List plans", "planning", (), CommandPermission.UTILITY),
        ("plan show", "Show a plan", "planning", (), CommandPermission.UTILITY),
        ("plan steps", "Show plan steps", "planning", (), CommandPermission.UTILITY),
        ("plan validate", "Validate a plan", "planning", (), CommandPermission.UTILITY),
        ("plan alternatives", "Show plan alternatives", "planning", (), CommandPermission.UTILITY),
        ("plan approve", "Approve a plan", "planning", (), CommandPermission.UTILITY),
        ("plan reject", "Reject a plan", "planning", (), CommandPermission.UTILITY),
        ("plan pause", "Pause a plan", "planning", (), CommandPermission.UTILITY),
        ("plan resume", "Resume a plan", "planning", (), CommandPermission.UTILITY),
        ("plan cancel", "Cancel a plan", "planning", (), CommandPermission.UTILITY),
        ("plan replan", "Create a revised plan", "planning", (), CommandPermission.UTILITY),
        ("plan history", "Show plan history", "planning", (), CommandPermission.DIAGNOSTIC),
        ("plan mode", "Set planning mode", "planning", (), CommandPermission.UTILITY),
        ("plan limits", "Show planning limits", "planning", (), CommandPermission.DIAGNOSTIC),
        ("voice status", "Show voice status", "voice", (), CommandPermission.UTILITY),
        ("voice on", "Enable voice sessions", "voice", (), CommandPermission.UTILITY),
        ("voice off", "Disable voice", "voice", (), CommandPermission.UTILITY),
        ("voice listen", "Start explicit listening", "voice", (), CommandPermission.UTILITY),
        ("voice cleanup", "Remove temporary voice audio", "voice", (), CommandPermission.UTILITY),
        ("voice stop", "Stop active speech", "voice", (), CommandPermission.UTILITY),
        ("voice pause", "Pause speech at a safe boundary", "voice", (), CommandPermission.UTILITY),
        ("voice resume", "Resume retained speech", "voice", (), CommandPermission.UTILITY),
        ("voice speaking", "Show speech playback state", "voice", (), CommandPermission.UTILITY),
        ("voice speaking status", "Show speech playback state", "voice", (), CommandPermission.UTILITY),
        ("voice repeat", "Repeat the last safe reply", "voice", (), CommandPermission.UTILITY),
        ("voice replay", "Repeat the last safe reply", "voice", (), CommandPermission.UTILITY),
        ("voice correction", "Submit a corrected request", "voice", (), CommandPermission.UTILITY),
        ("voice cancel", "Cancel voice session", "voice", (), CommandPermission.UTILITY),
        ("voice interrupt", "Interrupt voice output", "voice", (), CommandPermission.UTILITY),
        ("voice session", "Show voice session", "voice", (), CommandPermission.UTILITY),
        ("voice devices", "List audio devices", "voice", (), CommandPermission.UTILITY),
        ("voice backend", "Configure voice backend", "voice", (), CommandPermission.UTILITY),
        ("voice device", "Configure audio device", "voice", (), CommandPermission.UTILITY),
        ("voice input", "Configure voice input", "voice", (), CommandPermission.UTILITY),
        ("voice output", "Configure voice output", "voice", (), CommandPermission.UTILITY),
        ("voice say", "Speak with local TTS", "voice", (), CommandPermission.UTILITY),
        ("voice transcribe", "Transcribe an audio file", "voice", (), CommandPermission.UTILITY),
        ("voice mode", "Set voice mode", "voice", (), CommandPermission.UTILITY),
        ("voice privacy", "Set voice privacy", "voice", (), CommandPermission.UTILITY),
        ("voice language", "Set voice language", "voice", (), CommandPermission.UTILITY),
        ("voice rate", "Set speech rate", "voice", (), CommandPermission.UTILITY),
        ("voice volume", "Set speech volume", "voice", (), CommandPermission.UTILITY),
        ("voice raw-audio", "Set raw audio retention", "voice", (), CommandPermission.UTILITY),
        ("voice limits", "Show voice limits", "voice", (), CommandPermission.DIAGNOSTIC),
        ("voice health", "Show voice health", "voice", (), CommandPermission.DIAGNOSTIC),
        ("vision status", "Show vision readiness", "vision", (), CommandPermission.DIAGNOSTIC),
        ("vision models", "Show local Ollama vision models", "vision", (), CommandPermission.DIAGNOSTIC),
        ("vision analyze", "Analyze an image locally", "vision", (), CommandPermission.UTILITY),
        ("vision describe", "Describe an image", "vision", (), CommandPermission.UTILITY),
        ("vision ask", "Ask a question about an image", "vision", (), CommandPermission.UTILITY),
        ("vision audit", "Show bounded vision audit metadata", "vision", (), CommandPermission.DIAGNOSTIC),
        ("vision cleanup", "Clear vision audit metadata", "vision", (), CommandPermission.UTILITY),
        ("image status", "Show image generation readiness", "image", (), CommandPermission.DIAGNOSTIC),
        ("image help", "Show image generation command help", "image", (), CommandPermission.UTILITY),
        ("image providers", "List registered image providers", "image", (), CommandPermission.DIAGNOSTIC),
        ("image generate", "Generate an image when a provider is ready", "image", (), CommandPermission.UTILITY),
        ("image plan", "Dry-run an image generation request", "image", (), CommandPermission.UTILITY),
        ("image safety", "Evaluate image prompt safety", "image", (), CommandPermission.UTILITY),
        ("image history", "Show bounded recent image jobs", "image", (), CommandPermission.DIAGNOSTIC),
        ("image show", "Show one image generation job", "image", (), CommandPermission.DIAGNOSTIC),
        ("video status", "Show video editing readiness", "video", (), CommandPermission.DIAGNOSTIC),
        ("video help", "Show video editing command help", "video", (), CommandPermission.UTILITY),
        ("video providers", "List registered video providers", "video", (), CommandPermission.DIAGNOSTIC),
        ("video plan", "Plan a non-destructive video edit", "video", (), CommandPermission.UTILITY),
        ("video safety", "Evaluate video prompt safety", "video", (), CommandPermission.UTILITY),
        ("video history", "Show bounded recent video plans", "video", (), CommandPermission.DIAGNOSTIC),
        ("video show", "Show one video editing plan", "video", (), CommandPermission.DIAGNOSTIC),
        ("sync status", "Show sync and local queue readiness", "sync", (), CommandPermission.SYNC),
        ("sync on", "Enable manual local queue mode", "sync", (), CommandPermission.SYNC),
        ("sync off", "Disable sync without deleting queue items", "sync", (), CommandPermission.SYNC),
        ("sync queue", "List bounded sync queue metadata", "sync", (), CommandPermission.SYNC),
        ("sync queue summary", "Summarize sync queue", "sync", (), CommandPermission.SYNC),
        ("sync add", "Queue an approved sanitized summary", "sync", (), CommandPermission.SYNC),
        ("sync inspect", "Inspect one sanitized sync item", "sync", (), CommandPermission.SYNC),
        ("sync cancel", "Cancel a queued sync item", "sync", (), CommandPermission.SYNC),
        ("sync retry", "Retry an eligible failed sync item", "sync", (), CommandPermission.SYNC),
        ("sync cleanup", "Prune bounded sync history", "sync", (), CommandPermission.SYNC),
        ("sync run", "Run a manual sync batch", "sync", (), CommandPermission.SYNC),
        ("sync conflicts", "List unresolved sync conflicts", "sync", (), CommandPermission.SYNC),
        ("web status", "Show Web Automation readiness", "web", (), CommandPermission.WEB),
        ("web open", "Open a policy-approved URL read-only", "web", (), CommandPermission.WEB),
        ("web title", "Read the active page title", "web", (), CommandPermission.WEB),
        ("web url", "Read the active safe URL", "web", (), CommandPermission.WEB),
        ("web snapshot", "Read non-persistent page metadata", "web", (), CommandPermission.WEB),
        ("web close", "Close the active web session", "web", (), CommandPermission.WEB),
        ("web audit", "Show bounded web audit metadata", "web", (), CommandPermission.WEB),
        ("web policy", "Show Web Automation policy", "web", (), CommandPermission.WEB),
        ("web session", "Show active Web Automation sessions", "web", (), CommandPermission.WEB),
        ("mobile status", "Show Mobile Automation foundation status", "mobile", (), CommandPermission.MOBILE),
        ("mobile policy", "Show mobile privacy and action policy", "mobile", (), CommandPermission.MOBILE),
        ("mobile capabilities", "Show current and future mobile capabilities", "mobile", (), CommandPermission.MOBILE),
        ("mobile setup", "Show safe future mobile setup guidance", "mobile", (), CommandPermission.MOBILE),
        ("mobile plan", "Plan a mobile workflow without execution", "mobile", (), CommandPermission.MOBILE),
        ("mobile audit", "Show bounded redacted mobile audit", "mobile", (), CommandPermission.MOBILE),
        ("mobile close", "Clear mobile planning session state", "mobile", (), CommandPermission.MOBILE),
        ("mobile devices", "Show privacy-safe device summary", "mobile", (), CommandPermission.MOBILE),
        ("mobile session", "Show mobile planning session state", "mobile", (), CommandPermission.MOBILE),
        ("departments", "Show department summary", "department", (), CommandPermission.DEPARTMENT),
        ("department list", "List departments", "department", (), CommandPermission.DEPARTMENT),
        ("memory", "Show memory summary", "memory", (), CommandPermission.MEMORY),
        ("memory status", "Show memory status", "memory", (), CommandPermission.MEMORY),
        ("memory help", "Show memory help", "memory", (), CommandPermission.MEMORY),
        ("memory list", "List memories", "memory", (), CommandPermission.MEMORY),
        ("memory search", "Search memories", "memory", (), CommandPermission.MEMORY),
        ("memory show", "Show a memory", "memory", (), CommandPermission.MEMORY),
        ("memory remember", "Remember a memory", "memory", (), CommandPermission.MEMORY),
        ("memory forget", "Forget a memory", "memory", (), CommandPermission.MEMORY),
        ("memory update", "Update a memory", "memory", (), CommandPermission.MEMORY),
        ("memory archive", "Archive a memory", "memory", (), CommandPermission.MEMORY),
        ("memory recent", "Show recent memories", "memory", (), CommandPermission.MEMORY),
        ("memory preferences", "Show memory preferences", "memory", (), CommandPermission.MEMORY),
        ("memory projects", "Show memory projects", "memory", (), CommandPermission.MEMORY),
        ("memory audit", "Show memory audit trail", "memory", (), CommandPermission.MEMORY),
        ("memory cleanup", "Clean up memory records", "memory", (), CommandPermission.MEMORY),
        ("memory consolidate", "Consolidate memory records", "memory", (), CommandPermission.MEMORY),
        ("knowledge", "Show knowledge summary", "knowledge", (), CommandPermission.KNOWLEDGE),
        ("knowledge search", "Search knowledge architecture hook", "knowledge", (), CommandPermission.KNOWLEDGE),
        ("tasks", "Show task summary", "task", (), CommandPermission.TASK),
        ("task list", "List tasks", "task", (), CommandPermission.TASK),
        ("task status", "Show task status", "task", (), CommandPermission.TASK),
        ("workflow", "Show workflow summary", "workflow", (), CommandPermission.WORKFLOW),
        ("workflow list", "List workflows", "workflow", (), CommandPermission.WORKFLOW),
        ("config", "Show config summary", "configuration", (), CommandPermission.CONFIGURATION),
        ("config show", "Show configuration metadata", "configuration", (), CommandPermission.CONFIGURATION),
        ("profile", "Show personal intelligence summary", "personal", (), CommandPermission.CONVERSATION),
        ("profile show", "Show personal intelligence summary", "personal", (), CommandPermission.CONVERSATION),
        ("profile list", "List personal intelligence items", "personal", (), CommandPermission.CONVERSATION),
        ("profile explain", "Explain a personal intelligence item", "personal", (), CommandPermission.CONVERSATION),
        ("profile update", "Update a personal intelligence item", "personal", (), CommandPermission.CONVERSATION),
        ("profile forget", "Forget a personal intelligence item", "personal", (), CommandPermission.CONVERSATION),
        ("profile confirm", "Confirm a personal intelligence item", "personal", (), CommandPermission.CONVERSATION),
        ("profile reject", "Reject a personal intelligence item", "personal", (), CommandPermission.CONVERSATION),
        ("context", "Show current context", "conversation", (), CommandPermission.CONVERSATION),
        ("context show", "Show current context", "conversation", (), CommandPermission.CONVERSATION),
        ("context recent", "Show recent context history", "conversation", (), CommandPermission.CONVERSATION),
        ("context clear", "Clear active context", "conversation", (), CommandPermission.CONVERSATION),
        ("context pause", "Pause active context", "conversation", (), CommandPermission.CONVERSATION),
        ("context resume", "Resume previous context", "conversation", (), CommandPermission.CONVERSATION),
        ("context previous", "Return to previous context", "conversation", (), CommandPermission.CONVERSATION),
        ("objective show", "Show the current objective", "conversation", (), CommandPermission.CONVERSATION),
        ("goal", "Show goal intelligence summary", "goal", (), CommandPermission.CONVERSATION),
        ("goal show", "Show the active goal", "goal", (), CommandPermission.CONVERSATION),
        ("goal list", "List goals", "goal", (), CommandPermission.CONVERSATION),
        ("goal review", "Review a goal", "goal", (), CommandPermission.CONVERSATION),
        ("goal progress", "Show goal progress", "goal", (), CommandPermission.CONVERSATION),
        ("goal next", "Show next meaningful goal step", "goal", (), CommandPermission.CONVERSATION),
        ("goal blockers", "Show goal blockers", "goal", (), CommandPermission.CONVERSATION),
        ("goal evaluate", "Evaluate goal completion", "goal", (), CommandPermission.CONVERSATION),
        ("goal conflicts", "Show goal conflicts", "goal", (), CommandPermission.CONVERSATION),
        ("goal align", "Explain goal-task alignment", "goal", (), CommandPermission.CONVERSATION),
        ("goal portfolio", "Show goal portfolio", "goal", (), CommandPermission.CONVERSATION),
        ("goal pause", "Pause a goal", "goal", (), CommandPermission.CONVERSATION),
        ("goal resume", "Resume a goal", "goal", (), CommandPermission.CONVERSATION),
        ("goal complete", "Complete a goal", "goal", (), CommandPermission.CONVERSATION),
        ("logs", "Show logs summary", "diagnostic", (), CommandPermission.DIAGNOSTIC),
        ("logs recent", "Show recent logs metadata", "diagnostic", (), CommandPermission.DIAGNOSTIC),
    )
    for name, description, category, aliases, permission in commands:
        registry.register(
            CommandRecord(
                name=name,
                handler=_handler_for(name),
                description=description,
                category=category,
                aliases=aliases,
                permissions=(permission,),
            )
        )


def _handler_for(name: str):
    def handler(context: CommandContext) -> ConversationResponse:
        manager = _manager(context)
        if name == "help" and manager is not None:
            return _text_response(manager.help.render(manager.registry))
        if name == "project status":
            return _project_health_summary(context)
        if name.startswith("limitations "):
            try:
                return _text_response(LimitationsRegister().command(name, context.arguments))
            except LimitationsRegisterError as exc:
                return _text_response(f"Limitations unavailable: {exc}.")
        if name.startswith("conversation "):
            intelligence = _conversation_intelligence(context)
            if intelligence is None:
                return _text_response("Conversation intelligence is unavailable.")
            if name == "conversation reset":
                intelligence.reset()
                session = getattr(context.conversation_context, "session", None)
                if session is not None:
                    session.current_topic = None
                return _text_response("Conversation context reset. Persistent memory was not changed.")
            if name == "conversation summary": return _text_response(intelligence.summary_text())
            if name == "conversation mode": return _text_response(intelligence.mode_text())
            if name == "conversation confidence": return _text_response(intelligence.confidence_text())
            if name == "conversation topic": return _text_response(intelligence.topic_text())
            return _text_response(intelligence.status_text())
        if name == "memory":
            memory = _memory_intelligence(context)
            if memory is None:
                return _text_response("memory summary unavailable: Memory intelligence is unavailable.")
            return _text_response("Memory summary: " + memory.status_text())
        if name.startswith("memory "):
            memory = _memory_intelligence(context)
            if memory is None:
                return _text_response(f"{name} unavailable: Memory intelligence is unavailable.")
            try:
                summary = memory.handle_command(name, context.arguments)
            except Exception as exc:  # pragma: no cover - defensive command surface
                return _text_response(f"Memory command failed: {exc}")
            return _text_response(summary)
        if name == "exit":
            return ConversationResponse(response="Shutting down JARVIS OS.", should_exit=True)
        if name == "clear":
            return ConversationResponse(response="", should_clear=True)
        if name == "history" and manager is not None:
            return _text_response(f"Command history: {len(manager.history.list_history())} entries")
        if name == "metrics" and manager is not None:
            return _text_response(f"Commands executed: {manager.metrics.commands_executed}")
        if name in {"agents", "agent status", "agent list", "agent capabilities", "agent show", "agent find", "agent diagnostics", "agent ready", "agent unavailable", "agent future", "agent risks", "agent approvals"}:
            return _text_response(render_agent_command(_phase3_agent_registry(context), name, context.arguments))
        if name.startswith("prime "):
            return _text_response(render_prime_command(_prime_agent(context), name, context.arguments))
        if name.startswith("model advanced "):
            return _text_response(render_advanced_model_command(_advanced_model_planner(context), name, context.arguments))
        if name.startswith("model "):
            registry, router = _model_foundation(context)
            return _text_response(render_model_command(registry, router, name, context.arguments))
        if name.startswith("skill "):
            return _text_response(render_skill_command(_skill_registry(context), name, context.arguments))
        if name.startswith("research "):
            return _text_response(render_research_command(_research_agent(context), name, context.arguments))
        if name.startswith("coding "):
            return _text_response(render_coding_command(_coding_agent(context), name, context.arguments))
        if name.split(" ", 1)[0] in {"execution","approval","broker","file-exec","command","git-exec","notification"} or name in {"browser policy","browser validate","browser dry-run","browser read","browser read-show","browser read-history","scheduler runtime-status","scheduler jobs","scheduler due","scheduler create","scheduler run","scheduler run-due","scheduler pause","scheduler resume","scheduler cancel","scheduler runs","scheduler runtime-policy"}:
            return _text_response(render_phase4_command(get_phase4_runtime(Path(__file__).resolve().parents[1]), name, context.arguments, context.flags))
        if name.startswith("document "):
            return _text_response(render_document_command(_document_agent(context), name, context.arguments))
        if name.startswith("browser "):
            return _text_response(render_browser_command(_browser_agent(context), name, context.arguments))
        if name.startswith("scheduler "):
            return _text_response(render_scheduler_command(_scheduler_agent(context), name, context.arguments))
        if name.startswith("communication "):
            return _text_response(render_communication_command(_communication_agent(context), name, context.arguments))
        if name.startswith("adapter "):
            return _text_response(render_adapter_command(_adapter_agent(context), name, context.arguments))
        if name.startswith("evaluation "):
            return _text_response(render_evaluation_command(_evaluation_runner(context), name, context.arguments))
        if name.startswith("release-readiness "):
            return _text_response(render_release_command(_release_evaluator(context), name, context.arguments))
        if name.startswith("multiagent "):
            agent_manager = _agent_manager(context)
            orchestrator = getattr(agent_manager, "orchestrator", None)
            if orchestrator is None:
                return _text_response("Multi-agent intelligence is not available.")
            if name == "multiagent status":
                status = orchestrator.status()
                return _text_response(
                    f"Multi-agent status: mode={status['mode']} coordinations={status['coordinations']} active={status['active']}",
                    **status,
                )
            if name == "multiagent list":
                records = orchestrator.store.list()
                if not records:
                    return _text_response("No multi-agent coordinations have been recorded.")
                return _text_response("Multi-agent coordinations: " + ", ".join(f"{item.coordination_id}:{item.status.value}" for item in records[:10]))
            if name == "multiagent limits":
                limits = orchestrator.status()["limits"]
                return _text_response("Multi-agent limits: " + ", ".join(f"{key}={value}" for key, value in limits.items()), limits=limits)
            if name == "multiagent show":
                coordination_id = context.arguments[0] if context.arguments else ""
                record = orchestrator.store.get(coordination_id)
                if record is None:
                    return _text_response("Coordination not found.")
                return _text_response(
                    f"Coordination {record.coordination_id}: status={record.status.value} mode={record.mode.value} agents={len(record.plan.participating_agents)} results={len(record.results)}",
                    coordination_id=record.coordination_id,
                    status=record.status.value,
                )
            if name == "multiagent cancel":
                coordination_id = context.arguments[0] if context.arguments else ""
                return _text_response("Coordination cancellation requested." if orchestrator.cancel(coordination_id) else "Coordination not found or no longer cancellable.")
            if name == "multiagent mode":
                if not context.arguments:
                    return _text_response(f"Multi-agent mode: {orchestrator.mode.value}")
                try:
                    selected = orchestrator.set_mode(context.arguments[0])
                except ValueError:
                    return _text_response("Mode must be off, confirm, automatic-safe, or automatic.")
                conversation = context.conversation_context
                if conversation is not None:
                    conversation.session.metadata["multiagent_mode"] = selected.value
                return _text_response(f"Multi-agent mode set to {selected.value}.", mode=selected.value)
        if name == "tools status":
            tools = _tool_manager(context)
            if tools is None:
                return _text_response("Tools unavailable: Tool Intelligence is not initialized.")
            records = tools.list_tools()
            ready = sum(1 for item in records if item.enabled and item.healthy and item.available)
            return _text_response(
                f"Tools status: ready={ready}/{len(records)} mode={tools.mode.value}",
                registered=len(records),
                ready=ready,
                mode=tools.mode.value,
            )
        if name.startswith("tool "):
            tools = _tool_manager(context)
            if tools is None:
                return _text_response("Tool Intelligence is not available.")
            args = context.arguments
            if name == "tool list":
                return _text_response("Tools: " + ", ".join(item.tool_id for item in tools.list_tools()))
            if name in {"tool show", "tool permissions"}:
                record = tools.lookup(args[0] if args else "")
                if record is None: return _text_response("Tool not found.")
                if name == "tool permissions": return _text_response(f"Tool permissions for {record.tool_id}: " + ", ".join(record.permissions))
                return _text_response(f"Tool {record.tool_id}: {record.description} risk={record.risk_class.value} enabled={record.enabled} healthy={record.healthy}")
            if name == "tool health":
                records = tools.list_tools()
                if args: records = tuple(item for item in records if item.tool_id == args[0])
                return _text_response("Tool health: " + (", ".join(f"{item.tool_id}={'healthy' if item.healthy and item.available else 'unavailable'}" for item in records) or "none"))
            if name == "tool match":
                selection = tools.match(args[0] if args else "")
                return _text_response(f"Tool match: {selection.selected_tool_id or 'none'} ({selection.selection_reason})")
            if name == "tool dry-run":
                if len(args) < 2: return _text_response("Usage: tool dry-run <tool_id> <operation> [key=value ...]")
                values = dict(item.split("=", 1) for item in args[2:] if "=" in item)
                result = tools.execute(tools.prepare("command-tool-dry-run", args[0], args[1], values, dry_run=True), executive_approved=True)
                return _text_response(result.content or ", ".join(result.errors), invocation_id=result.invocation_id, status=result.status.value)
            if name == "tool history":
                records = tools.history()
                return _text_response("Tool history: " + (", ".join(f"{item.invocation_id}:{item.status.value}" for item in records[:10]) or "none"))
            if name == "tool invocation":
                record = tools.invocation(args[0] if args else "")
                return _text_response(f"Tool invocation: {record.status.value} tool={record.tool_id}" if record else "Tool invocation not found.")
            if name == "tool cancel": return _text_response("Tool cancellation requested." if tools.cancel(args[0] if args else "") else "Tool invocation not found or no longer active.")
            if name == "tool mode":
                if not args: return _text_response(f"Tool mode: {tools.mode.value}")
                try: selected = tools.set_mode(args[0])
                except ValueError: return _text_response("Mode must be off, confirm, automatic-safe, or automatic.")
                context.conversation_context.session.metadata["tool_mode"] = selected.value
                return _text_response(f"Tool mode set to {selected.value}.")
            if name == "tool limits":
                values = {field: getattr(tools.limits, field) for field in tools.limits.__slots__}
                return _text_response("Tool limits: " + ", ".join(f"{key}={value}" for key, value in values.items()))
        if name.startswith("plan "):
            planner=_planning_manager(context); args=context.arguments
            if planner is None:return _text_response("Autonomous Planning is not available.")
            if name=="plan status":return _text_response(f"Planning status: mode={planner.mode.value} plans={len(planner.plans)}")
            if name=="plan list":return _text_response("Plans: "+(", ".join(f"{p.plan_id}:{p.status.value}" for p in planner.plans.values()) or "none"))
            pid=args[0] if args else ""; plan=planner.plans.get(pid)
            if name=="plan mode":
                if not args:return _text_response(f"Planning mode: {planner.mode.value}")
                try:selected=planner.set_mode(args[0])
                except ValueError:return _text_response("Mode must be off, suggest, confirm, or automatic-safe.")
                context.conversation_context.session.metadata["plan_mode"]=selected.value; return _text_response(f"Planning mode set to {selected.value}.")
            if name=="plan limits":return _text_response("Planning limits: "+", ".join(f"{k}={getattr(planner.limits,k)}" for k in planner.limits.__slots__))
            if plan is None:return _text_response("Plan not found.")
            if name=="plan show":return _text_response(f"Plan {pid}: {plan.title} status={plan.status.value} version={plan.version}")
            if name=="plan steps":return _text_response("Plan steps: "+", ".join(f"{s.sequence}:{s.title}" for s in plan.steps))
            if name=="plan validate":
                result=planner.validate(plan); return _text_response(f"Plan validation: {'valid' if result.valid else 'invalid'}"+(" errors="+",".join(result.errors) if result.errors else ""))
            if name=="plan approve":
                try: approved=planner.approve(pid,f"command:{context.request_id}")
                except ValueError as exc:return _text_response(f"Plan approval failed: {exc}")
                return _text_response(f"Plan approved: {approved.plan_id}. Execution has not started.")
            if name=="plan reject": planner.cancel(pid); return _text_response("Plan rejected.")
            if name=="plan pause": planner.pause(pid); return _text_response("Plan paused.")
            if name=="plan resume":
                try:planner.resume(pid)
                except ValueError as exc:return _text_response(f"Plan resume failed: {exc}")
                return _text_response("Plan resumed for review.")
            if name=="plan cancel":planner.cancel(pid); return _text_response("Plan cancelled.")
            if name=="plan replan":
                try:new=planner.replan(pid,"user request")
                except ValueError as exc:return _text_response(f"Replanning failed: {exc}")
                return _text_response(f"Replanned as {new.plan_id} version={new.version}.")
            if name in {"plan alternatives","plan history"}:return _text_response(f"Plan {pid} has version {plan.version}; alternatives are bounded and advisory.")
        if name.startswith("voice "):
            voice=_voice_manager(context);args=context.arguments
            if voice is None:return _text_response("Voice Intelligence is unavailable; text mode remains active.")
            if name=="voice status":
                backend=voice.registry.get(voice.selected_output_backend);input_status=voice.input_status()
                available=bool(backend and backend.available);retained=len(voice.retained_audio_files());playback_status=voice.playback_status()
                return _text_response(
                    "Voice status: "
                    f"output={'on' if voice.output_enabled else 'off'} "
                    f"output_backend={voice.selected_output_backend} "
                    f"playback={'ready' if available else 'unavailable'} "
                    f"input={'on' if voice.input_enabled else 'off'} "
                    f"input_backend={voice.selected_input_backend} "
                    f"stt={'ready' if input_status['stt_available'] else 'unavailable'} "
                    f"stt_provider={input_status['provider']} model={'ready' if input_status['model_ready'] else 'missing'} "
                    f"microphone={'ready' if input_status['microphone_available'] else input_status['capture_status']} "
                    f"raw_audio_persistence={'on' if voice.raw_audio_persistence else 'off'} "
                    f"temp_directory={voice.temp_directory} retained_audio={retained} "
                    f"mode={voice.mode.value} privacy={voice.privacy_mode} speaking={playback_status['state']}",
                    output_enabled=voice.output_enabled,
                    output_backend=voice.selected_output_backend,
                    playback_ready=available,
                    input_enabled=voice.input_enabled,
                    input_backend=voice.selected_input_backend,
                    stt_available=input_status["stt_available"],
                    stt_provider=input_status["provider"],
                    stt_provider_status=input_status["provider_status"],
                    stt_model_ready=input_status["model_ready"],
                    microphone_available=input_status["microphone_available"],
                    capture_status=input_status["capture_status"],
                    raw_audio_persistence=voice.raw_audio_persistence,
                    temp_directory=str(voice.temp_directory),
                    retained_audio_count=retained,
                    playback=playback_status,
                )
            if name=="voice on":voice.enabled=True;return _text_response("Voice enabled. Microphone capture remains disabled until explicitly activated.")
            if name=="voice off":voice.enabled=False;voice.input_enabled=False;voice.mode=type(voice.mode).OFF;voice.cancel();return _text_response("Voice disabled. Text mode remains active.")
            if name=="voice input":
                status=voice.input_status()
                if args and args[0]=="off":voice.input_enabled=False;return _text_response("Voice input disabled. No microphone is active.")
                if args and args[0]=="on":
                    if not status["stt_available"]:
                        voice.input_enabled=False
                        message="Voice input is not available because no local STT model is configured. The optional Vosk dependency is also missing." if not status["dependency_ready"] else "Voice input is not available because no local STT model (Vosk) is configured."
                        return _text_response(message,missing_capabilities=status["missing_capabilities"])
                    if not status["microphone_available"]:
                        voice.input_enabled=False
                        return _text_response("Voice input is unavailable because no microphone capture adapter/device is ready.",missing_capabilities=status["missing_capabilities"])
                    voice.input_enabled=True;voice.enabled=True;return _text_response("Voice input enabled for explicit push-to-talk listening. Continuous listening remains disabled.")
                if args and args[0]=="test":
                    if not voice.input_enabled:return _text_response("Voice input is disabled; no microphone was activated.")
                    if not status["ready"]:return _text_response("Voice input test unavailable: configure Vosk, a local model, and a microphone capture adapter.",missing_capabilities=status["missing_capabilities"])
                    result=voice.listen(parent_request_id="command-voice-input-test")
                    if result.status.value=="completed":return _text_response(f"Voice input test completed locally: {result.text}",status=result.status.value,confidence=result.confidence,provider_id=result.backend_id)
                    return _text_response(f"Voice input test {result.status.value}: {', '.join(result.errors) or 'no clear speech detected'}",status=result.status.value)
                return _text_response(
                    f"Voice input: {'on' if voice.input_enabled else 'off'} backend={status['backend']} "
                    f"stt={'ready' if status['stt_available'] else 'unavailable'} "
                    f"provider={status['provider']} dependency={'ready' if status['dependency_ready'] else 'missing'} "
                    f"model={'ready' if status['model_ready'] else 'missing'} microphone={'ready' if status['microphone_available'] else status['capture_status']} "
                    "raw_audio_persistence=off continuous_listening=off wake_word=off",
                    **status,
                )
            if name=="voice output":
                if args and args[0] in {"on","off"}:
                    if args[0]=="on":
                        backend=voice.registry.get(voice.selected_output_backend)
                        if backend is None or not backend.available:
                            voice.output_enabled=False
                            return _text_response(f"Voice output unavailable: {voice.selected_output_backend} is not ready.")
                        voice.output_enabled=True;voice.enabled=True
                        return _text_response(f"Voice output enabled through {voice.selected_output_backend}. Safe assistant replies will be spoken.")
                    voice.output_enabled=False;voice.stop_playback(wait=True)
                    return _text_response("Voice output disabled. Replies will remain text-only.")
                return _text_response(f"Voice output: {voice.output_enabled}")
            if name=="voice say":
                if not args:return _text_response("Please provide text to speak.")
                try:r=voice.start_playback(" ".join(args),parent_request_id="command-voice-say")
                except (RuntimeError,ValueError) as exc:return _text_response(f"Voice synthesis blocked: {exc}")
                return _text_response(f"Voice playback queued through {voice.selected_output_backend}.",**r)
            if name=="voice transcribe":
                if not args:return _text_response("Please provide an allowed WAV file path.")
                try:r=voice.transcribe_file(args[0])
                except ValueError as exc:return _text_response(f"Transcription rejected: {exc}")
                if r.status.value=="completed":return _text_response(f"Transcript: {r.text}",status=r.status.value,confidence=r.confidence,provider_id=r.backend_id,transcription_id=r.transcription_id)
                reason=", ".join(r.errors) or r.status.value
                return _text_response(f"Offline transcription {r.status.value}: {reason}.",status=r.status.value,provider_id=r.backend_id,transcription_id=r.transcription_id)
            if name=="voice devices":
                direction=args[0] if args and args[0] in {"input","output"} else None;items=voice.devices(direction);return _text_response("Voice devices: "+(", ".join(f"{x.device_id}:{x.name}" for x in items) or "none discovered"))
            if name=="voice backend":
                if not args or args[0]=="list":return _text_response("Voice backends: "+", ".join(f"{x.adapter_id}:{x.health_check()['status']}" for x in voice.registry.list()))
                if len(args)<2:return _text_response("Specify input or output and a backend id.")
                if voice.registry.get(args[1]) is None:return _text_response("Voice backend not found.")
                if args[0]=="input":voice.selected_input_backend=args[1]
                elif args[0]=="output":voice.selected_output_backend=args[1]
                else:return _text_response("Backend direction must be input or output.")
                return _text_response(f"Voice {args[0]} backend set to {args[1]}.")
            if name=="voice mode":
                if not args:return _text_response(f"Voice mode: {voice.mode.value}")
                try:voice.mode=type(voice.mode)(args[0])
                except ValueError:return _text_response("Unsupported voice mode.")
                return _text_response(f"Voice mode set to {voice.mode.value}. No background listening was started.")
            if name=="voice privacy":
                if not args or args[0] not in {"strict","standard","diagnostic"}:return _text_response("Privacy must be strict, standard, or diagnostic.")
                voice.privacy_mode=args[0];return _text_response(f"Voice privacy set to {voice.privacy_mode}.")
            if name=="voice language":voice.language=args[0] if args else voice.language;return _text_response(f"Voice language: {voice.language}")
            if name in {"voice rate","voice volume"}:
                try:value=int(args[0])
                except (IndexError,ValueError):return _text_response("A numeric value is required.")
                if name=="voice rate" and -10<=value<=10:voice.rate=value
                elif name=="voice volume" and 0<=value<=100:voice.volume=value
                else:return _text_response("Value is outside the supported range.")
                return _text_response(f"{name.title()} set to {value}.")
            if name=="voice raw-audio":
                if not args or args[0] not in {"on","off"}:return _text_response("Specify on or off.")
                voice.raw_audio_persistence=args[0]=="on";return _text_response(f"Raw audio retention {'enabled with explicit consent' if voice.raw_audio_persistence else 'disabled'}.")
            if name=="voice stop":return _text_response("Voice playback stopped. Unspoken chunks were retained for 'voice resume'." if voice.stop_playback(wait=True) else "VOICE_NOT_SPEAKING: No active voice playback.")
            if name=="voice pause":
                result=voice.pause_playback();return _text_response(result["message"],**result)
            if name=="voice resume":
                result=voice.resume_playback();return _text_response(result["message"],**result)
            if name in {"voice speaking","voice speaking status"}:
                state=voice.playback_status();return _text_response(f"Voice playback: state={state['state']} chunk={state['current_chunk']}/{state['total_chunks']} completed={state['completed_chunks']} remaining={state['remaining_chunks']} resumable={'yes' if state['resumable'] else 'no'} interrupted_chunk={'yes' if state['interrupted_chunk'] else 'no'}.",**state)
            if name in {"voice repeat","voice replay"}:
                try:result=voice.repeat_last()
                except ValueError as exc:return _text_response(f"Voice repeat blocked: {exc}")
                return _text_response(result["message"],**result)
            if name=="voice correction":
                voice.stop_playback(wait=True);corrected=" ".join(args).strip()
                if not corrected:return _text_response("VOICE_CORRECTION_EMPTY: Provide corrected text; no request was submitted.")
                return _text_response(f"Corrected request submitted: {corrected}",voice_transcript=corrected,dispatch_voice_transcript=True,voice_correction=True)
            if name=="voice interrupt":
                voice.stop_playback(wait=True);status=voice.input_status()
                if not status["stt_available"]:return _text_response("VOICE_INTERRUPT_STT_UNAVAILABLE: Current speech stopped, but local transcription is unavailable.")
                if not voice.enabled or not voice.input_enabled:return _text_response("VOICE_INTERRUPT_STT_UNAVAILABLE: Current speech stopped; voice input is disabled and no microphone was activated.")
                if not status["microphone_available"]:return _text_response("VOICE_INTERRUPT_STT_UNAVAILABLE: Current speech stopped, but no microphone capture adapter is ready.")
                result=voice.listen(parent_request_id="command-voice-interrupt")
                if result.status.value!="completed":return _text_response(f"VOICE_INTERRUPT_NO_SPEECH: {', '.join(result.errors) or result.status.value}.",status=result.status.value)
                return _text_response(f"Interruption transcript: {result.text}. Sending through the normal JARVIS path.",voice_transcript=result.text,dispatch_voice_transcript=True,voice_interruption=True)
            if name=="voice cancel":return _text_response("Voice playback cancelled; queued speech was permanently cleared." if voice.cancel_playback(wait=True) else "VOICE_NOT_SPEAKING: No active or resumable voice playback.")
            if name=="voice listen":
                status=voice.input_status()
                if not status["stt_available"]:
                    message="Voice input is not available because no local STT model is configured. The optional Vosk dependency is also missing." if not status["dependency_ready"] else "Voice input is not available because no local STT model (Vosk) is configured."
                    return _text_response(message,missing_capabilities=status["missing_capabilities"])
                if not voice.enabled or not voice.input_enabled:return _text_response("Voice input is disabled; no microphone was activated.")
                if not status["microphone_available"]:return _text_response("Voice input is unavailable because no microphone capture adapter is configured.",missing_capabilities=status["missing_capabilities"])
                result=voice.listen(parent_request_id="command-voice-listen")
                if result.status.value!="completed":return _text_response(f"Voice listen {result.status.value}: {', '.join(result.errors) or 'no clear speech detected'}",status=result.status.value,provider_id=result.backend_id)
                should_send=bool(args and args[0].lower()=="send")
                return _text_response(f"Transcript: {result.text}"+(" Sending through the normal JARVIS path." if should_send else " Use 'voice listen send' to submit it."),status=result.status.value,confidence=result.confidence,provider_id=result.backend_id,transcription_id=result.transcription_id,voice_transcript=result.text if should_send else None,dispatch_voice_transcript=should_send)
            if name=="voice cleanup":
                cleanup=voice.cleanup_temp_audio(remove_all=True)
                return _text_response(f"Voice cleanup complete: removed={cleanup['removed']} remaining={cleanup['remaining']} failed={cleanup['failed']}.",**cleanup)
            if name=="voice session":
                sessions=tuple(voice.sessions.values());return _text_response(f"Voice session: {sessions[-1].voice_session_id}:{sessions[-1].state.value}" if sessions else "No voice session exists.")
            if name=="voice limits":return _text_response("Voice limits: "+", ".join(f"{k}={getattr(voice.limits,k)}" for k in voice.limits.__slots__))
            if name=="voice health":return _text_response("Voice health: "+json.dumps(voice.health(),default=str))
            if name=="voice device":return _text_response("Explicit device selection is unavailable until a matching capture/output adapter exposes device IDs.")
        if name.startswith("vision "):
            vision=_vision_manager(context);args=context.arguments
            if vision is None:return _text_response("Vision Intelligence is unavailable.")
            session=getattr(context.conversation_context,"session",None);metadata=getattr(session,"metadata",{}) or {}
            local_only=bool(metadata.get("local_only") or metadata.get("execution_policy")=="local_only" or vision.local_only)
            if name=="vision status":
                status=vision.status(local_only);providers=tuple(status["providers"]);provider_text=", ".join(f"{item.provider_id}:{item.model_id}" for item in providers) or "none"
                return _text_response(f"Vision status: {'ready' if status['available'] else status['availability_status']} provider={status['provider']} model={status['configured_model']} ollama={'ready' if status['ollama_available'] else 'unavailable'} local_only={'on' if local_only else 'off'} providers={provider_text} raw_image_persistence=off audit_entries={status['audit_events']} max_image_size={status['max_image_size']}.",enabled=status["enabled"],available=status["available"],local_only=local_only,privacy_mode=status["privacy_mode"],provider=status["provider"],configured_model=status["configured_model"],ollama_available=status["ollama_available"],model_available=status["model_available"],availability_status=status["availability_status"],provider_models=tuple((item.provider_id,item.model_id) for item in providers),raw_image_persistence=False,max_image_size=status["max_image_size"])
            if name=="vision models":
                models=vision.models();installed=", ".join(models["installed_models"]) or "none";capable=", ".join(models["vision_models"]) or "none"
                return _text_response(f"Vision models: provider={models['provider']} configured={models['configured_model']} ollama={'ready' if models['ollama_available'] else 'unavailable'} installed={installed} vision_capable={capable} status={models['availability_status']}. JARVIS never downloads models automatically.",**models)
            if name in {"vision analyze","vision describe"}:
                if not args:return _text_response(f"Provide an allowed image path: {name} <image_path>.")
                result=vision.analyze(args[0],local_only=local_only)
            elif name=="vision ask":
                if len(args)<2:return _text_response("Provide an image path and question: vision ask <image_path> <question>.")
                result=vision.analyze(args[0]," ".join(args[1:]),local_only=local_only)
            elif name=="vision audit":
                events=vision.audit_events()
                if not events:return _text_response("Vision audit: no events. Image content, base64 data, and full paths are never retained.",audit_events=())
                summary="; ".join(f"{event.action}:{event.status}:{event.image_name or 'none'}:{event.provider_id or 'none'}:{event.model_id or 'none'}" for event in events[-10:])
                return _text_response(f"Vision audit ({len(events)} bounded metadata events): {summary}. Image content and prompts are not retained.",audit_events=tuple(events[-10:]))
            elif name=="vision cleanup":
                cleanup=vision.cleanup()
                return _text_response(f"Vision cleanup complete: removed={cleanup['removed']} remaining={cleanup['remaining']} failed={cleanup['failed']}. User images were not changed.",**cleanup)
            else:result=None
            if result is not None:
                if result.status.value=="completed":return _text_response(result.content,vision_status=result.status.value,provider_id=result.provider_id,model_id=result.model_id,request_id=result.request_id,image_metadata=dict(result.metadata),warnings=result.warnings,latency_ms=result.latency_ms)
                guidance=" Start Ollama and install/configure a local vision-capable model such as llava; JARVIS will not download it automatically." if result.status.value=="unavailable" else ""
                detail=(result.error or "analysis did not complete").rstrip(".")
                return _text_response(f"Vision {result.status.value}: {detail}.{guidance}",vision_status=result.status.value,availability_status=result.availability_status,request_id=result.request_id,image_metadata=dict(result.metadata))
        if name.startswith("image "):
            image = _image_generation_manager(context); args = context.arguments
            if image is None:
                return _text_response("Image generation workflow is unavailable.")
            if name == "image help":
                return _text_response(
                    "Image commands: image status, image providers, image plan <prompt>, "
                    "image generate <prompt> [--dry-run], image safety <prompt>, image history, image show <job_id>."
                )
            if name == "image status":
                status = image.status()
                return _text_response(
                    "Image status: "
                    f"enabled={'yes' if status['enabled'] else 'no'} "
                    f"local_only={'on' if status['local_only'] else 'off'} "
                    f"provider={status['default_provider']} "
                    f"provider_status={status['provider_status']} "
                    f"overwrite={'on' if status['allow_overwrite'] else 'off'} "
                    f"metadata={'on' if status['save_metadata'] else 'off'} "
                    f"output={status['output_policy']}.",
                    **status,
                )
            if name == "image providers":
                providers = image.list_providers()
                summary = "; ".join(
                    f"{item['provider_name']}:{item['status']}:{item['model'] or 'no-model'}"
                    for item in providers
                ) or "none"
                return _text_response(f"Image providers: {summary}.", providers=tuple(providers))
            if name == "image history":
                jobs = image.history()
                text = "; ".join(
                    f"{item['job_id']}:{item['status']}:{item['provider']}:{item['prompt_preview']}"
                    for item in jobs
                ) or "none"
                return _text_response(f"Image history ({len(jobs)}): {text}.", jobs=tuple(jobs))
            if name == "image show":
                if not args:
                    return _text_response("Usage: image show <image_job_id>")
                job = image.show(args[0])
                if job is None:
                    return _text_response("Image job not found.")
                return _text_response(
                    f"Image job {job['job_id']}: status={job['status']} provider={job['provider']} "
                    f"dry_run={'yes' if job['dry_run'] else 'no'} outputs={', '.join(job['output_paths']) or 'none'} "
                    f"prompt={job['prompt_preview']}.",
                    **job,
                )
            if name in {"image plan", "image safety", "image generate"}:
                if not args:
                    usage = "image generate <prompt>" if name == "image generate" else f"{name} <prompt>"
                    return _text_response(f"Usage: {usage}")
                prompt = " ".join(args)
                if name == "image safety":
                    safety = image.evaluate_safety(prompt)
                    alternative = f" Alternative: {safety.safe_alternative}" if safety.safe_alternative else ""
                    return _text_response(
                        f"Image safety: allowed={'yes' if safety.allowed else 'no'} category={safety.category} severity={safety.severity}. {safety.reason}{alternative}",
                        allowed=safety.allowed,
                        category=safety.category,
                        severity=safety.severity,
                        reason=safety.reason,
                        safe_alternative=safety.safe_alternative,
                    )
                dry_run = bool(context.flags.get("dry-run", False)) or name == "image plan"
                result = image.generate(prompt, dry_run=dry_run) if name == "image generate" else image.plan(prompt)
                if result.status.value == "completed":
                    outputs = ", ".join(result.output_paths) or "none"
                    return _text_response(
                        f"Image generate completed: job={result.job_id} provider={result.provider} outputs={outputs}.",
                        job_id=result.job_id,
                        provider=result.provider,
                        output_paths=result.output_paths,
                        metadata_path=result.metadata_path,
                    )
                return _text_response(
                    f"Image {name.split()[1]} {result.status.value}: {result.message}",
                    job_id=result.job_id,
                    provider=result.provider,
                    status=result.status.value,
                    prompt_preview=result.prompt_preview,
                    warnings=result.warnings,
                    error=result.error,
                    metadata=result.metadata,
                )
        if name.startswith("video "):
            video = _video_editing_manager(context); args = context.arguments
            if video is None:
                return _text_response("Video editing workflow is unavailable.")
            if name == "video help":
                return _text_response(
                    "Video commands: video status, video providers, video plan <prompt>, video safety <prompt>, video history, video show <plan_id>."
                )
            if name == "video status":
                status = video.status()
                return _text_response(
                    "Video status: "
                    f"enabled={'yes' if status['enabled'] else 'no'} "
                    f"local_only={'on' if status['local_only'] else 'off'} "
                    f"provider={status['default_provider']} "
                    f"provider_status={status['provider_status']} "
                    f"metadata={'on' if status['save_metadata'] else 'off'} "
                    f"output={status['output_policy']}.",
                    **status,
                )
            if name == "video providers":
                providers = video.list_providers()
                summary = "; ".join(
                    f"{item['provider_name']}:{item['status']}:{item['model'] or 'no-model'}"
                    for item in providers
                ) or "none"
                return _text_response(f"Video providers: {summary}.", providers=tuple(providers))
            if name == "video history":
                plans = video.history()
                text = "; ".join(
                    f"{item['plan_id']}:{item['status']}:{item['provider']}:{item['prompt_preview']}"
                    for item in plans
                ) or "none"
                return _text_response(f"Video history ({len(plans)}): {text}.", jobs=tuple(plans))
            if name == "video show":
                if not args:
                    return _text_response("Usage: video show <video_plan_id>")
                plan = video.show(args[0])
                if plan is None:
                    return _text_response("Video plan not found.")
                return _text_response(
                    f"Video plan {plan['plan_id']}: status={plan['status']} provider={plan['provider']} "
                    f"dry_run={'yes' if plan['dry_run'] else 'no'} steps={len(plan['plan_steps'])} "
                    f"deliverables={', '.join(plan['deliverables']) or 'none'} prompt={plan['prompt_preview']}.",
                    **plan,
                )
            if name in {"video plan", "video safety"}:
                if not args:
                    return _text_response(f"Usage: {name} <prompt>")
                prompt = " ".join(args)
                if name == "video safety":
                    safety = video.evaluate_safety(prompt)
                    alternative = f" Alternative: {safety.safe_alternative}" if safety.safe_alternative else ""
                    return _text_response(
                        f"Video safety: allowed={'yes' if safety.allowed else 'no'} category={safety.category} severity={safety.severity}. {safety.reason}{alternative}",
                        allowed=safety.allowed,
                        category=safety.category,
                        severity=safety.severity,
                        reason=safety.reason,
                        safe_alternative=safety.safe_alternative,
                    )
                result = video.plan(prompt, dry_run=True)
                if result.status.value == "planned":
                    return _text_response(
                        f"Video plan prepared: plan={result.plan_id} provider={result.provider} steps={len(result.plan_steps)} deliverables={len(result.deliverables)}.",
                        plan_id=result.plan_id,
                        provider=result.provider,
                        plan_steps=result.plan_steps,
                        deliverables=result.deliverables,
                        metadata_path=result.metadata_path,
                        prompt_preview=result.prompt_preview,
                        dry_run=result.dry_run,
                        warnings=result.warnings,
                        error=result.error,
                    )
                if result.status.value == "blocked":
                    return _text_response(
                        f"Video planning blocked: {result.message}",
                        plan_id=result.plan_id,
                        provider=result.provider,
                        safety_status="blocked",
                        warnings=result.warnings,
                        error=result.error,
                        dry_run=result.dry_run,
                    )
                if result.status.value == "disabled":
                    return _text_response("Video editing is disabled in local configuration.")
                return _text_response(f"Video planning unavailable: {result.message}", plan_id=result.plan_id, provider=result.provider, error=result.error)
        if name.startswith("sync "):
            sync = _sync_manager(context); args = context.arguments
            if sync is None:
                return _text_response("Sync Intelligence is unavailable. Local JARVIS remains operational.")
            if name == "sync status":
                state = sync.status()
                return _text_response(
                    "Sync status: "
                    f"mode={state['mode']} enabled={'yes' if state['enabled'] else 'no'} "
                    f"adapter={state['adapter']} remote={'ready' if state['remote_available'] else 'unavailable'} "
                    f"queued={state['queue_count']} failed={state['failed_count']} conflicts={state['conflict_count']} "
                    f"last_success={state['last_successful_sync'] or 'never'} policy=allowlisted-summaries-only "
                    "deployment=status-only-not-sync-backend.",
                    **state,
                )
            if name == "sync on":
                result = sync.enable_manual(); return _text_response(result.message, sync_status=result.status.value)
            if name == "sync off":
                result = sync.disable(); return _text_response(result.message, sync_status=result.status.value)
            if name in {"sync queue", "sync queue summary"}:
                summary = sync.summary()
                if name == "sync queue summary":
                    return _text_response("Sync queue summary: " + " ".join(f"{key}={value}" for key, value in summary.items()), **summary)
                items = sync.list_items()
                text = ", ".join(f"{item.sync_item_id}:{item.item_type}:{item.status}" for item in items[-20:]) or "empty"
                return _text_response(f"Sync queue ({len(items)}): {text}", **summary)
            if name == "sync add":
                if not args:
                    return _text_response("Usage: sync add <approved_type> [safe JSON]. Example: sync add project_status")
                item_type = args[0]
                if item_type == "project_status" and len(args) == 1:
                    payload = _safe_project_snapshot()
                    if payload is None:
                        return _text_response("Project status snapshot is unavailable.")
                else:
                    if len(args) < 2:
                        return _text_response("A small allowlisted JSON object is required for this item type.")
                    try:
                        payload = json.loads(" ".join(args[1:]))
                    except json.JSONDecodeError:
                        return _text_response("Sync item rejected: payload must be valid JSON.")
                result = sync.enqueue(item_type, payload)
                return _text_response(f"Sync add {result.status.value}: {result.message}" + (f" id={result.sync_item_id}" if result.sync_item_id else ""), sync_status=result.status.value, sync_item_id=result.sync_item_id, error_code=result.error_code)
            if name == "sync inspect":
                if not args: return _text_response("Usage: sync inspect <sync_item_id>")
                item = sync.inspect(args[0])
                if item is None: return _text_response("Sync item was not found.")
                return _text_response(
                    f"Sync item: id={item.sync_item_id} type={item.item_type} status={item.status} attempts={item.attempt_count}/{item.maximum_attempts} payload={json.dumps(item.sanitized_payload, sort_keys=True)}",
                    sync_item_id=item.sync_item_id, item_type=item.item_type, status=item.status,
                )
            if name in {"sync cancel", "sync retry"}:
                if not args: return _text_response(f"Usage: {name} <sync_item_id>")
                result = sync.cancel(args[0]) if name == "sync cancel" else sync.retry(args[0])
                return _text_response(result.message, sync_status=result.status.value, sync_item_id=result.sync_item_id, error_code=result.error_code)
            if name == "sync cleanup":
                result = sync.cleanup(); return _text_response(f"Sync cleanup: removed={result['removed']} remaining={result['remaining']} audit_events={result['audit_events']}.", **result)
            if name == "sync run":
                result = sync.run()
                message = result.results[0].message if result.results else result.status.value
                return _text_response(f"Sync run {result.status.value}: {message} processed={result.processed} synced={result.synced} failed={result.failed} conflicts={result.conflicts}.", sync_status=result.status.value, processed=result.processed, synced=result.synced, failed=result.failed, conflicts=result.conflicts)
            if name == "sync conflicts":
                conflicts = sync.conflicts()
                text = ", ".join(f"{item.conflict_id}:{item.sync_item_id}:{item.status}" for item in conflicts[-20:]) or "none"
                return _text_response(f"Sync conflicts ({len(conflicts)}): {text}", conflict_count=len(conflicts))
        if name.startswith("web "):
            web = _web_manager(context); args = context.arguments
            conversation = context.conversation_context
            request_id = getattr(getattr(conversation, "session", None), "request_id", None)
            if web is None:
                return _text_response("Web Automation is unavailable. No browser action was performed.")
            if name == "web status":
                state = web.status()
                return _text_response(
                    "Web Automation: "
                    f"mode={state['mode']} enabled={'yes' if state['enabled'] else 'no'} "
                    f"adapter={state['adapter_id']} available={'yes' if state['adapter_available'] else 'no'} "
                    f"network_inspection={'ready' if state['network_inspection_enabled'] else 'unavailable'} "
                    f"read_only=yes interactive_actions=blocked sensitive_actions=blocked page_storage=off screenshots=off.",
                    **state,
                )
            if name == "web policy":
                return _text_response(
                    "Web policy: HTTP(S) read-only metadata actions may proceed after URL validation when a governed adapter is configured. "
                    "Local/private targets and unsafe topics are blocked by default. Click, type, submit, download, upload, login, purchase, message, delete, and account changes are blocked. "
                    "CAPTCHA, paywall, and access-control bypass are never permitted in this foundation.",
                    read_only_actions=("open_url", "get_page_title", "get_current_url", "snapshot_page", "close_session"),
                    sensitive_actions="blocked",
                )
            if name == "web session":
                sessions = tuple(web.sessions.values())
                text = ", ".join(f"{item.session_id}:{item.status}:{item.current_domain or 'unknown'}" for item in sessions) or "none"
                return _text_response(f"Web sessions ({len(sessions)}): {text}", active_sessions=len(sessions))
            if name == "web audit":
                events = web.audit_events()
                text = ", ".join(f"{item.action_type}:{item.status}:{item.safe_domain or 'none'}" for item in events[-20:]) or "none"
                return _text_response(f"Web audit ({len(events)}): {text}", audit_count=len(events))
            if name == "web open":
                if not args: return _text_response("Usage: web open <https_url>")
                result = web.open_url(args[0], request_id)
            elif name == "web title": result = web.title(request_id=request_id)
            elif name == "web url": result = web.current_url(request_id=request_id)
            elif name == "web snapshot": result = web.snapshot(request_id=request_id)
            elif name == "web close": result = web.close(request_id=request_id)
            else: result = None
            if result is not None:
                details = result.message
                if result.title: details += f" title={result.title}"
                safe_url = web.safe_url_for_display(result.current_url)
                if safe_url: details += f" url={safe_url}"
                if result.snapshot:
                    snapshot = result.snapshot
                    details += (
                        f" domain={snapshot.domain or 'unknown'} status={snapshot.status_code or 'unknown'} "
                        f"content_type={snapshot.content_type or 'unknown'} redirects={snapshot.redirect_count} "
                        f"bytes={snapshot.byte_count} content_stored=no screenshot_stored=no"
                    )
                    if snapshot.description:
                        details += f" description={snapshot.description[:300]}"
                    if snapshot.text_preview:
                        details += f" preview={snapshot.text_preview[:500]}"
                return _text_response(
                    f"Web {result.action_type.value} {result.status.value}: {details}",
                    web_status=result.status.value, action_type=result.action_type.value,
                    session_id=result.session_id, safe_domain=result.safe_domain,
                    error_code=result.error_code, approval_required=result.approval_required,
                )
        if name.startswith("mobile "):
            mobile = _mobile_manager(context); args = context.arguments
            conversation = context.conversation_context
            request_id = getattr(getattr(conversation, "session", None), "request_id", None)
            if mobile is None:
                return _text_response("Mobile Automation is unavailable. No device was accessed.")
            if name == "mobile status":
                state = mobile.status()
                return _text_response(
                    "Mobile Automation: "
                    f"status={state['status']} mode={state['mode']} adapter={state['adapter_id']} "
                    f"available={'yes' if state['adapter_available'] else 'no'} real_phone_adapter=no "
                    "live_control=off private_data_access=blocked sensitive_actions=blocked.", **state)
            if name == "mobile policy":
                return _text_response("Mobile policy: status, setup guidance, capability summaries, connection planning, audit reading, and session closure are allowed. Private phone data, communications, sensors, device input, installs, settings, purchases, login/unlock, and background monitoring are blocked.", sensitive_actions="blocked")
            if name == "mobile capabilities":
                result = mobile.capabilities(request_id)
                return _text_response(f"Mobile capabilities {result.status.value}: current=status,policy,capabilities,setup,connection_plan,audit,close; future_blocked=private_data,communications,camera,microphone,location,tap,type,swipe,install,settings,purchase,login,unlock,background_monitor.", error_code=result.error_code)
            if name == "mobile setup":
                result = mobile.setup(request_id)
                return _text_response(f"Mobile setup {result.status.value}: {result.message}", error_code=result.error_code)
            if name == "mobile plan":
                if not args: return _text_response("Usage: mobile plan <safe_mobile_workflow>")
                result = mobile.plan(" ".join(args), request_id)
                return _text_response(f"Mobile plan {result.status.value}: {result.message}", error_code=result.error_code, approval_required=result.approval_required)
            if name == "mobile audit":
                events = mobile.audit_events()
                text = ", ".join(f"{item.action_type}:{item.status}:{item.policy_decision}" for item in events[-20:]) or "none"
                return _text_response(f"Mobile audit ({len(events)}): {text}", audit_count=len(events))
            if name == "mobile close":
                result = mobile.close(request_id)
                return _text_response(f"Mobile close {result.status.value}: {result.message}", error_code=result.error_code)
            if name == "mobile devices":
                devices = mobile.device_summaries()
                return _text_response(f"Mobile devices ({len(devices)}): none; no phone identifiers were read.", device_count=len(devices))
            if name == "mobile session":
                return _text_response(f"Mobile sessions ({len(mobile.sessions)}): planning-only; no device connection.", session_count=len(mobile.sessions))
        if name in {"provider show","provider capabilities","provider policy","provider validate","provider history","integration status","integration policy","credential status","credential required"}:
            return _text_response(render_external_command(name, context.arguments, _external_integrations(context)))
        if name == "provider health" and context.arguments and _external_integrations(context).registry.get(context.arguments[0]):
            return _text_response(render_external_command(name, context.arguments, _external_integrations(context)))
        if name in {"providers", "provider list", "provider status", "provider health"}:
            provider_manager = _provider_manager(context)
            if provider_manager is None:
                if name == "provider list":
                    return _text_response(render_external_command("provider list", (), _external_integrations(context)))
                return _text_response(f"{name} unavailable: Provider Manager is not initialized.")
            records = provider_manager.registry.all()
            conversation = context.conversation_context
            session = getattr(conversation, "session", None)
            metadata = getattr(session, "metadata", {}) or {}
            policy = _cloud_policy(session)
            preferred_provider = metadata.get("provider_preference") or metadata.get("local_provider") or metadata.get("cloud_provider")
            preferred_model = metadata.get("model_preference") or metadata.get("local_model") or metadata.get("cloud_model")
            if name == "provider status":
                return _text_response(
                    "Provider status: "
                    f"mode={policy} "
                    f"provider={preferred_provider or 'automatic'} "
                    f"model={preferred_model or 'automatic'} "
                    f"configured={len(records)}",
                    execution_policy=policy,
                    provider=preferred_provider,
                    model=preferred_model,
                    configured=len(records),
                )
            details = []
            healthy = 0
            for record in records:
                provider = getattr(record, "provider", None)
                available = bool(provider and getattr(provider.health, "available", False))
                healthy += int(available)
                location = "local" if _is_local_provider(record) else "cloud"
                details.append(f"{record.config.provider_id}={location}/{'ready' if available else 'unavailable'}")
            label = "Provider health" if name == "provider health" else "Providers"
            suffix = " | " + render_external_command("provider list", (), _external_integrations(context)) if name == "provider list" else ""
            return _text_response(f"{label}: " + (", ".join(details) if details else "none configured") + suffix, configured=len(records), healthy=healthy)
        if name in {"local", "local status", "local providers", "local models", "local refresh", "local use", "local test", "local explain-selection", "local only on", "local only off", "cloud", "cloud status", "cloud providers", "cloud models", "cloud refresh", "cloud use", "cloud test", "cloud explain-selection", "cloud only on", "cloud only off", "provider enable", "provider disable", "provider test"}:
            provider_manager = _provider_manager(context)
            if provider_manager is None:
                return _text_response("Local AI is not available.")
            local_records = tuple(
                record for record in provider_manager.registry.all()
                if _is_local_provider(record)
            )
            if name in {"local", "local status"}:
                health = provider_manager.health_check()
                stats = provider_manager.statistics()
                models = sum(len(record.provider.list_models()) for record in local_records if getattr(record, "provider", None) is not None)
                return _text_response(
                    f"Local AI status: configured={len(local_records)} available={stats.healthy_providers} models={models}",
                    configured=len(local_records),
                    healthy=stats.healthy_providers,
                    models=models,
                    health=health,
                )
            if name == "local providers":
                if not local_records:
                    return _text_response("No local providers are configured.")
                return _text_response("Local providers: " + ", ".join(record.config.provider_id for record in local_records))
            if name == "local models":
                models: list[str] = []
                for record in local_records:
                    provider = getattr(record, "provider", None)
                    if provider is None:
                        continue
                    for model in provider.list_models():
                        models.append(f"{record.config.provider_id}:{model.model_id}")
                return _text_response("Local models: " + (", ".join(models) if models else "none discovered"))
            if name == "local refresh":
                for record in local_records:
                    provider = getattr(record, "provider", None)
                    if provider is not None and hasattr(provider, "refresh_inventory"):
                        provider.refresh_inventory()
                return _text_response("Local model inventory refreshed.")
            if name == "local use":
                if not context.arguments:
                    return _text_response("Please provide a local model id.")
                model_id = context.arguments[0]
                selected = None
                for record in local_records:
                    provider = getattr(record, "provider", None)
                    if provider is None:
                        continue
                    for model in provider.list_models():
                        if model.model_id == model_id:
                            selected = record
                            break
                    if selected is not None:
                        break
                if selected is None:
                    return _text_response(f"Local model not found: {model_id}")
                conversation = context.conversation_context
                if conversation is not None:
                    conversation.session.metadata["local_model"] = model_id
                    conversation.session.metadata["local_provider"] = selected.config.provider_id
                    conversation.session.metadata["model_preference"] = model_id
                    conversation.session.metadata["provider_preference"] = selected.config.provider_id
                return _text_response(
                    f"Local model selected: {selected.config.provider_id}:{model_id}",
                    provider=selected.config.provider_id,
                    model=model_id,
                )
            if name == "local test":
                provider_router = getattr(provider_manager, "router", None)
                if provider_router is None:
                    return _text_response("Local AI is not available.")
                conversation = context.conversation_context
                session_metadata = conversation.session.metadata if conversation is not None else {}
                selected_provider = session_metadata.get("provider_preference") or session_metadata.get("local_provider")
                selected_model = session_metadata.get("model_preference") or session_metadata.get("local_model")
                candidate = next(
                    (
                        record
                        for record in local_records
                        if getattr(record, "provider", None) is not None
                        and record.provider.list_models()
                        and (not selected_provider or record.config.provider_id == selected_provider)
                    ),
                    None,
                )
                if candidate is None:
                    candidate = next((record for record in local_records if getattr(record, "provider", None) is not None and record.provider.list_models()), None)
                if candidate is None:
                    return _text_response("No usable local model is available.")
                available_models = {model.model_id for model in candidate.provider.list_models()}
                model_id = selected_model if selected_model in available_models else candidate.provider.list_models()[0].model_id
                try:
                    result = asyncio.run(
                        provider_router.execute_with_failover(
                            ProviderRequest(
                                prompt="Reply with ok.",
                                goal="Test local AI",
                                model=model_id,
                                request_id="command-local-test",
                                local_only=True,
                                # A cold local model can need longer than the interactive
                                # default while it is loaded into Ollama.
                                timeout_seconds=120,
                            )
                        )
                    )
                except Exception as exc:  # pragma: no cover - defensive command surface
                    return _text_response(f"Local model test failed: {exc}")
                if result.error:
                    return _text_response(f"Local model test failed: {result.error}", provider=result.provider_id, model=result.model, retryable=result.retryable)
                return _text_response(
                    "Local model test succeeded.",
                    provider=result.provider_id,
                    model=result.model,
                    content=result.content,
                )
            if name == "local explain-selection":
                return _text_response("Local model selection is based on locality, health, availability, and capability match.")
            if name == "local only on":
                conversation = context.conversation_context
                if conversation is not None:
                    conversation.session.metadata["local_only"] = True
                    conversation.session.metadata["cloud_only"] = False
                    conversation.session.metadata["execution_policy"] = "local_only"
                return _text_response("Local-only mode enabled.")
            if name == "local only off":
                conversation = context.conversation_context
                if conversation is not None:
                    conversation.session.metadata["local_only"] = False
                    conversation.session.metadata["execution_policy"] = "automatic"
                return _text_response("Local-only mode disabled.")
            if name in {"cloud", "cloud status"}:
                health = provider_manager.health_check()
                stats = provider_manager.statistics()
                cloud_records = tuple(
                    record for record in provider_manager.registry.all()
                    if not (
                        getattr(getattr(record, "config", None), "local_only", False)
                        or str(getattr(getattr(record, "config", None), "kind", "")).lower() in {"local", "ollama", "lm_studio"}
                    )
                )
                models = sum(len(record.provider.list_models()) for record in cloud_records if getattr(record, "provider", None) is not None)
                return _text_response(
                    f"Cloud AI status: configured={len(cloud_records)} available={stats.healthy_providers} models={models}",
                    configured=len(cloud_records),
                    healthy=stats.healthy_providers,
                    models=models,
                    health=health,
                )
            if name == "cloud providers":
                cloud_records = tuple(
                    record for record in provider_manager.registry.all()
                    if not (
                        getattr(getattr(record, "config", None), "local_only", False)
                        or str(getattr(getattr(record, "config", None), "kind", "")).lower() in {"local", "ollama", "lm_studio"}
                    )
                )
                if not cloud_records:
                    return _text_response("No cloud providers are configured.")
                return _text_response("Cloud providers: " + ", ".join(record.config.provider_id for record in cloud_records))
            if name == "cloud models":
                models: list[str] = []
                for record in provider_manager.registry.all():
                    if getattr(getattr(record, "config", None), "local_only", False):
                        continue
                    if str(getattr(getattr(record, "config", None), "kind", "")).lower() in {"local", "ollama", "lm_studio"}:
                        continue
                    provider = getattr(record, "provider", None)
                    if provider is None:
                        continue
                    for model in provider.list_models():
                        models.append(f"{record.config.provider_id}:{model.model_id}")
                return _text_response("Cloud models: " + (", ".join(models) if models else "none discovered"))
            if name == "cloud refresh":
                for record in provider_manager.registry.all():
                    if getattr(getattr(record, "config", None), "local_only", False):
                        continue
                    provider = getattr(record, "provider", None)
                    if provider is not None and hasattr(provider, "refresh_inventory"):
                        provider.refresh_inventory()
                return _text_response("Cloud model inventory refreshed.")
            if name == "cloud use":
                if not context.arguments:
                    return _text_response("Please provide a cloud provider or model id.")
                selected_provider = None
                selected_model = None
                choice = context.arguments[0]
                for record in provider_manager.registry.all():
                    if getattr(getattr(record, "config", None), "local_only", False):
                        continue
                    provider = getattr(record, "provider", None)
                    if provider is None:
                        continue
                    if record.config.provider_id == choice:
                        selected_provider = record
                        selected_model = context.arguments[1] if len(context.arguments) > 1 else record.config.preferred_model or record.config.default_model
                        break
                    for model in provider.list_models():
                        if model.model_id == choice:
                            selected_provider = record
                            selected_model = model.model_id
                            break
                    if selected_provider is not None:
                        break
                if selected_provider is None:
                    return _text_response(f"Cloud provider or model not found: {choice}")
                conversation = context.conversation_context
                if conversation is not None:
                    conversation.session.metadata["provider_preference"] = selected_provider.config.provider_id
                    if selected_model:
                        conversation.session.metadata["model_preference"] = selected_model
                    conversation.session.metadata["execution_policy"] = "prefer_cloud"
                label = selected_provider.config.provider_id if not selected_model else f"{selected_provider.config.provider_id}:{selected_model}"
                return _text_response(f"Cloud selection updated: {label}", provider=selected_provider.config.provider_id, model=selected_model)
            if name == "cloud test":
                provider_router = getattr(provider_manager, "router", None)
                if provider_router is None:
                    return _text_response("Cloud AI is not available.")
                conversation = context.conversation_context
                policy = _cloud_policy(getattr(conversation, "session", None), "prefer_cloud")
                preferred_provider = None
                preferred_model = None
                if conversation is not None:
                    metadata = getattr(conversation.session, "metadata", {}) or {}
                    preferred_provider = metadata.get("provider_preference") or metadata.get("cloud_provider")
                    preferred_model = metadata.get("model_preference") or metadata.get("cloud_model")
                candidates = tuple(
                    record for record in provider_manager.registry.all()
                    if not (
                        getattr(getattr(record, "config", None), "local_only", False)
                        or str(getattr(getattr(record, "config", None), "kind", "")).lower() in {"local", "ollama", "lm_studio"}
                    )
                )
                candidate = next((record for record in candidates if getattr(record, "provider", None) is not None), None)
                if candidate is None:
                    return _text_response("No usable cloud provider is available.")
                candidate_models = candidate.provider.list_models() if getattr(candidate, "provider", None) is not None else ()
                model_id = preferred_model or (candidate_models[0].model_id if candidate_models else candidate.config.preferred_model or candidate.config.default_model or "cloud-mini")
                try:
                    result = asyncio.run(
                        provider_router.execute_with_failover(
                            ProviderRequest(
                                prompt="Reply with ok.",
                                goal="Test cloud AI",
                                model=model_id or None,
                                request_id="command-cloud-test",
                                preferred_provider=preferred_provider or candidate.config.provider_id,
                                metadata={"execution_policy": policy},
                            )
                        )
                    )
                except Exception as exc:  # pragma: no cover - defensive command surface
                    return _text_response(f"Cloud model test failed: {exc}")
                if result.error:
                    return _text_response(f"Cloud model test failed: {result.error}", provider=result.provider_id, model=result.model, retryable=result.retryable)
                return _text_response(
                    "Cloud model test succeeded.",
                    provider=result.provider_id,
                    model=result.model,
                    content=result.content,
                )
            if name == "cloud explain-selection":
                return _text_response("Cloud model selection is based on policy, credentials, health, availability, and capability match.")
            if name == "cloud only on":
                conversation = context.conversation_context
                if conversation is not None:
                    conversation.session.metadata["cloud_only"] = True
                    conversation.session.metadata["execution_policy"] = "cloud_only"
                return _text_response("Cloud-only mode enabled.")
            if name == "cloud only off":
                conversation = context.conversation_context
                if conversation is not None:
                    conversation.session.metadata["cloud_only"] = False
                    conversation.session.metadata["execution_policy"] = "automatic"
                return _text_response("Cloud-only mode disabled.")
            if name == "provider enable":
                if not context.arguments:
                    return _text_response("Please provide a provider id to enable.")
                try:
                    provider_manager.enable_provider(context.arguments[0])
                    return _text_response(f"Provider enabled: {context.arguments[0]}")
                except Exception as exc:
                    return _text_response(f"Unable to enable provider: {exc}")
            if name == "provider disable":
                if not context.arguments:
                    return _text_response("Please provide a provider id to disable.")
                try:
                    provider_manager.disable_provider(context.arguments[0])
                    return _text_response(f"Provider disabled: {context.arguments[0]}")
                except Exception as exc:
                    return _text_response(f"Unable to disable provider: {exc}")
            if name == "provider test":
                if not context.arguments:
                    return _text_response("Please provide a provider id to test.")
                provider_id = context.arguments[0]
                try:
                    record = provider_manager.registry.require(provider_id)
                except Exception as exc:
                    return _text_response(f"Provider not found: {exc}")
                provider = getattr(record, "provider", None)
                if provider is None:
                    return _text_response("Provider is not initialized.")
                health = provider.health_check()
                models = provider.list_models()
                return _text_response(
                    f"Provider test completed for {provider_id}.",
                    provider=provider_id,
                    healthy=health.available,
                    models=len(models),
                )
        if name in {"profile", "profile show", "profile list"}:
            personal = _personal_manager(context)
            if personal is None:
                return _text_response("Personal intelligence is not available.")
            return _text_response(personal.summarize(" ".join(context.arguments) if context.arguments else None))
        if name == "profile explain":
            personal = _personal_manager(context)
            if personal is None:
                return _text_response("Personal intelligence is not available.")
            item_id = context.arguments[0] if context.arguments else ""
            explanation = personal.explain(item_id)
            return _text_response(str(explanation) if explanation is not None else "Personal item not found.")
        if name == "profile update":
            personal = _personal_manager(context)
            if personal is None:
                return _text_response("Personal intelligence is not available.")
            if len(context.arguments) < 2:
                return _text_response("Usage: profile update <item-id> <new-value>")
            updated = personal.update(context.arguments[0], value=" ".join(context.arguments[1:]))
            return _text_response("Personal item updated." if updated is not None else "Personal item not found.")
        if name == "profile forget":
            personal = _personal_manager(context)
            if personal is None:
                return _text_response("Personal intelligence is not available.")
            item_id = context.arguments[0] if context.arguments else ""
            return _text_response("Personal item forgotten." if personal.forget(item_id) else "Personal item not found.")
        if name == "profile confirm":
            personal = _personal_manager(context)
            if personal is None:
                return _text_response("Personal intelligence is not available.")
            item_id = context.arguments[0] if context.arguments else ""
            return _text_response("Personal item confirmed." if personal.confirm(item_id) is not None else "Personal item not found.")
        if name == "profile reject":
            personal = _personal_manager(context)
            if personal is None:
                return _text_response("Personal intelligence is not available.")
            item_id = context.arguments[0] if context.arguments else ""
            return _text_response("Personal item rejected." if personal.reject(item_id) is not None else "Personal item not found.")
        if name in {"context", "context show"}:
            context_manager = _context_manager(context)
            conversation = context.conversation_context
            if context_manager is None or conversation is None:
                return _text_response("Context intelligence is not available.")
            resolution = context_manager.describe_current_context(conversation.session)
            return _text_response(resolution.immediate_response or "There is no active context.")
        if name == "context recent":
            context_manager = _context_manager(context)
            conversation = context.conversation_context
            if context_manager is None or conversation is None:
                return _text_response("Context intelligence is not available.")
            recent = context_manager.list_recent_context(conversation.session)
            if not recent:
                return _text_response("There is no recent context history yet.")
            return _text_response("Recent context: " + "; ".join(f"{item.context_type}: {item.value}" for item in recent[:5]))
        if name == "context clear":
            context_manager = _context_manager(context)
            conversation = context.conversation_context
            if context_manager is None or conversation is None:
                return _text_response("Context intelligence is not available.")
            context_manager.clear_active_context(conversation.session)
            return _text_response("Active context cleared.")
        if name == "context pause":
            context_manager = _context_manager(context)
            conversation = context.conversation_context
            if context_manager is None or conversation is None:
                return _text_response("Context intelligence is not available.")
            suspended = context_manager.suspend_current_context(conversation.session)
            if suspended is None:
                return _text_response("There is no active context to pause.")
            return _text_response(f"Paused {suspended.context_type}: {suspended.value}.")
        if name in {"context resume", "context previous"}:
            context_manager = _context_manager(context)
            conversation = context.conversation_context
            if context_manager is None or conversation is None:
                return _text_response("Context intelligence is not available.")
            resolution = context_manager.resume_previous_context(conversation.session)
            return _text_response(resolution.immediate_response or "I could not restore a previous context.")
        if name == "objective show":
            context_manager = _context_manager(context)
            conversation = context.conversation_context
            if context_manager is None or conversation is None:
                return _text_response("Context intelligence is not available.")
            objective = context_manager.current_objective(conversation.session)
            if not objective:
                return _text_response("There is no active objective right now.")
            return _text_response(f"Current objective: {objective}")
        if name in {"goal", "goal show", "goal review", "goal progress", "goal next", "goal blockers", "goal evaluate", "goal conflicts", "goal align", "goal portfolio", "goal pause", "goal resume", "goal complete"}:
            goal_intel = _goal_manager(context)
            conversation = context.conversation_context
            if goal_intel is None or conversation is None:
                return _text_response("Goal intelligence is not available.")
            argument_text = " ".join(context.arguments).strip()
            if name == "goal":
                return _text_response(goal_intel.prepare_request("Show the current goal portfolio.", conversation.session).immediate_response)
            if name == "goal show":
                return _text_response(goal_intel.prepare_request("Show the active goal.", conversation.session).immediate_response)
            if name == "goal list":
                return _text_response(goal_intel.goal_portfolio().immediate_response)
            if name == "goal review":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                return _text_response(goal_intel.review_goal(goal).immediate_response if goal else "I could not find a goal to review.")
            if name == "goal progress":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                return _text_response(goal_intel.evaluate_progress(goal).immediate_response if goal else "I could not find a goal to evaluate.")
            if name == "goal next":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                return _text_response(goal_intel.recommend_next_step(goal).immediate_response if goal else "I could not find a goal to continue.")
            if name == "goal blockers":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                if goal is None:
                    return _text_response("I could not find a goal to inspect.")
                blockers = goal_intel.detect_blockers(goal)
                return _text_response("Goal blockers: " + (", ".join(blockers) if blockers else "none"))
            if name == "goal evaluate":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                return _text_response(goal_intel.evaluate_completion(goal).immediate_response if goal else "I could not find a goal to evaluate.")
            if name == "goal conflicts":
                goals = goal_intel.task_intelligence_manager.goal_manager.list_goals() if goal_intel.task_intelligence_manager else ()
                return _text_response(goal_intel.detect_conflicts(goals).immediate_response)
            if name == "goal align":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                if goal is None:
                    return _text_response("I could not find a goal to align.")
                return _text_response(goal_intel.decompose_goal(goal).immediate_response)
            if name == "goal portfolio":
                return _text_response(goal_intel.goal_portfolio().immediate_response)
            if name == "goal pause":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                return _text_response(goal_intel.pause_goal(goal.goal_id).immediate_response if goal else "I could not find a goal to pause.")
            if name == "goal resume":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                return _text_response(goal_intel.resume_goal(goal.goal_id).immediate_response if goal else "I could not find a goal to resume.")
            if name == "goal complete":
                goal = goal_intel.resolve_goal_reference(argument_text or "goal", conversation.session).goal
                return _text_response(goal_intel.evaluate_completion(goal).immediate_response if goal else "I could not find a goal to complete.")
        return _text_response(f"{name} command acknowledged.", command=name)

    return handler
