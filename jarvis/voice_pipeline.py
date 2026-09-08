"""Provider-neutral local voice routing and explicit push-to-talk capture."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
import importlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import threading
import time
import wave
from typing import Callable, Protocol
from uuid import uuid4

from jarvis.stt_intelligence import LocalTranscriptionResult, VoiceInputStatus
from jarvis.voice_intelligence import SpeechSynthesisRequest, SpeechSynthesisResult, TranscriptionRequest, TranscriptionResult, VoiceStatus


def _now() -> str:
    return datetime.now(UTC).isoformat()


class PipelineState(StrEnum):
    READY = "ready"; DEGRADED = "degraded"; UNAVAILABLE = "unavailable"; FAILED = "failed"


class PTTState(StrEnum):
    IDLE = "idle"; CAPTURING = "capturing"; PROCESSING_AUDIO = "processing_audio"; TRANSCRIBING = "transcribing"
    THINKING = "thinking"; SYNTHESIZING = "synthesizing"; READY_TO_PLAY = "ready_to_play"; PLAYING = "playing"
    CANCELLED = "cancelled"; FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SpeechSegment:
    text: str; start: float | None = None; end: float | None = None; confidence: float | None = None


@dataclass(frozen=True, slots=True)
class VoiceInput:
    request_id: str; source_type: str; audio_format: str; sample_rate: int; channels: int; duration: float
    audio_reference: str = ""; privacy_class: str = "private"; created_at: str = field(default_factory=_now)


@dataclass(frozen=True, slots=True)
class AudioFrame:
    sequence: int; byte_count: int; sample_rate: int; channels: int; captured_at: str = field(default_factory=_now)


@dataclass(frozen=True, slots=True)
class AudioReference:
    reference_id: str; format: str; sample_rate: int; channels: int; duration: float; byte_count: int; temporary: bool = True


@dataclass(frozen=True, slots=True)
class VoiceCommand:
    request_id: str; transcript: str; route: str = "normal_jarvis_request"; approval_bypass: bool = False


@dataclass(frozen=True, slots=True)
class VoiceResponse:
    request_id: str; text: str; synthesis_reference: str = ""; authority_path: str = "executive_jarvis"; persistent_memory_write: bool = False


@dataclass(frozen=True, slots=True)
class VoiceBackendStatus:
    backend_id: str; state: PipelineState; local: bool; available: bool; healthy: bool; model: str = ""; device: str = ""
    compute_type: str = ""; language_support: tuple[str, ...] = (); reason: str = ""


def _safe_wav(path: Path, *, max_bytes: int, max_seconds: int) -> tuple[int, int, int, float, bytes]:
    if path.suffix.lower() != ".wav" or not path.is_file():
        raise ValueError("audio_format_invalid")
    if path.stat().st_size > max_bytes:
        raise ValueError("audio_too_large")
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels(); width = source.getsampwidth(); rate = source.getframerate(); frames = source.getnframes()
            if source.getcomptype() != "NONE" or channels not in {1, 2} or width != 2 or rate <= 0:
                raise ValueError("audio_format_invalid")
            pcm = source.readframes(frames)
    except (OSError, EOFError, wave.Error):
        raise ValueError("audio_format_invalid") from None
    duration = frames / max(1, rate)
    if duration > max_seconds:
        raise ValueError("audio_too_long")
    return rate, channels, width, duration, pcm


class FasterWhisperAdapter:
    adapter_id = "faster-whisper"; name = "Faster-Whisper"; version = "foundation-1"; local = True
    capabilities = ("transcription", "wav", "segments", "language_detection", "vad")
    supported_languages = ("auto", "en"); supported_formats = ("wav",)

    def __init__(self, model_path: Path | None = None, *, device: str = "cpu", compute_type: str = "int8", transcriber: Callable[[Path, str], object] | None = None, max_audio_bytes: int = 20_000_000, max_audio_seconds: int = 300) -> None:
        self.model_path = Path(model_path).expanduser().resolve() if model_path else None
        self.device = device; self.compute_type = compute_type; self.transcriber = transcriber
        self.max_audio_bytes = max_audio_bytes; self.max_audio_seconds = max_audio_seconds; self._cancelled = threading.Event()

    @property
    def dependency_ready(self) -> bool:
        return importlib.util.find_spec("faster_whisper") is not None

    @property
    def model_ready(self) -> bool:
        return bool(self.transcriber or self.model_path and self.model_path.exists())

    @property
    def available(self) -> bool:
        return bool(self.transcriber or self.dependency_ready and self.model_ready)

    def detect(self) -> VoiceBackendStatus:
        reason = "" if self.available else "stt_model_missing" if self.dependency_ready else "dependency_missing"
        return VoiceBackendStatus(self.adapter_id, PipelineState.READY if self.available else PipelineState.DEGRADED, True, self.available, self.available, self.model_path.name if self.model_path else "", self.device, self.compute_type, self.supported_languages, reason)

    def health(self) -> VoiceBackendStatus:
        return self.detect()

    def health_check(self) -> dict[str, object]:
        item = self.detect()
        return {"status": "healthy" if item.healthy else "degraded", "state": item.state.value, "local": True, "model_ready": self.model_ready, "dependency_ready": self.dependency_ready, "reason": item.reason}

    def cancel(self) -> bool:
        self._cancelled.set(); return True

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        started = time.monotonic(); self._cancelled.clear(); path = Path(request.audio_reference)
        try:
            _safe_wav(path, max_bytes=self.max_audio_bytes, max_seconds=self.max_audio_seconds)
        except ValueError as exc:
            return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.INVALID_OUTPUT, errors=(str(exc),), latency=time.monotonic() - started)
        if not self.available:
            return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.UNAVAILABLE, errors=("stt_model_missing",), latency=time.monotonic() - started)
        try:
            if self.transcriber:
                raw = self.transcriber(path, request.language)
            else:
                module = importlib.import_module("faster_whisper")
                model = module.WhisperModel(str(self.model_path), device=self.device, compute_type=self.compute_type)
                segments, info = model.transcribe(str(path), language=None if request.language in {"auto", ""} else request.language, beam_size=1, vad_filter=True)
                raw = {"segments": tuple(segments), "language": getattr(info, "language", request.language)}
            if self._cancelled.is_set():
                return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.CANCELLED, errors=("voice_session_cancelled",), latency=time.monotonic() - started)
            items = tuple(raw.get("segments", ()))[:100] if isinstance(raw, dict) else tuple(raw)[:100]
            text = str(raw.get("text", "")).strip() if isinstance(raw, dict) else ""
            language = str(raw.get("language", request.language)) if isinstance(raw, dict) else request.language
            confidence = raw.get("confidence") if isinstance(raw, dict) else None
            normalized = []
            for item in items:
                value = item if isinstance(item, dict) else {"text": getattr(item, "text", ""), "start": getattr(item, "start", None), "end": getattr(item, "end", None)}
                normalized.append(SpeechSegment(str(value.get("text", "")).strip()[:500], value.get("start"), value.get("end"), value.get("confidence")))
            if not text:
                text = " ".join(item.text for item in normalized).strip()
            model_name = self.model_path.name if self.model_path else "fixture"
            if not text:
                return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.NO_SPEECH, language=language, errors=("no_speech",), latency=time.monotonic() - started, model=model_name)
            score = float(confidence) if isinstance(confidence, (int, float)) else 0.0
            return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.COMPLETED, text[:request.maximum_output_length], text[:request.maximum_output_length], language, max(0, min(1, score)), tuple({"text": item.text, "start": item.start, "end": item.end, "confidence": item.confidence} for item in normalized), latency=time.monotonic() - started, model=model_name)
        except TimeoutError:
            return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.TIMED_OUT, errors=("stt_timeout",), latency=time.monotonic() - started)
        except (OSError, RuntimeError, ValueError, TypeError):
            return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.FAILED, errors=("stt_failed",), latency=time.monotonic() - started)


class VoskCanonicalAdapter:
    adapter_id = "offline-stt"

    def __init__(self, adapter: object) -> None:
        self.adapter = adapter

    @property
    def available(self) -> bool:
        return bool(getattr(self.adapter, "available", False))

    def detect(self) -> VoiceBackendStatus:
        info = self.adapter.model_info()
        return VoiceBackendStatus(self.adapter_id, PipelineState.READY if self.available else PipelineState.DEGRADED, True, self.available, self.available, Path(info.path).name if info.path else "", "cpu", "int16", (info.language,), "" if self.available else self.adapter.status().value)

    def health(self) -> VoiceBackendStatus:
        return self.detect()

    def health_check(self) -> dict[str, object]:
        item = self.detect()
        return {"status": "healthy" if item.healthy else "degraded", "state": item.state.value, "local": True, "model_ready": item.available, "dependency_ready": item.available, "reason": item.reason}

    def cancel(self) -> bool:
        return True

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        result: LocalTranscriptionResult = self.adapter.transcribe_wav(Path(request.audio_reference), request.transcription_id, request.parent_request_id)
        states = {VoiceInputStatus.COMPLETED: VoiceStatus.COMPLETED, VoiceInputStatus.NO_SPEECH: VoiceStatus.NO_SPEECH, VoiceInputStatus.UNAVAILABLE: VoiceStatus.UNAVAILABLE, VoiceInputStatus.MODEL_MISSING: VoiceStatus.UNAVAILABLE, VoiceInputStatus.DEPENDENCY_MISSING: VoiceStatus.UNAVAILABLE}
        return TranscriptionResult(result.request_id, request.voice_session_id, result.parent_request_id, self.adapter_id, states.get(result.status, VoiceStatus.FAILED), result.text, result.text, result.language, result.confidence, duration=result.duration, errors=(result.error_code,) if result.error_code else (), model=Path(result.model_path).name if result.model_path else "")


class STTRouter:
    def __init__(self, primary: FasterWhisperAdapter, fallback: VoskCanonicalAdapter, max_fallbacks: int = 1) -> None:
        self.primary = primary; self.fallback = fallback; self.max_fallbacks = max(0, min(max_fallbacks, 1)); self.last_route: dict[str, object] = {}

    def route(self, request: TranscriptionRequest) -> TranscriptionResult:
        attempts = []
        for index, adapter in enumerate((self.primary, self.fallback)):
            if index and not self.max_fallbacks: break
            if not adapter.available:
                attempts.append(f"{adapter.adapter_id}:unavailable"); continue
            result = adapter.transcribe(replace(request, backend_id=adapter.adapter_id)); attempts.append(f"{adapter.adapter_id}:{result.status.value}")
            if result.status in {VoiceStatus.COMPLETED, VoiceStatus.NO_SPEECH, VoiceStatus.CANCELLED}:
                self.last_route = {"backend": adapter.adapter_id, "attempts": tuple(attempts), "fallback_used": bool(index)}
                return replace(result, warnings=result.warnings + (("fallback_from_faster_whisper",) if index else ()), fallback_used=bool(index))
        self.last_route = {"backend": "", "attempts": tuple(attempts), "fallback_used": len(attempts) > 1}
        return TranscriptionResult(request.transcription_id, request.voice_session_id, request.parent_request_id, "none", VoiceStatus.UNAVAILABLE, errors=("stt_unavailable",), fallback_used=len(attempts) > 1)

    def status(self) -> dict[str, object]:
        return {"primary": self.primary.detect(), "fallback": self.fallback.detect(), "maximum_fallbacks": self.max_fallbacks, "last_route": self.last_route, "local_only": True}


class PiperAdapter:
    adapter_id = "piper"; name = "Piper TTS"; version = "foundation-1"; local = True
    capabilities = ("synthesis", "wav", "file"); supported_languages = ("configured_voice",); supported_formats = ("wav",)

    def __init__(self, executable: Path | None = None, model_path: Path | None = None, temp_dir: Path | None = None, *, runner: Callable[[str, Path], None] | None = None, max_text_chars: int = 12000) -> None:
        found = str(executable) if executable else shutil.which("piper")
        self.executable = Path(found).resolve() if found else None; self.model_path = Path(model_path).resolve() if model_path else None
        self.temp_dir = (temp_dir or Path("data/voice-temp")).resolve(); self.runner = runner; self.max_text_chars = max(1, min(max_text_chars, 50_000)); self._process = None; self._lock = threading.RLock()

    @property
    def dependency_ready(self) -> bool:
        return bool(self.runner or self.executable and self.executable.is_file())

    @property
    def model_ready(self) -> bool:
        return bool(self.runner or self.model_path and self.model_path.is_file())

    @property
    def available(self) -> bool:
        return self.dependency_ready and self.model_ready

    def detect(self) -> VoiceBackendStatus:
        reason = "" if self.available else "tts_voice_missing" if self.dependency_ready else "dependency_missing"
        return VoiceBackendStatus(self.adapter_id, PipelineState.READY if self.available else PipelineState.DEGRADED, True, self.available, self.available, self.model_path.name if self.model_path else "", "local", "native", self.supported_languages, reason)

    def health(self) -> VoiceBackendStatus:
        return self.detect()

    def health_check(self) -> dict[str, object]:
        item = self.detect()
        return {"status": "healthy" if item.healthy else "degraded", "state": item.state.value, "local": True, "voice_ready": self.model_ready, "dependency_ready": self.dependency_ready, "reason": item.reason}

    def synthesize(self, request: SpeechSynthesisRequest) -> SpeechSynthesisResult:
        started = time.monotonic(); text = " ".join(request.text.split())
        if not text:
            return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.INVALID_OUTPUT, errors=("empty_speech_text",), latency=time.monotonic() - started)
        if len(text) > self.max_text_chars:
            return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.INVALID_OUTPUT, errors=("tts_text_too_large",), latency=time.monotonic() - started)
        if not self.available:
            return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.UNAVAILABLE, errors=(self.detect().reason,), latency=time.monotonic() - started)
        path = Path(request.output_path).resolve() if request.output_path else self.temp_dir / f"speech-{uuid4().hex}.wav"; path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if self.runner:
                self.runner(text, path)
            else:
                process = subprocess.Popen([str(self.executable), "--model", str(self.model_path), "--output_file", str(path)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)); self._process = process
                process.communicate(text, timeout=max(5, min(request.timeout, 120)))
                if process.returncode: raise RuntimeError("piper_failed")
            if not path.is_file() or path.stat().st_size <= 0: raise OSError("audio_file_not_created")
            return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.COMPLETED, str(path), "file", audio_size=path.stat().st_size, audio_format="wav", voice_id=self.model_path.name if self.model_path else "fixture", latency=time.monotonic() - started)
        except subprocess.TimeoutExpired:
            self.cancel(); return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.TIMED_OUT, errors=("tts_timeout",), latency=time.monotonic() - started)
        except (OSError, RuntimeError, ValueError):
            return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, self.adapter_id, VoiceStatus.FAILED, errors=("tts_failed",), latency=time.monotonic() - started)
        finally:
            self._process = None

    def cancel(self) -> bool:
        with self._lock: process = self._process
        if process is None or process.poll() is not None: return False
        try: process.terminate(); return True
        except OSError: return False

    @staticmethod
    def cleanup(reference: str | None) -> bool:
        if not reference: return False
        try: Path(reference).unlink(missing_ok=True); return True
        except OSError: return False


class TTSRouter:
    def __init__(self, primary: PiperAdapter, fallback: object, max_fallbacks: int = 1) -> None:
        self.primary = primary; self.fallback = fallback; self.max_fallbacks = max(0, min(max_fallbacks, 1)); self.last_route: dict[str, object] = {}

    def route(self, request: SpeechSynthesisRequest) -> SpeechSynthesisResult:
        attempts = []
        for index, adapter in enumerate((self.primary, self.fallback)):
            if index and not self.max_fallbacks: break
            if not bool(getattr(adapter, "available", False)):
                attempts.append(f"{adapter.adapter_id}:unavailable"); continue
            result = adapter.synthesize(replace(request, backend_id=adapter.adapter_id)); attempts.append(f"{adapter.adapter_id}:{result.status.value}")
            if result.status is VoiceStatus.COMPLETED:
                self.last_route = {"backend": adapter.adapter_id, "attempts": tuple(attempts), "fallback_used": bool(index)}
                return replace(result, warnings=result.warnings + (("fallback_from_piper",) if index else ()), fallback_used=bool(index))
        self.last_route = {"backend": "", "attempts": tuple(attempts), "fallback_used": len(attempts) > 1}
        return SpeechSynthesisResult(request.synthesis_id, request.voice_session_id, request.parent_request_id, "none", VoiceStatus.UNAVAILABLE, errors=("tts_unavailable",), fallback_used=len(attempts) > 1)

    def status(self) -> dict[str, object]:
        return {"primary": self.primary.detect(), "fallback": self.fallback.health_check(), "maximum_fallbacks": self.max_fallbacks, "last_route": self.last_route, "local_only": True}


class PTTCaptureBackend(Protocol):
    adapter_id: str
    def status(self) -> str: ...
    def start(self, callback: Callable[[bytes], None], sample_rate: int, channels: int) -> None: ...
    def stop(self) -> None: ...


class SoundDevicePTTBackend:
    adapter_id = "sounddevice-ptt"

    def __init__(self) -> None:
        self._stream = None

    def status(self) -> str:
        if importlib.util.find_spec("sounddevice") is None: return "dependency_missing"
        try: return "ready" if any(int(item.get("max_input_channels", 0)) > 0 for item in importlib.import_module("sounddevice").query_devices()) else "microphone_unavailable"
        except (OSError, RuntimeError, ValueError, TypeError): return "microphone_unavailable"

    def start(self, callback: Callable[[bytes], None], sample_rate: int, channels: int) -> None:
        if self.status() != "ready": raise RuntimeError("microphone_unavailable")
        module = importlib.import_module("sounddevice")
        self._stream = module.RawInputStream(samplerate=sample_rate, channels=channels, dtype="int16", callback=lambda data, frames, time_info, status: callback(bytes(data)))
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop(); self._stream.close(); self._stream = None


@dataclass(frozen=True, slots=True)
class PTTSession:
    session_id: str; state: PTTState; sample_rate: int = 16000; channels: int = 1; byte_count: int = 0; duration: float = 0
    audio_reference: str = ""; transcript_status: str = ""; stt_backend: str = ""; tts_backend: str = ""; fallback_used: bool = False
    last_error: str = ""; started_at: str = field(default_factory=_now); updated_at: str = field(default_factory=_now)


class PushToTalkController:
    def __init__(self, stt: STTRouter, tts: TTSRouter, temp_dir: Path, *, backend: PTTCaptureBackend | None = None, max_recording_seconds: int = 30, max_audio_bytes: int = 20_000_000) -> None:
        self.stt = stt; self.tts = tts; self.temp_dir = temp_dir.resolve(); self.backend = backend or SoundDevicePTTBackend()
        self.max_recording_seconds = max(1, min(max_recording_seconds, 120)); self.max_audio_bytes = max(1024, min(max_audio_bytes, 100_000_000))
        self.session = PTTSession("", PTTState.IDLE); self._buffer = bytearray(); self._lock = threading.RLock(); self._started_monotonic = 0.0

    def _audio(self, data: bytes) -> None:
        with self._lock:
            if self.session.state is not PTTState.CAPTURING: return
            elapsed = time.monotonic() - self._started_monotonic
            if elapsed > self.max_recording_seconds or len(self._buffer) + len(data) > self.max_audio_bytes:
                self.session = replace(self.session, state=PTTState.FAILED, last_error="audio_limit_exceeded", updated_at=_now()); self.backend.stop(); return
            self._buffer.extend(data)
            self.session = replace(self.session, byte_count=len(self._buffer), duration=len(self._buffer) / max(1, self.session.sample_rate * self.session.channels * 2), updated_at=_now())

    def start_capture(self) -> PTTSession:
        with self._lock:
            if self.session.state is not PTTState.IDLE: raise ValueError("capture_already_active")
            self._buffer = bytearray(); self.session = PTTSession(f"ptt-{uuid4().hex[:12]}", PTTState.CAPTURING); self._started_monotonic = time.monotonic()
            try: self.backend.start(self._audio, self.session.sample_rate, self.session.channels)
            except (OSError, RuntimeError, ValueError):
                self.session = replace(self.session, state=PTTState.FAILED, last_error="microphone_unavailable", updated_at=_now()); raise ValueError("microphone_unavailable") from None
            return self.session

    def stop_capture(self) -> PTTSession:
        with self._lock:
            if self.session.state is not PTTState.CAPTURING: raise ValueError("capture_not_active")
            self.backend.stop(); data = bytes(self._buffer)
            if not data:
                self.session = replace(self.session, state=PTTState.FAILED, last_error="no_speech", updated_at=_now()); return self.session
            self.temp_dir.mkdir(parents=True, exist_ok=True); path = self.temp_dir / f"ptt-{uuid4().hex}.wav"
            with wave.open(str(path), "wb") as output:
                output.setnchannels(self.session.channels); output.setsampwidth(2); output.setframerate(self.session.sample_rate); output.writeframes(data)
            self.session = replace(self.session, state=PTTState.PROCESSING_AUDIO, byte_count=len(data), duration=len(data) / max(1, self.session.sample_rate * self.session.channels * 2), audio_reference=str(path), updated_at=_now())
            return self.session

    def process_capture(self, dispatcher: Callable[[str], object] | None = None, *, synthesize: bool = False) -> tuple[PTTSession, TranscriptionResult, object | None]:
        if self.session.state is not PTTState.PROCESSING_AUDIO: raise ValueError("capture_not_ready")
        self.session = replace(self.session, state=PTTState.TRANSCRIBING, updated_at=_now())
        request = TranscriptionRequest(f"stt-{uuid4().hex[:12]}", self.session.session_id, None, self.session.audio_reference, "router")
        result = self.stt.route(request); response = None
        if result.status is not VoiceStatus.COMPLETED:
            self._finish(PTTState.FAILED, result.errors[0] if result.errors else "stt_failed"); return self.session, result, None
        self.session = replace(self.session, state=PTTState.THINKING, transcript_status="session_context_only", stt_backend=result.backend_id, fallback_used=result.fallback_used, updated_at=_now())
        if dispatcher is not None: response = dispatcher(result.text)
        if synthesize and response is not None:
            self.session = replace(self.session, state=PTTState.SYNTHESIZING, updated_at=_now()); text = str(getattr(response, "response", response))
            output_path = self.temp_dir / f"response-{uuid4().hex}.wav"
            synth = self.tts.route(SpeechSynthesisRequest(f"tts-{uuid4().hex[:12]}", self.session.session_id, None, "router", text, output_mode="file", output_path=str(output_path)))
            self.session = replace(self.session, state=PTTState.READY_TO_PLAY if synth.status is VoiceStatus.COMPLETED else PTTState.FAILED, tts_backend=synth.backend_id, last_error="" if synth.status is VoiceStatus.COMPLETED else synth.errors[0], updated_at=_now())
        else:
            self.session = replace(self.session, state=PTTState.READY_TO_PLAY, updated_at=_now())
        self._cleanup_capture(); return self.session, result, response

    def cancel_capture(self) -> PTTSession:
        if self.session.state is PTTState.IDLE: return self.session
        try: self.backend.stop()
        except (OSError, RuntimeError): pass
        self.stt.primary.cancel(); self.stt.fallback.cancel(); self.tts.primary.cancel(); self._finish(PTTState.CANCELLED, "voice_session_cancelled"); return self.session

    def reset(self) -> PTTSession:
        self._cleanup_capture(); self._buffer = bytearray(); self.session = PTTSession("", PTTState.IDLE); return self.session

    def recover_after_restart(self) -> PTTSession:
        return self.reset()

    def _finish(self, state: PTTState, error: str = "") -> None:
        self.session = replace(self.session, state=state, last_error=error, updated_at=_now()); self._cleanup_capture()

    def _cleanup_capture(self) -> None:
        if self.session.audio_reference:
            try: Path(self.session.audio_reference).unlink(missing_ok=True)
            except OSError: pass

    def status(self) -> dict[str, object]:
        return {"state": self.session.state.value, "capturing": self.session.state is PTTState.CAPTURING, "session_id": self.session.session_id, "audio_bytes": self.session.byte_count, "duration": self.session.duration, "backend": self.backend.adapter_id, "backend_status": self.backend.status(), "stt_backend": self.session.stt_backend, "tts_backend": self.session.tts_backend, "fallback_used": self.session.fallback_used, "last_error": self.session.last_error, "raw_audio_persistence": False, "transcript_persistence": False, "wake_word": False, "continuous_listening": False}

    def checkpoint_metadata(self) -> dict[str, object]:
        return {"session_id": self.session.session_id, "state": self.session.state.value, "stt_backend": self.session.stt_backend, "tts_backend": self.session.tts_backend, "last_error": self.session.last_error, "raw_audio": False, "transcript": False}
