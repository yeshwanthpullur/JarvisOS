# Voice Tooling

Phase 6 adapter routing prefers Faster-Whisper and Piper only when detected in their isolated environment, with Vosk and Windows SAPI as existing local fallbacks. `voice stt`, `voice tts`, `voice test-input`, `voice test-output`, and privacy-safe session diagnostics never start capture or playback themselves.

Voice remains explicit and local. Faster-Whisper and Piper are optional isolated primary candidates; Vosk and Windows SAPI remain verified fallbacks. Coqui XTTS is deferred to a compatible Python 3.11 environment. Detection never starts the microphone, enables a wake word, creates audio files, or authorizes background capture.
