# Changelog

All notable verified changes to JARVIS OS are recorded here. Unreleased architecture or planned work belongs in `docs/ROADMAP.md`, not in release history.

## Unreleased

### Changed

- Isolated Vercel deployment from the root CLI launcher with a status-only Python function and explicit build routes.
- Added safe root, `/api/health`, and `/api/status` responses without exposing local runtime state or secrets.
- Verified both connected Vercel projects reached Ready; the canonical `jarvis-os` status endpoint returned the expected bounded JSON.
- Made direct Windows SAPI playback the default for normal and automatic speech; permanent audio now requires an explicit output path.
- Added clear CLI voice input/STT/microphone/storage status, safe input enable/disable behavior, and `voice cleanup`.
- Added bounded temporary-audio retention and local discovery metadata for Vosk, faster-whisper, and configured whisper.cpp-style runtimes.
- Added Vision Intelligence foundation with safe image validation, metadata extraction, CLI commands, local-only enforcement, and Provider Router integration.
- Added evidence-based Ollama vision capability discovery without changing the existing text model.

### Security

- Raw microphone audio remains non-persistent by default, temporary audio stays scoped to the configured directory, and no cloud speech fallback is permitted.

## v0.3.0-alpha - Local Voice and CLI Stability (2026-07-31)

### Added

- Real local Ollama chat through the Provider Execution Framework and Provider Router.
- Local-only execution enforcement and explicit local-model selection.
- Governed Tool Intelligence, Autonomous Planning, and Multi-Agent foundations.
- Windows SAPI voice playback with `voice status`, `voice output on/off`, and `voice say <text>`.
- Safe automatic spoken assistant replies when voice output is enabled.
- Localhost desktop web interface as an optional experimental surface.

### Changed

- Made `python main.py` the stable primary user mode.
- Simplified startup status and focused CLI command help.
- Kept non-debug internal INFO logs out of the conversation console.
- Kept sensitive content, credentials, code blocks, warnings, and failed responses text-only.

### Verified

- Full suite: 1,374 passed, 0 skipped, 0 failed, 0 errors.
- Focused CLI/voice/command/plugin suite: 139 passed.
- Real Ollama chat, local-only routing, explicit SAPI playback, automatic reply playback, and `git diff --check` passed.

### Known Limitations

- The web interface is experimental and may feel jerky or laggy.
- SAPI playback is synchronous.
- Offline speech recognition requires a separately configured local STT model.
- Vision, online sync, web automation, and mobile automation are not included.
