"""Built-in command registration for JARVIS OS."""

from __future__ import annotations

import asyncio

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
        ("plugins", "Show plugin summary", "plugin", (), CommandPermission.PLUGIN),
        ("plugin list", "List plugins", "plugin", (), CommandPermission.PLUGIN),
        ("plugin status", "Show plugin status", "plugin", (), CommandPermission.PLUGIN),
        ("agents", "Show agent summary", "agent", (), CommandPermission.AGENT),
        ("agent list", "List agents", "agent", (), CommandPermission.AGENT),
        ("agent status", "Show agent status", "agent", (), CommandPermission.AGENT),
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
        if name in {"local", "local status", "local providers", "local models", "local refresh", "local use", "local test", "local explain-selection", "local only on", "local only off"}:
            provider_manager = _provider_manager(context)
            if provider_manager is None:
                return _text_response("Local AI is not available.")
            local_records = tuple(
                record for record in provider_manager.registry.all()
                if getattr(getattr(record, "config", None), "local_only", False)
                or str(getattr(getattr(record, "config", None), "kind", "")).lower() in {"local", "ollama", "lm_studio"}
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
                return _text_response("Local-only mode enabled.")
            if name == "local only off":
                conversation = context.conversation_context
                if conversation is not None:
                    conversation.session.metadata["local_only"] = False
                return _text_response("Local-only mode disabled.")
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
