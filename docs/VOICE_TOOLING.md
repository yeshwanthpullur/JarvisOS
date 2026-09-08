# Voice Tooling

Phase 6 detection is now connected to dedicated Roadmap Steps 57-62 adapters. STT prefers Faster-Whisper only when its dependency and local model are configured, then falls back once to Vosk. TTS similarly prefers configured Piper and falls back once to Windows SAPI. `voice stt`, `voice tts`, `voice test-input`, `voice test-output`, and privacy-safe session diagnostics never start capture or playback themselves.

Voice remains explicit and local. Faster-Whisper and Piper remain degraded until their local model assets are configured; Vosk and Windows SAPI remain fallbacks. Coqui XTTS is deferred. Detection never starts the microphone, enables a wake word, creates audio files, or authorizes background capture. Only `voice ptt start` opens the configured capture backend, and temporary WAV input is removed after processing or cancellation.
