from __future__ import annotations

import tempfile
import threading
import time
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from commands import CommandManager
from conversation import ConversationContext, ConversationResponse, ConversationSession
from core.startup_manager import StartupManager
from jarvis.voice_intelligence import (
    PlaybackState,
    SpeechSynthesisResult,
    TranscriptionResult,
    VoiceIntelligence,
    VoiceStatus,
)


class VoicePlaybackControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.voice = VoiceIntelligence()
        self.voice.enabled = True
        self.voice.output_enabled = True
        self.adapter = self.voice.registry.get("windows-sapi")
        self.adapter.available = True

    def tearDown(self) -> None:
        self.voice.shutdown()

    @staticmethod
    def completed(request: object) -> SpeechSynthesisResult:
        return SpeechSynthesisResult(
            request.synthesis_id,
            request.voice_session_id,
            request.parent_request_id,
            "windows-sapi",
            VoiceStatus.COMPLETED,
            output_mode="playback",
        )

    def wait_for(self, state: PlaybackState, timeout: float = 2.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.voice.playback_status()["state"] == state.value:
                return
            time.sleep(0.01)
        self.fail(f"Playback did not reach {state.value}: {self.voice.playback_status()}")

    def test_automatic_playback_is_non_blocking_and_stop_clears_queue(self) -> None:
        entered = threading.Event()

        def blocking(request: object, stop_event: threading.Event) -> SpeechSynthesisResult:
            entered.set()
            stop_event.wait(2)
            return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, "windows-sapi", VoiceStatus.CANCELLED, output_mode="playback")

        with patch.object(self.adapter, "synthesize_interruptible", side_effect=blocking), patch.object(self.adapter, "stop_playback", return_value=True):
            started = time.monotonic()
            self.voice.start_playback("First sentence. Second sentence. Third sentence.")
            self.assertLess(time.monotonic() - started, 0.25)
            self.assertTrue(entered.wait(1))
            self.assertTrue(self.voice.stop_playback(wait=True))
        status = self.voice.playback_status()
        self.assertEqual(status["state"], "stopped")
        self.assertEqual(status["remaining_chunks"], 0)

    def test_stop_while_idle_is_truthful(self) -> None:
        commands = CommandManager(); commands.initialize()
        response = commands.execute("voice stop", ConversationContext(ConversationSession(), voice_intelligence=self.voice))
        self.assertIn("VOICE_NOT_SPEAKING", response.response)

    def test_pause_at_boundary_and_resume_retained_chunks(self) -> None:
        self.voice.limits = replace(self.voice.limits, max_spoken_response_length=100)
        first_gate = threading.Event(); calls = []

        def controlled(request: object, stop_event: threading.Event) -> SpeechSynthesisResult:
            calls.append(request.text)
            if len(calls) == 1:
                first_gate.wait(2)
            return self.completed(request)

        text = "First sentence contains enough explanatory detail to occupy most of one safe speech chunk. Second sentence remains queued for resume."
        with patch.object(self.adapter, "synthesize_interruptible", side_effect=controlled):
            self.voice.start_playback(text)
            while not calls: time.sleep(0.01)
            result = self.voice.pause_playback()
            self.assertEqual(result["code"], "VOICE_PAUSE_AT_BOUNDARY")
            first_gate.set(); self.wait_for(PlaybackState.PAUSED)
            self.assertEqual(len(calls), 1)
            self.assertTrue(self.voice.resume_playback()["ok"])
            self.wait_for(PlaybackState.COMPLETED)
        self.assertGreater(len(calls), 1)
        self.assertEqual(" ".join(calls), text)

    def test_new_playback_replaces_old_without_overlap(self) -> None:
        first_entered = threading.Event(); calls = []; active = 0; maximum_active = 0
        def controlled(request: object, stop_event: threading.Event) -> SpeechSynthesisResult:
            nonlocal active, maximum_active
            active += 1; maximum_active = max(maximum_active, active); calls.append(request.text)
            if request.text == "Old response.": first_entered.set(); stop_event.wait(2)
            active -= 1
            status = VoiceStatus.CANCELLED if stop_event.is_set() else VoiceStatus.COMPLETED
            return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, "windows-sapi", status, output_mode="playback")
        with patch.object(self.adapter, "synthesize_interruptible", side_effect=controlled), patch.object(self.adapter, "stop_playback", return_value=True):
            self.voice.start_playback("Old response."); self.assertTrue(first_entered.wait(1))
            self.voice.start_playback("New response."); self.wait_for(PlaybackState.COMPLETED)
        self.assertEqual(calls, ["Old response.", "New response."])
        self.assertEqual(maximum_active, 1)

    def test_sapi_stop_terminates_active_process(self) -> None:
        process = SimpleNamespace(poll=lambda: None, terminate=lambda: setattr(process, "terminated", True), wait=lambda timeout: 0, terminated=False)
        self.adapter._active_process = process
        self.assertTrue(self.adapter.stop_playback())
        self.assertTrue(process.terminated)

    def test_sapi_cancel_before_launch_never_starts_process(self) -> None:
        stop_event = threading.Event(); stop_event.set()
        request = SimpleNamespace(synthesis_id="s", voice_session_id="v", parent_request_id="p", text="cancelled", rate=0, volume=100, timeout=30)
        with patch("jarvis.voice_intelligence.subprocess.Popen") as popen:
            result = self.adapter.synthesize_interruptible(request, stop_event)
        self.assertEqual(result.status, VoiceStatus.CANCELLED)
        popen.assert_not_called()

    def test_repeat_replays_last_safe_reply_once(self) -> None:
        calls = []
        def capture(request: object, stop_event: threading.Event) -> SpeechSynthesisResult:
            calls.append(request.text); return self.completed(request)
        with patch.object(self.adapter, "synthesize_interruptible", side_effect=capture):
            self.voice.start_playback("A safe reply."); self.wait_for(PlaybackState.COMPLETED)
            result = self.voice.repeat_last(); self.assertTrue(result["ok"])
            self.wait_for(PlaybackState.COMPLETED)
        self.assertEqual(calls, ["A safe reply.", "A safe reply."])

    def test_shutdown_stops_worker_without_audio_files(self) -> None:
        entered = threading.Event()
        def blocking(request: object, stop_event: threading.Event) -> SpeechSynthesisResult:
            entered.set(); stop_event.wait(2); return self.completed(request)
        with tempfile.TemporaryDirectory() as directory, patch.object(self.adapter, "synthesize_interruptible", side_effect=blocking), patch.object(self.adapter, "stop_playback", return_value=True):
            self.voice.temp_directory = Path(directory)
            self.voice.start_playback("Shutdown test."); self.assertTrue(entered.wait(1)); self.voice.shutdown()
            self.assertFalse(any(Path(directory).iterdir()))
        self.assertFalse(self.voice._playback_thread.is_alive())

    def test_new_free_form_question_stops_speech_before_routing(self) -> None:
        events = []
        commands = CommandManager(); commands.initialize()
        voice = SimpleNamespace(output_enabled=False, stop_playback=lambda wait=False: events.append("stop"))
        def handle(text: str) -> ConversationResponse:
            events.append(f"handle:{text}")
            return ConversationResponse("answer", should_exit=text == "exit")
        startup = StartupManager()
        startup.jarvis_core = SimpleNamespace(manager=SimpleNamespace(voice_intelligence=voice))
        startup.conversation_manager = SimpleNamespace(command_manager=commands, handle_input=handle)
        with patch("builtins.input", side_effect=["What changed?", "exit"]), patch("builtins.print"):
            startup.command_loop()
        self.assertLess(events.index("stop"), events.index("handle:What changed?"))

    def test_interrupt_stops_before_explicit_capture_and_dispatches(self) -> None:
        events = []
        result = TranscriptionResult("t", "s", "p", "offline-stt", VoiceStatus.COMPLETED, "Explain intake again", "Explain intake again", confidence=.9)
        voice = SimpleNamespace(
            stop_playback=lambda wait=False: events.append("stop") or True,
            input_status=lambda: {"stt_available": True, "microphone_available": True},
            enabled=True, input_enabled=True,
            listen=lambda parent_request_id: events.append("listen") or result,
        )
        commands = CommandManager(); commands.initialize()
        response = commands.execute("voice interrupt", ConversationContext(ConversationSession(), voice_intelligence=voice))
        self.assertEqual(events, ["stop", "listen"])
        self.assertTrue(response.metadata["dispatch_voice_transcript"])
        self.assertEqual(response.metadata["voice_transcript"], "Explain intake again")

    def test_interrupt_unavailable_never_activates_microphone(self) -> None:
        voice = SimpleNamespace(stop_playback=lambda wait=False: True, input_status=lambda: {"stt_available": False}, enabled=True, input_enabled=True)
        commands = CommandManager(); commands.initialize()
        response = commands.execute("voice interrupt", ConversationContext(ConversationSession(), voice_intelligence=voice))
        self.assertIn("VOICE_INTERRUPT_STT_UNAVAILABLE", response.response)

    def test_interrupt_no_speech_is_safe(self) -> None:
        result = TranscriptionResult("t", "s", "p", "offline-stt", VoiceStatus.NO_SPEECH, errors=("STT_NO_SPEECH",))
        voice = SimpleNamespace(stop_playback=lambda wait=False: True, input_status=lambda: {"stt_available": True, "microphone_available": True}, enabled=True, input_enabled=True, listen=lambda parent_request_id: result)
        commands = CommandManager(); commands.initialize()
        response = commands.execute("voice interrupt", ConversationContext(ConversationSession(), voice_intelligence=voice))
        self.assertIn("VOICE_INTERRUPT_NO_SPEECH", response.response)
        self.assertFalse(response.metadata.get("dispatch_voice_transcript", False))

    def test_correction_stops_and_routes_without_history_rewrite(self) -> None:
        voice = SimpleNamespace(stop_playback=lambda wait=False: True)
        commands = CommandManager(); commands.initialize()
        response = commands.execute("voice correction Explain compression", ConversationContext(ConversationSession(), voice_intelligence=voice))
        self.assertTrue(response.metadata["voice_correction"])
        self.assertEqual(response.metadata["voice_transcript"], "Explain compression")
        self.assertTrue(response.metadata["dispatch_voice_transcript"])

    def test_empty_correction_is_rejected(self) -> None:
        voice = SimpleNamespace(stop_playback=lambda wait=False: True)
        commands = CommandManager(); commands.initialize()
        response = commands.execute("voice correction", ConversationContext(ConversationSession(), voice_intelligence=voice))
        self.assertIn("VOICE_CORRECTION_EMPTY", response.response)
        self.assertFalse(response.metadata.get("dispatch_voice_transcript", False))


if __name__ == "__main__":
    unittest.main()
