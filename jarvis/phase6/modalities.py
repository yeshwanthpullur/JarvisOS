"""Voice and visual adapter selection without hidden capture or persistence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import mimetypes

from .environment import ToolEnvironmentRegistry


@dataclass(frozen=True, slots=True)
class AdapterRoute:
    capability: str; primary: str; backup: str; selected: str; status: str; reason: str; local_only: bool = True


class VoiceAdapterRouter:
    def __init__(self, tools: ToolEnvironmentRegistry) -> None:
        self.tools = tools

    def _available(self, tool_id: str) -> bool:
        item = self.tools.inspect(tool_id)
        return bool(item and item.health_status.value == "ready" and item.detected and item.configured and item.integrated and item.enabled)

    def stt(self) -> AdapterRoute:
        selected = "faster_whisper" if self._available("faster_whisper") else "vosk" if self._available("vosk") else ""
        return AdapterRoute("speech_to_text", "faster_whisper", "vosk", selected, "ready_for_explicit_capture" if selected else "unavailable", "Microphone capture remains explicit push-to-talk; detected adapters without a JARVIS adapter are not selected.")

    def tts(self) -> AdapterRoute:
        selected = "piper" if self._available("piper") else "windows_sapi" if self._available("windows_sapi") else ""
        return AdapterRoute("text_to_speech", "piper", "windows_sapi", selected, "ready" if selected else "unavailable", "Playback remains explicit, interruptible, and governed by Voice Intelligence; detected adapters without a JARVIS adapter are not selected.")

    def status(self) -> dict[str, object]:
        return {"stt": self.stt(), "tts": self.tts(), "wake_enabled": False, "continuous_listening": False, "raw_audio_retained": False, "cloud_upload": False}


@dataclass(frozen=True, slots=True)
class VisualEvidence:
    display_name: str; media_type: str; size_bytes: int; source: str; retained: bool; trusted: bool; provider_route: str; status: str; warning: str = ""


class VisionControlPlane:
    def __init__(self, *, max_size_bytes: int = 15_000_000) -> None:
        self.max_size_bytes = max_size_bytes; self.camera_enabled = False; self.retain_images = False; self.cloud_allowed = False; self.sessions: dict[str, dict[str, object]] = {}; self.audit: list[dict[str, object]] = []

    def inspect(self, path_text: str) -> VisualEvidence:
        path = Path(path_text).expanduser().resolve()
        if not path.is_file():
            return VisualEvidence(path.name[:160], "unknown", 0, "explicit_file", False, False, "none", "blocked", "file_missing")
        size = path.stat().st_size
        mime, _ = mimetypes.guess_type(path.name)
        kind = (mime.split("/", 1)[1] if mime and mime.startswith("image/") else path.suffix.lower().lstrip("."))
        if kind not in {"png", "jpeg", "jpg", "gif", "bmp", "tiff", "webp"}:
            return VisualEvidence(path.name[:160], kind, size, "explicit_file", False, False, "none", "blocked", "unsupported_media")
        if size > self.max_size_bytes:
            return VisualEvidence(path.name[:160], kind, size, "explicit_file", False, False, "none", "blocked", "media_too_large")
        return VisualEvidence(path.name[:160], kind, size, "explicit_file", False, False, "ollama_llava", "ready_for_explicit_analysis", "visual_input_is_untrusted_evidence")

    def camera_start(self) -> str:
        return "Camera start blocked: camera is disabled and requires explicit configuration and per-session approval."

    def status(self) -> dict[str, object]:
        return {"local_only": True, "primary": "ollama_llava", "backup": "florence_2_unconfigured", "ocr_primary": "paddleocr_unconfigured", "ocr_backup": "easyocr_unconfigured", "camera_enabled": self.camera_enabled, "retain_images": self.retain_images, "cloud_processing": self.cloud_allowed, "execution_authority": False}
