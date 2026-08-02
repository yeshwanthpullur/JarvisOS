"""Focused tests for local Vosk STT and explicit microphone capture."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from commands import CommandManager
from conversation import ConversationContext, ConversationResponse, ConversationSession
from core.startup_manager import StartupManager
from jarvis.stt_intelligence import (
    AudioCaptureConfig,
    AudioCaptureStatus,
    CapturedAudio,
    LocalTranscriptionRequest,
    LocalTranscriptionResult,
    SoundDeviceCaptureAdapter,
    STTProviderStatus,
    VoiceInputManager,
    VoiceInputStatus,
    VoskSTTAdapter,
)
from jarvis.voice_intelligence import VoiceIntelligence


def make_model(root: Path) -> Path:
    model = root / "vosk-model"
    (model / "am").mkdir(parents=True)
    (model / "conf").mkdir()
    (model / "am" / "final.mdl").write_bytes(b"model")
    (model / "conf" / "model.conf").write_text("sample-frequency=16000", encoding="utf-8")
    return model


class FakeRecognizer:
    def __init__(self, model, sample_rate):
        self.model = model
        self.sample_rate = sample_rate
        self.chunks = []

    def SetWords(self, enabled):
        self.words = enabled

    def AcceptWaveform(self, chunk):
        self.chunks.append(chunk)
        return True

    def FinalResult(self):
        return json.dumps({"text": "jarvis local speech", "result": [{"word": "jarvis", "conf": 0.9}, {"word": "local", "conf": 0.8}, {"word": "speech", "conf": 1.0}]})


class FakeVosk:
    class Model:
        def __init__(self, path):
            self.path = path

    KaldiRecognizer = FakeRecognizer

    @staticmethod
    def SetLogLevel(level):
        return None


class FakeSTTAdapter:
    adapter_id = "offline-stt"

    def status(self):
        return STTProviderStatus.READY

    def model_info(self):
        return SimpleNamespace(valid=True, path="[local-model]")

    def transcribe(self, request):
        return LocalTranscriptionResult(request.request_id, request.parent_request_id, self.adapter_id, VoiceInputStatus.COMPLETED, "hello from microphone", 0.91, request.duration, "en", "[local-model]", started_at="start", completed_at="end")

    def transcribe_wav(self, path, request_id, parent_request_id=None):
        return LocalTranscriptionResult(request_id, parent_request_id, self.adapter_id, VoiceInputStatus.COMPLETED, "hello from file", 0.92, 0.1, "en", "[local-model]", started_at="start", completed_at="end")


class FakeCaptureAdapter:
    adapter_id = "fake-capture"

    def status(self):
        return AudioCaptureStatus.READY

    def devices(self):
        return ()

    def capture(self, config):
        return CapturedAudio(AudioCaptureStatus.COMPLETED, b"\x01\x00" * 1600, config.sample_rate, 1, 2, 0.1)


class VoskAdapterTests(unittest.TestCase):
    def test_dependency_is_lazy_and_missing_is_truthful(self):
        adapter = VoskSTTAdapter(None)
        with patch("jarvis.stt_intelligence.importlib.util.find_spec", return_value=None):
            self.assertEqual(adapter.status(), STTProviderStatus.DEPENDENCY_MISSING)
            self.assertFalse(adapter.available)
            result = adapter.transcribe(LocalTranscriptionRequest("r", None, "en", 16000, 1, 2, b"\0\0"))
        self.assertEqual(result.status, VoiceInputStatus.UNAVAILABLE)
        self.assertEqual(result.error_code, "STT_DEPENDENCY_MISSING")

    def test_model_structure_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = root / "invalid"; invalid.mkdir()
            self.assertFalse(VoskSTTAdapter(invalid).model_info().valid)
            valid = make_model(root)
            info = VoskSTTAdapter(valid).model_info()
            self.assertTrue(info.valid)
            self.assertEqual(info.missing_files, ())

    def test_real_adapter_algorithm_normalizes_vosk_result(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = VoskSTTAdapter(make_model(Path(directory)))
            request = LocalTranscriptionRequest("request-1", "parent-1", "en", 16000, 1, 2, b"\x01\x00" * 100, 0.1)
            with patch("jarvis.stt_intelligence.importlib.util.find_spec", return_value=object()), patch("jarvis.stt_intelligence.importlib.import_module", return_value=FakeVosk):
                result = adapter.transcribe(request)
            self.assertEqual(result.status, VoiceInputStatus.COMPLETED)
            self.assertEqual(result.text, "jarvis local speech")
            self.assertAlmostEqual(result.confidence, 0.9)
            self.assertEqual(result.parent_request_id, "parent-1")

    def test_unsupported_audio_and_empty_speech_are_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = VoskSTTAdapter(make_model(Path(directory)))
            with patch("jarvis.stt_intelligence.importlib.util.find_spec", return_value=object()):
                stereo = adapter.transcribe(LocalTranscriptionRequest("r", None, "en", 16000, 2, 2, b"\0\0"))
                empty = adapter.transcribe(LocalTranscriptionRequest("e", None, "en", 16000, 1, 2, b""))
            self.assertEqual(stereo.error_code, "STT_UNSUPPORTED_AUDIO_FORMAT")
            self.assertEqual(empty.status, VoiceInputStatus.NO_SPEECH)


class CaptureAndManagerTests(unittest.TestCase):
    def test_capture_dependency_missing_does_not_touch_microphone(self):
        adapter = SoundDeviceCaptureAdapter()
        with patch("jarvis.stt_intelligence.importlib.util.find_spec", return_value=None):
            self.assertEqual(adapter.status(), AudioCaptureStatus.DEPENDENCY_MISSING)
            result = adapter.capture(AudioCaptureConfig(max_capture_seconds=1))
        self.assertEqual(result.error_code, "STT_CAPTURE_DEPENDENCY_MISSING")
        self.assertEqual(result.pcm_bytes, b"")

    def test_manager_captures_in_memory_and_audit_omits_content(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = VoiceInputManager(SimpleNamespace(language="en-US", voice_input_audit_retention=2), Path(directory), stt_adapter=FakeSTTAdapter(), capture_adapter=FakeCaptureAdapter())
            result = manager.listen("parent-request")
            self.assertEqual(result.text, "hello from microphone")
            self.assertEqual(result.parent_request_id, "parent-request")
            stored = manager.audit_path.read_text(encoding="utf-8")
            self.assertNotIn(result.text, stored)
            self.assertNotIn("pcm", stored.lower())
            self.assertFalse(manager.audit_events()[0].raw_audio_persisted)
            self.assertFalse(manager.audit_events()[0].transcript_persisted)

    def test_audit_retention_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = VoiceInputManager(SimpleNamespace(voice_input_audit_retention=2), Path(directory), stt_adapter=FakeSTTAdapter(), capture_adapter=FakeCaptureAdapter())
            for _ in range(4):
                manager.listen()
            self.assertEqual(len(manager.audit_events()), 2)

    def test_environment_model_path_is_non_secret_configuration(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"JARVIS_VOSK_MODEL_PATH": directory}):
            manager = VoiceInputManager(SimpleNamespace())
            self.assertEqual(manager.stt_adapter.model_path, Path(directory).resolve())

    def test_default_model_path_is_repository_stable(self):
        with patch.dict("os.environ", {}, clear=True):
            manager = VoiceInputManager(SimpleNamespace())
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(manager.stt_adapter.model_path, root / "models" / "vosk")


class VoiceInputCommandTests(unittest.TestCase):
    def configured_voice(self):
        voice = VoiceIntelligence()
        voice.voice_input = VoiceInputManager(SimpleNamespace(), stt_adapter=FakeSTTAdapter(), capture_adapter=FakeCaptureAdapter())
        voice.input_enabled = True
        voice.enabled = True
        return voice

    def test_listen_returns_transcript_without_automatic_dispatch(self):
        commands = CommandManager(); commands.initialize()
        response = commands.execute("voice listen", ConversationContext(ConversationSession(), voice_intelligence=self.configured_voice()))
        self.assertIn("hello from microphone", response.response)
        self.assertFalse(response.metadata["dispatch_voice_transcript"])
        self.assertIsNone(response.metadata["voice_transcript"])

    def test_listen_send_requests_existing_conversation_path(self):
        commands = CommandManager(); commands.initialize()
        response = commands.execute("voice listen send", ConversationContext(ConversationSession(), voice_intelligence=self.configured_voice()))
        self.assertTrue(response.metadata["dispatch_voice_transcript"])
        self.assertEqual(response.metadata["voice_transcript"], "hello from microphone")

    def test_cli_loop_dispatches_only_explicit_voice_transcript(self):
        first = ConversationResponse("Transcript ready.", metadata={"dispatch_voice_transcript": True, "voice_transcript": "project status"})
        second = ConversationResponse("Project is healthy.")
        conversation = SimpleNamespace(handle_input=Mock(side_effect=[first, second]), command_manager=SimpleNamespace(parser=SimpleNamespace(parse=lambda text: SimpleNamespace(name="voice listen")), registry=SimpleNamespace(lookup=lambda name: object())))
        manager = StartupManager(); manager.conversation_manager = conversation; manager.jarvis_core = SimpleNamespace(manager=SimpleNamespace(voice_intelligence=SimpleNamespace(output_enabled=False)))
        with patch("builtins.input", side_effect=["voice listen send", EOFError]), patch("builtins.print"):
            manager.command_loop()
        self.assertEqual(conversation.handle_input.call_args_list[1].args[0], "project status")


class VoiceInputRepositorySafetyTests(unittest.TestCase):
    def test_optional_dependencies_are_not_core_requirements(self):
        root = Path(__file__).resolve().parents[1]
        core = (root / "requirements.txt").read_text(encoding="utf-8")
        optional = (root / "requirements-voice.txt").read_text(encoding="utf-8")
        self.assertNotIn("vosk", core.lower())
        self.assertIn("vosk", optional.lower())
        self.assertIn("sounddevice", optional.lower())

    def test_memory_policy_documents_transient_audio_and_transcripts(self):
        root = Path(__file__).resolve().parents[1]
        policy = (root / "docs" / "MEMORY_AND_DATA_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("Push-to-talk audio is processed in memory", policy)
        self.assertIn("never transcript text or audio bytes", policy)

    def test_model_and_audio_artifacts_are_ignored(self):
        root = Path(__file__).resolve().parents[1]
        ignore = (root / ".gitignore").read_text(encoding="utf-8")
        for value in ("models/vosk/", "*.wav", "*.mp3", "*.zip"):
            self.assertIn(value, ignore)


if __name__ == "__main__":
    unittest.main()
