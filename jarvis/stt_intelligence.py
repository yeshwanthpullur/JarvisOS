"""Offline, explicit-command speech input for JARVIS OS."""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import os
import queue
import time
import uuid
import wave
from array import array
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol


def _now() -> str:
    return datetime.now(UTC).isoformat()


class VoiceInputStatus(StrEnum):
    UNAVAILABLE = "unavailable"
    MODEL_MISSING = "model_missing"
    DEPENDENCY_MISSING = "dependency_missing"
    MICROPHONE_MISSING = "microphone_missing"
    READY = "ready"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    NO_SPEECH = "no_speech"
    FAILED = "failed"
    BLOCKED_BY_POLICY = "blocked_by_policy"


class VoiceInputMode(StrEnum):
    OFF = "off"
    PUSH_TO_TALK = "push_to_talk"
    SINGLE_UTTERANCE = "single_utterance"
    FUTURE_CONTINUOUS = "future_continuous"


class STTProvider(StrEnum):
    VOSK = "vosk"


class STTProviderStatus(StrEnum):
    DEPENDENCY_MISSING = "dependency_missing"
    MODEL_MISSING = "model_missing"
    READY = "ready"
    FAILED = "failed"


class AudioCaptureStatus(StrEnum):
    DEPENDENCY_MISSING = "dependency_missing"
    MICROPHONE_MISSING = "microphone_missing"
    READY = "ready"
    COMPLETED = "completed"
    NO_SPEECH = "no_speech"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class STTModelInfo:
    provider: STTProvider
    path: str | None
    configured: bool
    valid: bool
    language: str
    required_files_present: tuple[str, ...] = ()
    missing_files: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AudioCaptureConfig:
    sample_rate: int = 16_000
    channels: int = 1
    sample_width: int = 2
    max_capture_seconds: int = 30
    silence_timeout_seconds: float = 3.0
    speech_threshold: int = 350
    device_id: str | int | None = None


@dataclass(frozen=True, slots=True)
class AudioInputDevice:
    device_id: str
    name: str
    channels: int
    default_sample_rate: int
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class CapturedAudio:
    status: AudioCaptureStatus
    pcm_bytes: bytes = b""
    sample_rate: int = 16_000
    channels: int = 1
    sample_width: int = 2
    duration: float = 0.0
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class LocalTranscriptionRequest:
    request_id: str
    parent_request_id: str | None
    language: str
    sample_rate: int
    channels: int
    sample_width: int
    pcm_bytes: bytes
    duration: float = 0.0


@dataclass(frozen=True, slots=True)
class LocalTranscriptionResult:
    request_id: str
    parent_request_id: str | None
    provider_id: str
    status: VoiceInputStatus
    text: str = ""
    confidence: float = 0.0
    duration: float = 0.0
    language: str = "en"
    model_path: str | None = None
    error_code: str | None = None
    started_at: str = ""
    completed_at: str = ""


@dataclass(frozen=True, slots=True)
class VoiceInputSession:
    session_id: str
    request_id: str
    mode: VoiceInputMode
    status: VoiceInputStatus
    started_at: str
    completed_at: str | None = None
    provider_id: str = "vosk"
    capture_adapter_id: str = "sounddevice"
    raw_audio_persisted: bool = False
    transcript_persisted: bool = False
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class VoiceInputAuditEvent:
    event_id: str
    request_id: str
    timestamp: str
    operation: str
    status: str
    provider_id: str
    capture_adapter_id: str
    duration: float
    raw_audio_persisted: bool
    transcript_persisted: bool
    error_code: str | None = None


class STTAdapter(Protocol):
    adapter_id: str
    provider: STTProvider

    def status(self) -> STTProviderStatus: ...
    def model_info(self) -> STTModelInfo: ...
    def transcribe(self, request: LocalTranscriptionRequest) -> LocalTranscriptionResult: ...
    def transcribe_wav(self, path: Path, request_id: str, parent_request_id: str | None = None) -> LocalTranscriptionResult: ...


class AudioCaptureAdapter(Protocol):
    adapter_id: str

    def status(self) -> AudioCaptureStatus: ...
    def devices(self) -> tuple[AudioInputDevice, ...]: ...
    def capture(self, config: AudioCaptureConfig) -> CapturedAudio: ...


class VoskSTTAdapter:
    """Lazy local Vosk recognizer; no network or model download behavior."""

    adapter_id = "offline-stt"
    name = "Vosk offline STT"
    version = "1"
    local = True
    capabilities = ("transcription", "wav", "pcm16")
    supported_languages = ("en", "en-US")
    supported_formats = ("wav", "pcm16")
    provider = STTProvider.VOSK

    def __init__(self, model_path: Path | None, language: str = "en-US") -> None:
        self.model_path = Path(model_path).expanduser().resolve() if model_path else None
        self.language = language
        self._model: Any | None = None

    @property
    def dependency_ready(self) -> bool:
        return importlib.util.find_spec("vosk") is not None

    @property
    def model_ready(self) -> bool:
        return self.model_info().valid

    @property
    def available(self) -> bool:
        return self.dependency_ready and self.model_ready

    def status(self) -> STTProviderStatus:
        if not self.dependency_ready:
            return STTProviderStatus.DEPENDENCY_MISSING
        if not self.model_ready:
            return STTProviderStatus.MODEL_MISSING
        return STTProviderStatus.READY

    def model_info(self) -> STTModelInfo:
        required = ("am/final.mdl", "conf/model.conf")
        present: list[str] = []
        missing: list[str] = []
        if self.model_path and self.model_path.is_dir():
            for relative in required:
                (present if (self.model_path / relative).is_file() else missing).append(relative)
        else:
            missing.extend(required)
        return STTModelInfo(
            self.provider,
            str(self.model_path) if self.model_path else None,
            self.model_path is not None,
            bool(self.model_path and self.model_path.is_dir() and not missing),
            self.language,
            tuple(present),
            tuple(missing),
        )

    def health_check(self) -> dict[str, object]:
        provider_status = self.status()
        return {
            "status": "healthy" if provider_status is STTProviderStatus.READY else "unavailable",
            "provider_status": provider_status.value,
            "engine": self.provider.value,
            "dependency_ready": self.dependency_ready,
            "model_ready": self.model_ready,
            "capture_ready": False,
            "missing_capabilities": tuple(
                item
                for item, ready in (
                    ("vosk_dependency", self.dependency_ready),
                    ("local_stt_model", self.model_ready),
                )
                if not ready
            ),
            "local": True,
        }

    def transcribe(self, request: LocalTranscriptionRequest) -> LocalTranscriptionResult:
        started = _now()
        if self.status() is STTProviderStatus.DEPENDENCY_MISSING:
            return self._failure(request, VoiceInputStatus.UNAVAILABLE, "STT_DEPENDENCY_MISSING", started)
        if self.status() is STTProviderStatus.MODEL_MISSING:
            return self._failure(request, VoiceInputStatus.MODEL_MISSING, "STT_MODEL_MISSING", started)
        if request.channels != 1 or request.sample_width != 2 or request.sample_rate <= 0:
            return self._failure(request, VoiceInputStatus.FAILED, "STT_UNSUPPORTED_AUDIO_FORMAT", started)
        if not request.pcm_bytes:
            return self._failure(request, VoiceInputStatus.NO_SPEECH, "STT_NO_SPEECH", started)
        try:
            vosk = importlib.import_module("vosk")
            if self._model is None:
                try:
                    vosk.SetLogLevel(-1)
                except (AttributeError, TypeError):
                    pass
                self._model = vosk.Model(str(self.model_path))
            recognizer = vosk.KaldiRecognizer(self._model, request.sample_rate)
            if hasattr(recognizer, "SetWords"):
                recognizer.SetWords(True)
            for offset in range(0, len(request.pcm_bytes), 8_000):
                recognizer.AcceptWaveform(request.pcm_bytes[offset:offset + 8_000])
            payload = json.loads(recognizer.FinalResult() or "{}")
            text = " ".join(str(payload.get("text", "")).split())
            words = payload.get("result") if isinstance(payload.get("result"), list) else []
            confidences = [float(item["conf"]) for item in words if isinstance(item, dict) and isinstance(item.get("conf"), (int, float))]
            confidence = sum(confidences) / len(confidences) if confidences else (1.0 if text else 0.0)
            if not text:
                return self._failure(request, VoiceInputStatus.NO_SPEECH, "STT_NO_SPEECH", started)
            return LocalTranscriptionResult(
                request.request_id,
                request.parent_request_id,
                self.adapter_id,
                VoiceInputStatus.COMPLETED,
                text[:4_000],
                min(1.0, max(0.0, confidence)),
                request.duration,
                self.language,
                str(self.model_path),
                started_at=started,
                completed_at=_now(),
            )
        except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError):
            return self._failure(request, VoiceInputStatus.FAILED, "STT_RECOGNIZER_ERROR", started)

    def transcribe_wav(self, path: Path, request_id: str, parent_request_id: str | None = None) -> LocalTranscriptionResult:
        started = _now()
        try:
            with wave.open(str(path), "rb") as source:
                channels = source.getnchannels()
                sample_width = source.getsampwidth()
                sample_rate = source.getframerate()
                frame_count = source.getnframes()
                compression = source.getcomptype()
                if compression != "NONE":
                    raise ValueError("compressed_wav")
                pcm = source.readframes(frame_count)
            request = LocalTranscriptionRequest(
                request_id,
                parent_request_id,
                self.language,
                sample_rate,
                channels,
                sample_width,
                pcm,
                frame_count / max(1, sample_rate),
            )
            return self.transcribe(request)
        except (OSError, wave.Error, EOFError, ValueError):
            placeholder = LocalTranscriptionRequest(request_id, parent_request_id, self.language, 0, 0, 0, b"")
            return self._failure(placeholder, VoiceInputStatus.FAILED, "STT_UNSUPPORTED_AUDIO_FORMAT", started)

    def _failure(self, request: LocalTranscriptionRequest, status: VoiceInputStatus, code: str, started: str) -> LocalTranscriptionResult:
        return LocalTranscriptionResult(
            request.request_id,
            request.parent_request_id,
            self.adapter_id,
            status,
            duration=request.duration,
            language=self.language,
            model_path=str(self.model_path) if self.model_path else None,
            error_code=code,
            started_at=started,
            completed_at=_now(),
        )


class SoundDeviceCaptureAdapter:
    """Explicit, bounded microphone capture using optional sounddevice."""

    adapter_id = "sounddevice"

    @property
    def dependency_ready(self) -> bool:
        return importlib.util.find_spec("sounddevice") is not None

    @property
    def available(self) -> bool:
        return self.status() is AudioCaptureStatus.READY

    def status(self) -> AudioCaptureStatus:
        if not self.dependency_ready:
            return AudioCaptureStatus.DEPENDENCY_MISSING
        try:
            sounddevice = importlib.import_module("sounddevice")
            devices = sounddevice.query_devices()
            if not any(int(item.get("max_input_channels", 0)) > 0 for item in devices):
                return AudioCaptureStatus.MICROPHONE_MISSING
            return AudioCaptureStatus.READY
        except (OSError, RuntimeError, ValueError, TypeError):
            return AudioCaptureStatus.MICROPHONE_MISSING

    def devices(self) -> tuple[AudioInputDevice, ...]:
        if not self.dependency_ready:
            return ()
        try:
            sounddevice = importlib.import_module("sounddevice")
            default_input = sounddevice.default.device[0] if sounddevice.default.device else None
            result = []
            for index, item in enumerate(sounddevice.query_devices()):
                channels = int(item.get("max_input_channels", 0))
                if channels <= 0:
                    continue
                result.append(AudioInputDevice(str(index), str(item.get("name", f"Input {index}"))[:120], channels, int(item.get("default_samplerate", 16_000)), index == default_input))
            return tuple(result)
        except (OSError, RuntimeError, ValueError, TypeError):
            return ()

    def capture(self, config: AudioCaptureConfig) -> CapturedAudio:
        state = self.status()
        if state is not AudioCaptureStatus.READY:
            code = "STT_CAPTURE_DEPENDENCY_MISSING" if state is AudioCaptureStatus.DEPENDENCY_MISSING else "STT_MICROPHONE_MISSING"
            return CapturedAudio(state, error_code=code)
        chunks: queue.Queue[bytes] = queue.Queue()
        captured: list[bytes] = []
        heard_speech = False
        last_speech = 0.0
        started = time.monotonic()

        def callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
            del frames, time_info, status
            chunks.put(bytes(indata))

        try:
            sounddevice = importlib.import_module("sounddevice")
            with sounddevice.RawInputStream(
                samplerate=config.sample_rate,
                blocksize=max(800, config.sample_rate // 10),
                device=config.device_id,
                channels=config.channels,
                dtype="int16",
                callback=callback,
            ):
                while time.monotonic() - started < config.max_capture_seconds:
                    try:
                        chunk = chunks.get(timeout=0.25)
                    except queue.Empty:
                        continue
                    captured.append(chunk)
                    samples = array("h")
                    samples.frombytes(chunk)
                    peak = max((abs(value) for value in samples), default=0)
                    current = time.monotonic()
                    if peak >= config.speech_threshold:
                        heard_speech = True
                        last_speech = current
                    if heard_speech and current - last_speech >= config.silence_timeout_seconds:
                        break
            pcm_bytes = b"".join(captured)
            duration = len(pcm_bytes) / max(1, config.sample_rate * config.channels * config.sample_width)
            if not heard_speech:
                return CapturedAudio(AudioCaptureStatus.NO_SPEECH, duration=duration, error_code="STT_NO_SPEECH")
            return CapturedAudio(AudioCaptureStatus.COMPLETED, pcm_bytes, config.sample_rate, config.channels, config.sample_width, duration)
        except (OSError, RuntimeError, ValueError, TypeError):
            return CapturedAudio(AudioCaptureStatus.FAILED, error_code="STT_CAPTURE_FAILED")


class VoiceInputManager:
    """Coordinates explicit local capture and STT without background listening."""

    def __init__(self, config: object | None, storage_dir: Path | None = None, logger: logging.Logger | None = None, stt_adapter: STTAdapter | None = None, capture_adapter: AudioCaptureAdapter | None = None) -> None:
        self.logger = logger or logging.getLogger("voice_input")
        self.mode = VoiceInputMode.OFF
        self.language = str(getattr(config, "language", "en-US"))
        configured_path = getattr(config, "stt_model_path", None) or os.environ.get("JARVIS_VOSK_MODEL_PATH")
        if not configured_path:
            configured_path = Path(__file__).resolve().parents[1] / "models" / "vosk"
        self.stt_adapter = stt_adapter or VoskSTTAdapter(Path(configured_path), self.language)
        self.capture_adapter = capture_adapter or SoundDeviceCaptureAdapter()
        self.capture_config = AudioCaptureConfig(
            max_capture_seconds=min(60, max(1, int(getattr(config, "max_capture_seconds", 30)))),
            silence_timeout_seconds=min(10.0, max(0.5, float(getattr(config, "silence_timeout_seconds", 3)))),
            device_id=getattr(config, "input_device", None),
        )
        self.audit_retention = min(200, max(1, int(getattr(config, "voice_input_audit_retention", 50))))
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.audit_path = self.storage_dir / "input-audit.json" if self.storage_dir else None
        self.sessions: dict[str, VoiceInputSession] = {}
        self._audit = self._load_audit()

    def status(self) -> dict[str, object]:
        stt_state = self.stt_adapter.status()
        capture_state = self.capture_adapter.status()
        model = self.stt_adapter.model_info()
        return {
            "mode": self.mode.value,
            "provider": STTProvider.VOSK.value,
            "provider_status": stt_state.value,
            "dependency_ready": stt_state is not STTProviderStatus.DEPENDENCY_MISSING,
            "model_ready": model.valid,
            "model_path": model.path,
            "capture_adapter": self.capture_adapter.adapter_id,
            "capture_status": capture_state.value,
            "microphone_available": capture_state is AudioCaptureStatus.READY,
            "stt_available": stt_state is STTProviderStatus.READY,
            "ready": stt_state is STTProviderStatus.READY and capture_state is AudioCaptureStatus.READY,
            "raw_audio_persistence": False,
            "transcript_persistence": False,
            "wake_word": False,
            "continuous_listening": False,
            "audit_events": len(self._audit),
        }

    def listen(self, parent_request_id: str | None = None) -> LocalTranscriptionResult:
        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        started = _now()
        self.sessions[session_id] = VoiceInputSession(session_id, request_id, VoiceInputMode.SINGLE_UTTERANCE, VoiceInputStatus.LISTENING, started)
        capture = self.capture_adapter.capture(self.capture_config)
        if capture.status is not AudioCaptureStatus.COMPLETED:
            status = VoiceInputStatus.NO_SPEECH if capture.status is AudioCaptureStatus.NO_SPEECH else VoiceInputStatus.UNAVAILABLE if capture.status in {AudioCaptureStatus.DEPENDENCY_MISSING, AudioCaptureStatus.MICROPHONE_MISSING} else VoiceInputStatus.FAILED
            result = LocalTranscriptionResult(request_id, parent_request_id, self.stt_adapter.adapter_id, status, duration=capture.duration, language=self.language, error_code=capture.error_code, started_at=started, completed_at=_now())
        else:
            request = LocalTranscriptionRequest(request_id, parent_request_id, self.language, capture.sample_rate, capture.channels, capture.sample_width, capture.pcm_bytes, capture.duration)
            result = self.stt_adapter.transcribe(request)
        self.sessions[session_id] = VoiceInputSession(session_id, request_id, VoiceInputMode.SINGLE_UTTERANCE, result.status, started, _now(), self.stt_adapter.adapter_id, self.capture_adapter.adapter_id, False, False, result.error_code)
        self._record("listen", result)
        return result

    def transcribe_wav(self, path: Path, parent_request_id: str | None = None) -> LocalTranscriptionResult:
        result = self.stt_adapter.transcribe_wav(path, str(uuid.uuid4()), parent_request_id)
        self._record("transcribe_file", result)
        return result

    def devices(self) -> tuple[AudioInputDevice, ...]:
        return self.capture_adapter.devices()

    def audit_events(self) -> tuple[VoiceInputAuditEvent, ...]:
        return tuple(self._audit)

    def _record(self, operation: str, result: LocalTranscriptionResult) -> None:
        self._audit.append(VoiceInputAuditEvent(str(uuid.uuid4()), result.request_id, _now(), operation, result.status.value, result.provider_id, self.capture_adapter.adapter_id, result.duration, False, False, result.error_code))
        self._audit = self._audit[-self.audit_retention:]
        self._persist_audit()

    def _load_audit(self) -> list[VoiceInputAuditEvent]:
        if not self.audit_path:
            return []
        try:
            records = json.loads(self.audit_path.read_text(encoding="utf-8"))
            return [VoiceInputAuditEvent(**item) for item in records[-self.audit_retention:] if isinstance(item, dict)]
        except (OSError, ValueError, TypeError):
            return []

    def _persist_audit(self) -> None:
        if not self.audit_path:
            return
        try:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.audit_path.with_suffix(".tmp")
            temporary.write_text(json.dumps([asdict(item) for item in self._audit], indent=2), encoding="utf-8")
            os.replace(temporary, self.audit_path)
        except OSError:
            self.logger.warning("voice_input_audit_persistence_failed", extra={"event": "voice_input_audit_persistence_failed"})
