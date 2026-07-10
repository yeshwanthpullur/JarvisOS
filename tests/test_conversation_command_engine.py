"""Tests for Conversation and Command engines."""

from __future__ import annotations

import unittest

from commands import CommandManager, CommandParser, CommandRecord, CommandRegistry
from commands.command_aliases import CommandAliases
from commands.command_context import CommandContext
from commands.command_dispatcher import CommandDispatcher
from commands.command_help import CommandHelp
from commands.command_history import CommandHistory
from commands.command_metrics import CommandMetrics
from commands.command_permissions import CommandPermission
from commands.command_validator import CommandValidator
from conversation import ConversationContext, ConversationManager, ConversationRequest, ConversationResponse, ConversationSession, ConversationState
from conversation.conversation_engine import ConversationEngine
from conversation.conversation_events import ConversationEvent, ConversationEventType
from conversation.conversation_history import ConversationHistory
from conversation.conversation_logger import ConversationLogger
from conversation.conversation_memory import ConversationMemory
from conversation.conversation_metrics import ConversationMetrics
from conversation.conversation_recovery import ConversationRecovery
from conversation.conversation_router import ConversationRouter
from conversation.conversation_summary import ConversationSummary
from conversation.conversation_validator import ConversationValidator
from jarvis import JarvisCore
from jarvis.execution_planner import ExecutionPlanner
from jarvis.request_pipeline import ContextBuilder, ExecutionHistory, ExecutionSummary, RequestBuilder
from jarvis.response_pipeline import ResponseComposer, ResponseFormatter, ResponseRenderer, ResponseValidator


class ConversationCommandTests(unittest.TestCase):
    """Conversation and command tests."""

    def test_parser_single_command(self) -> None:
        self.assertEqual(CommandParser().parse("help").name, "help")

    def test_parser_slash_command(self) -> None:
        self.assertEqual(CommandParser().parse("/help").name, "help")

    def test_parser_arguments(self) -> None:
        parsed = CommandParser().parse('memory search "hello world"')
        self.assertEqual(parsed.name, "memory search")
        self.assertEqual(parsed.arguments, ("hello world",))

    def test_parser_flags(self) -> None:
        parsed = CommandParser().parse("logs recent --limit=5 --verbose")
        self.assertEqual(parsed.flags["limit"], "5")
        self.assertTrue(parsed.flags["verbose"])

    def test_parser_empty_invalid(self) -> None:
        self.assertFalse(CommandParser().parse("").valid)

    def test_aliases_resolve(self) -> None:
        self.assertEqual(CommandAliases().resolve("?"), "help")

    def test_registry_register_lookup(self) -> None:
        registry = CommandRegistry()
        registry.register(CommandRecord("x", lambda ctx: ConversationResponse("x"), "x", "utility"))
        self.assertIsNotNone(registry.lookup("x"))

    def test_registry_alias_lookup(self) -> None:
        registry = CommandRegistry()
        registry.register(CommandRecord("help", lambda ctx: ConversationResponse("h"), "h", "utility", aliases=("?",)))
        self.assertEqual(registry.lookup("?").name, "help")  # type: ignore[union-attr]

    def test_registry_disable_enable(self) -> None:
        registry = CommandRegistry()
        registry.register(CommandRecord("x", lambda ctx: ConversationResponse("x"), "x", "utility"))
        registry.disable("x")
        self.assertFalse(registry.lookup("x").enabled)  # type: ignore[union-attr]
        registry.enable("x")
        self.assertTrue(registry.lookup("x").enabled)  # type: ignore[union-attr]

    def test_registry_unregister(self) -> None:
        registry = CommandRegistry()
        registry.register(CommandRecord("x", lambda ctx: ConversationResponse("x"), "x", "utility"))
        self.assertTrue(registry.unregister("x"))

    def test_registry_statistics(self) -> None:
        registry = CommandRegistry()
        registry.register(CommandRecord("x", lambda ctx: ConversationResponse("x"), "x", "utility"))
        self.assertEqual(registry.statistics()["registered_commands"], 1)

    def test_validator_unknown_command(self) -> None:
        result = CommandValidator().validate(CommandParser().parse("missing"), CommandRegistry())
        self.assertFalse(result.valid)

    def test_validator_known_command(self) -> None:
        registry = CommandRegistry()
        registry.register(CommandRecord("x", lambda ctx: ConversationResponse("x"), "x", "utility"))
        self.assertTrue(CommandValidator().validate(CommandParser().parse("x"), registry).valid)

    def test_dispatcher_dispatches(self) -> None:
        registry = CommandRegistry()
        registry.register(CommandRecord("x", lambda ctx: ConversationResponse("ok"), "x", "utility"))
        response = CommandDispatcher(registry).dispatch(CommandParser().parse("x"))
        self.assertEqual(response.response, "ok")

    def test_dispatcher_unknown(self) -> None:
        response = CommandDispatcher(CommandRegistry()).dispatch(CommandParser().parse("x"))
        self.assertIn("Unknown command", response.response)

    def test_command_history(self) -> None:
        history = CommandHistory()
        parsed = CommandParser().parse("help")
        response = ConversationResponse("ok")
        history.append(parsed, response)
        self.assertEqual(len(history.list_history()), 1)

    def test_command_metrics_defaults(self) -> None:
        self.assertEqual(CommandMetrics().commands_executed, 0)

    def test_command_help(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("help", CommandHelp().render(manager.registry))

    def test_command_manager_initializes_builtins(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertGreaterEqual(len(manager.registry.list_commands()), 30)

    def test_command_manager_help(self) -> None:
        manager = CommandManager()
        manager.initialize()
        response = manager.execute("help")
        self.assertIn("Available commands", response.response)

    def test_command_manager_exit(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertTrue(manager.execute("exit").should_exit)

    def test_command_manager_clear(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertTrue(manager.execute("clear").should_clear)

    def test_command_manager_history(self) -> None:
        manager = CommandManager()
        manager.initialize()
        manager.execute("help")
        self.assertIn("Command history", manager.execute("history").response)

    def test_command_manager_metrics(self) -> None:
        manager = CommandManager()
        manager.initialize()
        manager.execute("help")
        self.assertIn("Commands executed", manager.execute("metrics").response)

    def test_command_context(self) -> None:
        context = CommandContext("help", permissions=(CommandPermission.UTILITY,))
        self.assertEqual(context.command_name, "help")

    def test_conversation_session_record(self) -> None:
        session = ConversationSession()
        session.record("hi", "hello")
        self.assertEqual(session.previous_requests, ["hi"])

    def test_conversation_request(self) -> None:
        request = ConversationRequest("Hi", "hi")
        self.assertEqual(request.normalized_input, "hi")

    def test_conversation_response(self) -> None:
        response = ConversationResponse("hello")
        self.assertEqual(response.conversation_state, ConversationState.RESPONDING)

    def test_conversation_context(self) -> None:
        session = ConversationSession()
        context = ConversationContext(session=session)
        self.assertEqual(context.session, session)

    def test_conversation_history_append(self) -> None:
        history = ConversationHistory()
        request = ConversationRequest("Hi", "hi")
        response = ConversationResponse("hello")
        history.append(request, response)
        self.assertEqual(history.statistics()["turns"], 1)

    def test_conversation_history_search(self) -> None:
        history = ConversationHistory()
        history.append(ConversationRequest("Find memory", "find memory"), ConversationResponse("ok"))
        self.assertEqual(len(history.search("memory")), 1)

    def test_conversation_history_summary(self) -> None:
        self.assertIn("0 conversation", ConversationHistory().summarize())

    def test_conversation_history_export_restore_replay(self) -> None:
        history = ConversationHistory()
        record = (ConversationRequest("Hi", "hi"), ConversationResponse("hello"))
        history.restore((record,))
        self.assertEqual(history.replay(), ("Hi",))
        self.assertEqual(history.export(), (record,))

    def test_conversation_memory_availability(self) -> None:
        self.assertFalse(ConversationMemory().is_available())
        self.assertTrue(ConversationMemory(object()).is_available())

    def test_conversation_validator_empty(self) -> None:
        self.assertFalse(ConversationValidator().validate_request(ConversationRequest("", "")).valid)

    def test_conversation_validator_valid(self) -> None:
        self.assertTrue(ConversationValidator().validate_request(ConversationRequest("hi", "hi")).valid)

    def test_conversation_router_command(self) -> None:
        self.assertEqual(ConversationRouter().route(ConversationRequest("/help", "/help")), "command")

    def test_conversation_router_executive(self) -> None:
        self.assertEqual(ConversationRouter().route(ConversationRequest("hello", "hello")), "executive")

    def test_conversation_event(self) -> None:
        event = ConversationEvent(ConversationEventType.STARTED, "c")
        self.assertEqual(event.conversation_id, "c")

    def test_conversation_summary(self) -> None:
        summary = ConversationSummary("c", 2)
        self.assertEqual(summary.turns, 2)

    def test_conversation_metrics_defaults(self) -> None:
        self.assertEqual(ConversationMetrics().requests, 0)

    def test_conversation_logger(self) -> None:
        self.assertEqual(ConversationLogger().get_logger().name, "conversation")

    def test_conversation_recovery(self) -> None:
        self.assertTrue(ConversationRecovery().recover()["recovered"])

    def test_conversation_engine_no_jarvis(self) -> None:
        response = ConversationEngine().handle(ConversationRequest("hi", "hi"), ConversationContext(ConversationSession()))
        self.assertFalse(response.response == "")

    def test_conversation_manager_initializes(self) -> None:
        manager = ConversationManager(jarvis_core=JarvisCore())
        manager.jarvis_core.initialize()
        stats = manager.initialize()
        self.assertEqual(stats.command_engine_status, "ready")

    def test_conversation_manager_handles_command(self) -> None:
        manager = ConversationManager(jarvis_core=JarvisCore())
        manager.jarvis_core.initialize()
        manager.initialize()
        self.assertIn("Available commands", manager.handle_input("help").response)

    def test_conversation_manager_handles_exit(self) -> None:
        manager = ConversationManager(jarvis_core=JarvisCore())
        manager.jarvis_core.initialize()
        manager.initialize()
        self.assertTrue(manager.handle_input("exit").should_exit)

    def test_conversation_manager_handles_natural_language(self) -> None:
        core = JarvisCore()
        core.initialize()
        manager = ConversationManager(jarvis_core=core)
        manager.initialize()
        self.assertIn("JARVIS Executive", manager.handle_input("plan my day").response)

    def test_conversation_manager_history_updates(self) -> None:
        core = JarvisCore()
        core.initialize()
        manager = ConversationManager(jarvis_core=core)
        manager.initialize()
        manager.handle_input("hello")
        self.assertEqual(manager.history.statistics()["turns"], 1)

    def test_conversation_manager_summary(self) -> None:
        manager = ConversationManager()
        manager.initialize()
        self.assertEqual(manager.summary().turns, 0)

    def test_request_builder(self) -> None:
        self.assertEqual(RequestBuilder().build("Hello").normalized_input, "hello")

    def test_context_builder(self) -> None:
        request = RequestBuilder().build("Goal")
        self.assertEqual(ContextBuilder().build(request)["goal"], "Goal")

    def test_execution_planner(self) -> None:
        self.assertEqual(ExecutionPlanner().plan("direct").strategy, "direct")

    def test_execution_history(self) -> None:
        history = ExecutionHistory()
        summary = ExecutionSummary(True, "direct")
        history.append(summary)
        self.assertEqual(history.list_items(), (summary,))

    def test_response_composer(self) -> None:
        self.assertEqual(ResponseComposer().compose("ok").response, "ok")

    def test_response_validator(self) -> None:
        self.assertTrue(ResponseValidator().validate(ConversationResponse("ok")))

    def test_response_formatter(self) -> None:
        self.assertEqual(ResponseFormatter().format(ConversationResponse("ok")), "ok")

    def test_response_renderer(self) -> None:
        self.assertEqual(ResponseRenderer().render(ConversationResponse("ok")), "ok")

    def test_builtin_provider_list(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("provider list", manager.execute("provider list").response)

    def test_builtin_plugin_list(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("plugin list", manager.execute("plugin list").response)

    def test_builtin_agent_list(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("agent list", manager.execute("agent list").response)

    def test_builtin_department_list(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("department list", manager.execute("department list").response)

    def test_builtin_memory_search(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("memory search", manager.execute("memory search test").response)

    def test_builtin_knowledge_search(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("knowledge search", manager.execute("knowledge search test").response)

    def test_builtin_task_list(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("task list", manager.execute("task list").response)

    def test_builtin_config_show(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("config show", manager.execute("config show").response)

    def test_builtin_logs_recent(self) -> None:
        manager = CommandManager()
        manager.initialize()
        self.assertIn("logs recent", manager.execute("logs recent").response)


if __name__ == "__main__":
    unittest.main()
