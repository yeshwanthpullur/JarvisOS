"""Built-in command registration for JARVIS OS."""

from __future__ import annotations

from commands.command_context import CommandContext
from commands.command_permissions import CommandPermission
from commands.command_registry import CommandRecord, CommandRegistry
from conversation.conversation_response import ConversationResponse


def _manager(context: CommandContext):
    if hasattr(context.conversation_context, "registry"):
        return context.conversation_context
    return getattr(context.conversation_context, "command_manager", None)


def _text_response(text: str, **metadata: object) -> ConversationResponse:
    return ConversationResponse(response=text, metadata=metadata)


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
        return _text_response(f"{name} command acknowledged.", command=name)

    return handler
