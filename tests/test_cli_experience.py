"""Focused tests for the stable primary JARVIS CLI experience."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from commands import CommandManager
from config.logging import configure_logging
from conversation import ConversationContext, ConversationResponse, ConversationSession
from core.startup_manager import StartupManager
from jarvis.jarvis_tools import JarvisTools
from jarvis.voice_intelligence import SpeechSynthesisResult, VoiceIntelligence, VoiceStatus


class _Registry:
    def __init__(self, records: tuple[object, ...]) -> None:
        self.records = records

    def all(self) -> tuple[object, ...]:
        return self.records


def _local_provider_manager() -> object:
    model = SimpleNamespace(model_id="llama3.2:1b")
    provider = SimpleNamespace(
        health=SimpleNamespace(available=True),
        list_models=lambda: (model,),
    )
    config = SimpleNamespace(
        provider_id="local",
        kind="ollama",
        local_only=True,
        preferred_model="llama3.2:1b",
        default_model="llama3.2:1b",
    )
    return SimpleNamespace(registry=_Registry((SimpleNamespace(config=config, provider=provider),)))


class CliExperienceTests(unittest.TestCase):
    def command_context(self, **kwargs: object) -> ConversationContext:
        return ConversationContext(session=ConversationSession(), **kwargs)

    def test_help_is_focused_on_primary_cli_commands(self) -> None:
        commands = CommandManager()
        commands.initialize()
        help_text = commands.execute("help").response
        for expected in (
            "local only on/off",
            "local use <model>",
            "voice status",
            "voice output on/off",
            "voice say <text>",
            "provider status",
            "tools status",
            "exit",
        ):
            self.assertIn(expected, help_text)

    def test_provider_status_shows_session_policy_and_selection(self) -> None:
        commands = CommandManager()
        commands.initialize()
        context = self.command_context(provider_manager=_local_provider_manager())
        context.session.metadata.update(
            execution_policy="local_only",
            provider_preference="local",
            model_preference="llama3.2:1b",
        )
        response = commands.execute("provider status", context)
        self.assertIn("mode=local_only", response.response)
        self.assertIn("provider=local", response.response)
        self.assertIn("model=llama3.2:1b", response.response)

    def test_local_use_populates_provider_neutral_preferences(self) -> None:
        commands = CommandManager()
        commands.initialize()
        context = self.command_context(provider_manager=_local_provider_manager())
        response = commands.execute("local use llama3.2:1b", context)
        self.assertIn("Local model selected", response.response)
        self.assertEqual(context.session.metadata["provider_preference"], "local")
        self.assertEqual(context.session.metadata["model_preference"], "llama3.2:1b")

    def test_tools_status_reports_real_registry_readiness(self) -> None:
        commands = CommandManager()
        commands.initialize()
        tools = JarvisTools()
        response = commands.execute("tools status", self.command_context(tool_manager=tools))
        self.assertIn("ready=2/2", response.response)

    def test_voice_output_commands_report_backend_readiness(self) -> None:
        commands = CommandManager()
        commands.initialize()
        voice = VoiceIntelligence()
        voice.registry.get("windows-sapi").available = True
        context = self.command_context(voice_intelligence=voice)
        enabled = commands.execute("voice output on", context)
        self.assertTrue(voice.output_enabled)
        self.assertIn("windows-sapi", enabled.response)
        self.assertIn("playback=ready", commands.execute("voice status", context).response)
        disabled = commands.execute("voice output off", context)
        self.assertFalse(voice.output_enabled)
        self.assertIn("text-only", disabled.response)

    def test_voice_output_cannot_enable_an_unavailable_backend(self) -> None:
        commands = CommandManager()
        commands.initialize()
        voice = VoiceIntelligence()
        voice.registry.get("windows-sapi").available = False
        response = commands.execute("voice output on", self.command_context(voice_intelligence=voice))
        self.assertFalse(voice.output_enabled)
        self.assertIn("unavailable", response.response)

    def test_non_debug_logging_keeps_info_messages_out_of_console(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = SimpleNamespace(
                logs_dir=root,
                log_level="INFO",
                debug=False,
                logging=SimpleNamespace(
                    log_dir=root,
                    log_file="jarvis.log",
                    max_bytes=1024,
                    backup_count=1,
                ),
            )
            with patch("config.logging.logging.config.dictConfig") as configure:
                configure_logging(settings)
        config = configure.call_args.args[0]
        self.assertEqual(config["handlers"]["console"]["level"], "WARNING")
        self.assertEqual(config["handlers"]["file"]["level"], "INFO")

    def test_debug_logging_keeps_configured_console_level(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = SimpleNamespace(
                logs_dir=root,
                log_level="DEBUG",
                debug=True,
                logging=SimpleNamespace(
                    log_dir=root,
                    log_file="jarvis.log",
                    max_bytes=1024,
                    backup_count=1,
                ),
            )
            with patch("config.logging.logging.config.dictConfig") as configure:
                configure_logging(settings)
        self.assertEqual(configure.call_args.args[0]["handlers"]["console"]["level"], "DEBUG")

    def test_safe_cli_response_requests_playback_with_correlated_id(self) -> None:
        voice = VoiceIntelligence()
        voice.output_enabled = True
        voice.enabled = True
        manager = StartupManager()
        manager.jarvis_core = SimpleNamespace(manager=SimpleNamespace(voice_intelligence=voice))
        completed = SpeechSynthesisResult(
            "synthesis",
            "session",
            "request-7",
            "windows-sapi",
            VoiceStatus.COMPLETED,
            output_mode="playback",
        )
        with patch.object(voice, "say", return_value=completed) as say:
            notice = manager._speak_cli_response(
                ConversationResponse("A safe answer.", metadata={"jarvis_request_id": "request-7"})
            )
        self.assertIsNone(notice)
        say.assert_called_once_with("A safe answer.", parent_request_id="request-7", playback=True)

    def test_multi_sentence_cli_response_is_passed_to_speech_in_full(self) -> None:
        voice = VoiceIntelligence()
        voice.output_enabled = True
        voice.enabled = True
        manager = StartupManager()
        manager.jarvis_core = SimpleNamespace(manager=SimpleNamespace(voice_intelligence=voice))
        text = "First paragraph is complete. Second sentence remains intact. Third sentence is also spoken."
        completed = SpeechSynthesisResult("synthesis", "session", "request-8", "windows-sapi", VoiceStatus.COMPLETED, output_mode="playback")
        with patch.object(voice, "say", return_value=completed) as say:
            notice = manager._speak_cli_response(ConversationResponse(text, metadata={"jarvis_request_id": "request-8"}))
        self.assertIsNone(notice)
        say.assert_called_once_with(text, parent_request_id="request-8", playback=True)
        self.assertNotIn("more detail", text.lower())

    def test_command_inputs_are_kept_out_of_automatic_reply_speech(self) -> None:
        commands = CommandManager()
        commands.initialize()
        manager = StartupManager()
        manager.conversation_manager = SimpleNamespace(command_manager=commands)
        self.assertTrue(manager._is_registered_command("voice status"))
        self.assertTrue(manager._is_registered_command("/provider status"))
        self.assertFalse(manager._is_registered_command("What is the capital of France?"))

    def test_code_and_sensitive_cli_responses_remain_text_only(self) -> None:
        voice = VoiceIntelligence()
        voice.output_enabled = True
        manager = StartupManager()
        manager.jarvis_core = SimpleNamespace(manager=SimpleNamespace(voice_intelligence=voice))
        with patch.object(voice, "say") as say:
            code_notice = manager._speak_cli_response(ConversationResponse("```python\nprint('x')\n```"))
            sensitive_notice = manager._speak_cli_response(ConversationResponse("The API key is hidden."))
            warning_notice = manager._speak_cli_response(ConversationResponse("Review this response.", warnings=("warning",)))
            failed_notice = manager._speak_cli_response(ConversationResponse("Provider failed.", execution_state="failed"))
        self.assertIn("code", code_notice)
        self.assertIn("safety", sensitive_notice)
        self.assertIn("safety", warning_notice)
        self.assertIn("safety", failed_notice)
        say.assert_not_called()

    def test_automatic_speech_cap_reports_text_only_instead_of_summarizing(self) -> None:
        voice = VoiceIntelligence()
        voice.output_enabled = True
        voice.max_auto_speech_chars = 10
        manager = StartupManager()
        manager.jarvis_core = SimpleNamespace(manager=SimpleNamespace(voice_intelligence=voice))
        with patch.object(voice, "say") as say:
            notice = manager._speak_cli_response(ConversationResponse("This response is safely over the configured cap."))
        self.assertIn("exceeds", notice)
        self.assertIn("10 character", notice)
        say.assert_not_called()

    def test_concise_cli_summary_includes_mode_model_and_voice(self) -> None:
        voice = VoiceIntelligence()
        voice.registry.get("windows-sapi").available = True
        manager = StartupManager()
        manager.provider_manager = _local_provider_manager()
        manager.conversation_manager = SimpleNamespace(active_session=ConversationSession())
        manager.jarvis_core = SimpleNamespace(manager=SimpleNamespace(voice_intelligence=voice))
        with patch("builtins.print") as output:
            manager._display_cli_startup_summary()
        rendered = "\n".join(str(call.args[0]) for call in output.call_args_list)
        self.assertIn("JARVIS CLI Ready", rendered)
        self.assertIn("Provider mode: automatic", rendered)
        self.assertIn("Local-only: off", rendered)
        self.assertIn("Local model: llama3.2:1b", rendered)
        self.assertIn("Voice output: off", rendered)


if __name__ == "__main__":
    unittest.main()
