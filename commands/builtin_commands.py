"""Built-in command registration for JARVIS OS."""

from __future__ import annotations

import asyncio
import json

from commands.command_context import CommandContext
from commands.command_permissions import CommandPermission
from commands.command_registry import CommandRecord, CommandRegistry
from conversation.conversation_response import ConversationResponse
from providers import ProviderRequest


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


def _cloud_policy(session: object | None, default: str = "automatic") -> str:
    if session is None:
        return default
    metadata = getattr(session, "metadata", {}) or {}
    return str(metadata.get("execution_policy") or metadata.get("provider_policy") or default)


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
        ("voice stop", "Stop listening", "voice", (), CommandPermission.UTILITY),
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
        ("departments", "Show department summary", "department", (), CommandPermission.DEPARTMENT),
        ("department list", "List departments", "department", (), CommandPermission.DEPARTMENT),
        ("memory", "Show memory summary", "memory", (), CommandPermission.MEMORY),
        ("memory search", "Search memory architecture hook", "memory", (), CommandPermission.MEMORY),
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
        if name == "exit":
            return ConversationResponse(response="Shutting down JARVIS OS.", should_exit=True)
        if name == "clear":
            return ConversationResponse(response="", should_clear=True)
        if name == "history" and manager is not None:
            return _text_response(f"Command history: {len(manager.history.list_history())} entries")
        if name == "metrics" and manager is not None:
            return _text_response(f"Commands executed: {manager.metrics.commands_executed}")
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
                backend=voice.registry.get(voice.selected_output_backend)
                available=bool(backend and backend.available)
                return _text_response(
                    "Voice status: "
                    f"output={'on' if voice.output_enabled else 'off'} "
                    f"backend={voice.selected_output_backend} "
                    f"playback={'ready' if available else 'unavailable'} "
                    f"input={'on' if voice.input_enabled else 'off'} "
                    f"mode={voice.mode.value} privacy={voice.privacy_mode}",
                    output_enabled=voice.output_enabled,
                    backend=voice.selected_output_backend,
                    playback_ready=available,
                    input_enabled=voice.input_enabled,
                )
            if name=="voice on":voice.enabled=True;return _text_response("Voice enabled. Microphone capture remains disabled until explicitly activated.")
            if name=="voice off":voice.enabled=False;voice.input_enabled=False;voice.mode=type(voice.mode).OFF;voice.cancel();return _text_response("Voice disabled. Text mode remains active.")
            if name=="voice input":
                if args and args[0] in {"on","off"}:voice.input_enabled=args[0]=="on";return _text_response(f"Voice input {'enabled' if voice.input_enabled else 'disabled'}.")
                return _text_response(f"Voice input: {voice.input_enabled}")
            if name=="voice output":
                if args and args[0] in {"on","off"}:
                    if args[0]=="on":
                        backend=voice.registry.get(voice.selected_output_backend)
                        if backend is None or not backend.available:
                            voice.output_enabled=False
                            return _text_response(f"Voice output unavailable: {voice.selected_output_backend} is not ready.")
                        voice.output_enabled=True;voice.enabled=True
                        return _text_response(f"Voice output enabled through {voice.selected_output_backend}. Safe assistant replies will be spoken.")
                    voice.output_enabled=False
                    return _text_response("Voice output disabled. Replies will remain text-only.")
                return _text_response(f"Voice output: {voice.output_enabled}")
            if name=="voice say":
                if not args:return _text_response("Please provide text to speak.")
                try:r=voice.say(" ".join(args),parent_request_id="command-voice-say",playback=True)
                except ValueError as exc:return _text_response(f"Voice synthesis blocked: {exc}")
                if r.status.value != "completed":
                    return _text_response(f"Voice synthesis failed: {', '.join(r.errors) or r.status.value}",synthesis_id=r.synthesis_id,backend_id=r.backend_id,status=r.status.value)
                return _text_response(f"Voice synthesis completed through {r.backend_id} playback.",synthesis_id=r.synthesis_id,backend_id=r.backend_id,audio_reference=r.audio_reference)
            if name=="voice transcribe":
                if not args:return _text_response("Please provide an allowed WAV file path.")
                try:r=voice.transcribe_file(args[0])
                except ValueError as exc:return _text_response(f"Transcription rejected: {exc}")
                return _text_response("Offline speech recognition is unavailable on this machine." if r.status.value=="unavailable" else r.text,status=r.status.value)
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
            if name in {"voice stop","voice interrupt"}:return _text_response("Voice interruption requested." if voice.interrupt() else "No active voice operation.")
            if name=="voice cancel":voice.cancel();return _text_response("Voice session cancelled.")
            if name=="voice listen":
                if not voice.enabled or not voice.input_enabled:return _text_response("Voice input is disabled; no microphone was activated.")
                return _text_response("No available microphone capture adapter is configured.")
            if name=="voice session":
                sessions=tuple(voice.sessions.values());return _text_response(f"Voice session: {sessions[-1].voice_session_id}:{sessions[-1].state.value}" if sessions else "No voice session exists.")
            if name=="voice limits":return _text_response("Voice limits: "+", ".join(f"{k}={getattr(voice.limits,k)}" for k in voice.limits.__slots__))
            if name=="voice health":return _text_response("Voice health: "+json.dumps(voice.health(),default=str))
            if name=="voice device":return _text_response("Explicit device selection is unavailable until a matching capture/output adapter exposes device IDs.")
        if name in {"providers", "provider list", "provider status", "provider health"}:
            provider_manager = _provider_manager(context)
            if provider_manager is None:
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
            return _text_response(f"{label}: " + (", ".join(details) if details else "none configured"), configured=len(records), healthy=healthy)
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
                candidate = next((record for record in local_records if getattr(record, "provider", None) is not None and record.provider.list_models()), None)
                if candidate is None:
                    return _text_response("No usable local model is available.")
                model_id = candidate.provider.list_models()[0].model_id
                try:
                    result = asyncio.run(
                        provider_router.execute_with_failover(
                            ProviderRequest(
                                prompt="Reply with ok.",
                                goal="Test local AI",
                                model=model_id,
                                request_id="command-local-test",
                                local_only=True,
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
