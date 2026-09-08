from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import wave

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from jarvis.voice_intelligence import SpeechSynthesisRequest, SpeechSynthesisResult, TranscriptionRequest, VoiceIntelligence, VoiceStatus
from jarvis.voice_pipeline import (
    FasterWhisperAdapter,
    PiperAdapter,
    PTTState,
    PushToTalkController,
    STTRouter,
    TTSRouter,
    VoiceCommand,
    VoskCanonicalAdapter,
)


def write_wav(path: Path, frames: bytes = b"\x01\x00" * 1600) -> Path:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000); output.writeframes(frames)
    return path


class FakeVosk:
    available = True
    def status(self): return type("Status", (), {"value": "ready"})()
    def model_info(self): return type("Info", (), {"path": "models/vosk", "language": "en-US"})()
    def transcribe_wav(self, path, request_id, parent_request_id=None):
        from jarvis.stt_intelligence import LocalTranscriptionResult, VoiceInputStatus
        return LocalTranscriptionResult(request_id, parent_request_id, "offline-stt", VoiceInputStatus.COMPLETED, "Jarvis voice test", .8, .1, "en-US", "models/vosk")


class FailedPrimary(FasterWhisperAdapter):
    @property
    def available(self): return True
    def transcribe(self, request):
        return request_result(request, self.adapter_id, VoiceStatus.FAILED, errors=("stt_failed",))


def request_result(request, backend, status, text="", errors=()):
    from jarvis.voice_intelligence import TranscriptionResult
    return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, backend, status, text, text, errors=errors)


class FakeSapi:
    adapter_id = "windows-sapi"; available = True
    def health_check(self): return {"status": "healthy", "local": True}
    def synthesize(self, request):
        return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.COMPLETED, output_mode=request.output_mode)


class FakeCapture:
    adapter_id = "fixture-ptt"
    def __init__(self): self.callback = None; self.active = False
    def status(self): return "ready"
    def start(self, callback, sample_rate, channels): self.callback = callback; self.active = True
    def stop(self): self.active = False
    def send(self, value=b"\x01\x00" * 1600): self.callback(value)


class VoiceProviderTests(unittest.TestCase):
    def setUp(self): self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.wav = write_wav(self.root / "voice.wav")
    def tearDown(self): self.temp.cleanup()

    def test_faster_whisper_detection_health_and_mock_normalization(self):
        adapter = FasterWhisperAdapter(transcriber=lambda path, language: {"text": "Jarvis voice test", "segments": ({"text": "Jarvis", "start": 0.0, "end": .1},), "language": "en", "confidence": .9})
        self.assertTrue(adapter.detect().local); self.assertTrue(adapter.health().healthy)
        result = adapter.transcribe(TranscriptionRequest("t", "v", None, str(self.wav), adapter.adapter_id))
        self.assertEqual(result.status, VoiceStatus.COMPLETED); self.assertEqual(result.text, "Jarvis voice test"); self.assertEqual(result.segments[0]["start"], 0.0)

    def test_faster_whisper_malformed_timeout_and_local_no_secret_requirement(self):
        invalid = self.root / "bad.wav"; invalid.write_bytes(b"bad")
        adapter = FasterWhisperAdapter(transcriber=lambda path, language: (_ for _ in ()).throw(TimeoutError()))
        malformed = adapter.transcribe(TranscriptionRequest("t", "v", None, str(invalid), adapter.adapter_id))
        timed = adapter.transcribe(TranscriptionRequest("t2", "v", None, str(self.wav), adapter.adapter_id))
        self.assertEqual(malformed.errors, ("audio_format_invalid",)); self.assertEqual(timed.status, VoiceStatus.TIMED_OUT)
        self.assertNotIn("credential", str(adapter.health_check()).lower())

    def test_stt_primary_and_bounded_vosk_fallback(self):
        request = TranscriptionRequest("t", "v", None, str(self.wav), "router")
        primary = FasterWhisperAdapter(transcriber=lambda path, language: {"text": "primary"})
        self.assertEqual(STTRouter(primary, VoskCanonicalAdapter(FakeVosk())).route(request).backend_id, "faster-whisper")
        fallback = STTRouter(FailedPrimary(transcriber=lambda p, l: {}), VoskCanonicalAdapter(FakeVosk())).route(request)
        self.assertEqual(fallback.backend_id, "offline-stt"); self.assertTrue(fallback.fallback_used)
        unavailable = STTRouter(FasterWhisperAdapter(), VoskCanonicalAdapter(type("Missing", (), {"available": False, "model_info": lambda s: type("I", (), {"path": None, "language": "en"})(), "status": lambda s: type("S", (), {"value": "model_missing"})()})()), max_fallbacks=1).route(request)
        self.assertEqual(unavailable.status, VoiceStatus.UNAVAILABLE)

    def test_piper_mock_synthesis_bounds_and_cleanup(self):
        def runner(text, path): write_wav(path)
        adapter = PiperAdapter(temp_dir=self.root, runner=runner, max_text_chars=20)
        request = SpeechSynthesisRequest("s", "v", None, "piper", "Safe voice text", output_mode="file")
        result = adapter.synthesize(request); self.assertEqual(result.status, VoiceStatus.COMPLETED); self.assertTrue(Path(result.audio_reference).is_file())
        self.assertTrue(adapter.cleanup(result.audio_reference)); self.assertFalse(Path(result.audio_reference).exists())
        self.assertEqual(adapter.synthesize(SpeechSynthesisRequest("s2", "v", None, "piper", "", output_mode="file")).errors, ("empty_speech_text",))
        self.assertEqual(adapter.synthesize(SpeechSynthesisRequest("s3", "v", None, "piper", "x" * 21, output_mode="file")).errors, ("tts_text_too_large",))

    def test_piper_missing_voice_degrades_and_sapi_fallback_is_recorded(self):
        piper = PiperAdapter(temp_dir=self.root); self.assertFalse(piper.health().healthy)
        result = TTSRouter(piper, FakeSapi()).route(SpeechSynthesisRequest("s", "v", None, "router", "hello", output_mode="playback"))
        self.assertEqual(result.backend_id, "windows-sapi"); self.assertTrue(result.fallback_used); self.assertIn("fallback_from_piper", result.warnings)

    def test_voice_runtime_applies_configured_duration_and_timeout_bounds(self):
        voice_config = SimpleNamespace(
            enabled=False, input_enabled=False, output_enabled=False,
            max_audio_duration=42, stt_timeout_seconds=17,
            tts_timeout_seconds=19, temp_directory=self.root,
        )
        voice = VoiceIntelligence(SimpleNamespace(voice=voice_config, base_dir=self.root))
        self.assertEqual(voice.limits.max_audio_duration, 42)
        self.assertEqual(voice.limits.transcription_timeout, 17)
        self.assertEqual(voice.limits.synthesis_timeout, 19)
        self.assertIn("primary_route", voice.input_status())
        self.assertIn("fallback_route", voice.input_status())
        self.assertNotIn(str(self.root), str(voice.health()))
        self.assertEqual(voice.health()["temp_directory"], "managed_local_temp")
        voice.shutdown()


class PushToTalkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.capture = FakeCapture()
        primary = FasterWhisperAdapter(transcriber=lambda path, language: {"text": "delete all files", "confidence": .9})
        self.controller = PushToTalkController(STTRouter(primary, VoskCanonicalAdapter(FakeVosk())), TTSRouter(PiperAdapter(temp_dir=self.root, runner=lambda text, path: write_wav(path)), FakeSapi()), self.root, backend=self.capture)
    def tearDown(self): self.controller.cancel_capture(); self.temp.cleanup()

    def test_no_recording_before_activation_double_start_and_double_stop(self):
        self.assertEqual(self.controller.status()["state"], "idle"); self.assertFalse(self.capture.active)
        self.controller.start_capture(); self.assertTrue(self.capture.active)
        with self.assertRaisesRegex(ValueError, "capture_already_active"): self.controller.start_capture()
        self.capture.send(); self.controller.stop_capture(); self.assertFalse(self.capture.active)
        with self.assertRaisesRegex(ValueError, "capture_not_active"): self.controller.stop_capture()

    def test_stop_process_uses_normal_dispatch_and_never_persists_transcript(self):
        calls = []; self.controller.start_capture(); self.capture.send(); stopped = self.controller.stop_capture(); path = Path(stopped.audio_reference)
        session, result, response = self.controller.process_capture(lambda text: calls.append(text) or "approval required")
        self.assertEqual(calls, ["delete all files"]); self.assertEqual(response, "approval required"); self.assertEqual(session.state, PTTState.READY_TO_PLAY)
        self.assertFalse(path.exists()); self.assertEqual(session.transcript_status, "session_context_only"); self.assertFalse(self.controller.status()["transcript_persistence"])
        command = VoiceCommand("request", result.text); self.assertFalse(command.approval_bypass); self.assertEqual(command.route, "normal_jarvis_request")

    def test_cancellation_cleanup_restart_and_checkpoint_are_safe(self):
        self.controller.start_capture(); self.capture.send(); stopped = self.controller.stop_capture(); path = Path(stopped.audio_reference)
        self.controller.cancel_capture(); self.assertFalse(path.exists()); self.assertEqual(self.controller.session.state, PTTState.CANCELLED)
        self.assertEqual(self.controller.recover_after_restart().state, PTTState.IDLE); self.assertFalse(self.controller.checkpoint_metadata()["raw_audio"])

    def test_audio_bounds_fail_without_file_leak(self):
        controller = PushToTalkController(self.controller.stt, self.controller.tts, self.root, backend=self.capture, max_audio_bytes=1024)
        controller.start_capture(); self.capture.send(b"x" * 2048)
        self.assertEqual(controller.session.state, PTTState.FAILED); self.assertFalse(tuple(self.root.glob("ptt-*.wav")))

    def test_ptt_cli_status_and_disabled_start_never_open_microphone(self):
        voice = VoiceIntelligence(); voice.ptt.backend = self.capture
        manager = CommandManager(); manager.initialize(); context = ConversationContext(ConversationSession(), voice_intelligence=voice)
        self.assertIn("state=idle", manager.execute("voice ptt status", context).response)
        self.assertIn("disabled", manager.execute("voice ptt start", context).response); self.assertFalse(self.capture.active)
        voice.shutdown()

    def test_ptt_cli_process_returns_normal_dispatch_metadata(self):
        voice = VoiceIntelligence(); voice.enabled = True; voice.input_enabled = True; voice.ptt = self.controller
        manager = CommandManager(); manager.initialize(); context = ConversationContext(ConversationSession(), voice_intelligence=voice)
        self.assertIn("capture active", manager.execute("voice ptt start", context).response); self.capture.send()
        self.assertIn("capture stopped", manager.execute("voice ptt stop", context).response)
        response = manager.execute("voice ptt process", context)
        self.assertTrue(response.metadata["dispatch_voice_transcript"]); self.assertFalse(response.metadata["raw_audio_persistence"]); self.assertEqual(self.controller.status()["state"], "idle")
        voice.shutdown()


if __name__ == "__main__": unittest.main()
