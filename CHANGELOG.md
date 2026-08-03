# Changelog

## Unreleased - Limitations Review and Safe Fix Pass

- Classified every open limitation with evidence, ownership, blockers, and one primary review category without changing roadmap order.
- Added bounded limitation inspection commands and richer project-status counts with fail-closed register validation.
- Added non-destructive automatic memory lifecycle handling that archives expired records and supersedes exact duplicates without deleting user memory.

## Unreleased - Conversation Intelligence

- Added bounded multi-turn conversation state, topic/entity tracking, follow-up intent, comparison context, reference resolution, confidence, and single-question clarification.
- Added conversation repair, interruption-aware topic changes, bounded summaries, and normal/teaching/discussion/brainstorming/debugging/project/interview modes.
- Added `conversation status`, `conversation reset`, `conversation summary`, `conversation mode`, `conversation confidence`, and `conversation topic`.
- Kept persistent memory authoritative and explicit, reused the same path for voice transcripts, and retained only bounded in-memory conversation context.

## Unreleased - Persistent Local Memory Intelligence

- Added local memory intelligence with explicit memory commands, bounded retrieval, and safe auto-session summaries.
- Wired persistent memory context into normal chat so approved local preferences and project notes can reappear in the conversation flow.
- Kept memory storage local-only, secret-aware, and bounded by explicit configuration.

## Unreleased - Verified Local Capability Status

- Recorded real local Ollama free-form chat, Vosk microphone input with an Indian-English model, and `voice listen send` as manually verified.
- Recorded local Ollama LLaVA image analysis and image question answering as manually verified.
- Recorded non-blocking Windows SAPI long-response playback with stop, resume, cancel, interrupt, repeat, and replay controls.
- Updated project health to 74% readiness and the limitations register to 46 total, 20 fixed, and 26 still open without changing the roadmap.

## Unreleased - Real Local Vision Model Integration

- Added configured local Ollama vision-model discovery and real image request execution through the existing Provider Router.
- Added `vision models`, `vision analyze`, `vision audit`, and `vision cleanup` alongside updated status, describe, and ask behavior.
- Added bounded metadata-only vision audit, timeout/error normalization, and policy blocks for identity recognition, sensitive-trait inference, medical diagnosis, and legal/forensic certainty.
- Kept Vercel status-only and retained no image bytes, base64 payloads, prompts, or absolute paths.

## Unreleased - Local Vosk STT Foundation

- Added lazy optional Vosk transcription with validated local model discovery and normalized results.
- Added explicit in-memory `sounddevice` microphone capture with bounded duration and silence handling.
- Added `voice input test` and explicit `voice listen send` handoff through the existing conversation path.
- Kept microphone input, wake word, and continuous listening off by default; no captured PCM or transcript text is persisted.

## Unreleased - Mobile Automation Foundation

- Added a provider-neutral, planning-only Mobile Automation Manager with null and planning adapters.
- Added strict policy blocks for private phone data, communication, sensors, input, apps, settings, purchases, authentication, unlock, and background monitoring.
- Added concise mobile CLI commands and bounded redacted audit records without live phone access.

All notable verified changes to JARVIS OS are recorded here. Unreleased architecture or planned work belongs in `docs/ROADMAP.md`, not in release history.

## Unreleased

### Added

- Central master use-cases and product-vision document with long-term capability, safety, completion, and milestone ownership rules.
- Roadmap alignment through Prompt 50 for mobile, STT, vision, study/research, builder, hardware, media, sync, voice, web interaction, communication, workspace, and v1.0 hardening.
- Standard-library read-only public page inspection with title, description, status, content type, byte count, redirect summary, and sanitized text preview.
- DNS/IP SSRF protection and per-redirect URL revalidation with bounded timeout, redirect, response, and preview limits.
- Provider-neutral Web Automation foundation with strict URL policy, scoped permissions, normalized results, bounded redacted audit, and CLI status/read-only commands.
- Truthful unavailable browser adapter so startup and CLI remain healthy without a browser runtime.

### Security

- Credential-bearing, local/internal, unsafe-scheme, and policy-sensitive URLs are rejected.
- Click, type, submit, download, upload, login, purchase, message, delete, and account-change actions are blocked before adapter dispatch.

- Added an evidence-backed limitations register covering Prompts 27 through 33, with internally checked fixed, open, deferred, blocked, and experimental counts.
- Added concise limitation totals to `project status` and consolidated safe local STT and vision setup guidance.
- Corrected stale tracking language so the working local sync queue is distinguished from unavailable encrypted remote synchronization.

### Changed

- Added the disabled-by-default Online Sync foundation with a bounded atomic local queue, summary allowlists, deduplication, conflicts, retention, and manual CLI controls.
- Added provider-neutral sync adapters while keeping remote synchronization truthfully unavailable until authenticated encrypted infrastructure is configured.
- Isolated Vercel deployment from the root CLI launcher with a status-only Python function and explicit build routes.
- Added safe root, `/api/health`, and `/api/status` responses without exposing local runtime state or secrets.
- Verified both connected Vercel projects reached Ready; the canonical `jarvis-os` status endpoint returned the expected bounded JSON.
- Made direct Windows SAPI playback the default for normal and automatic speech; permanent audio now requires an explicit output path.
- Added clear CLI voice input/STT/microphone/storage status, safe input enable/disable behavior, and `voice cleanup`.
- Added bounded temporary-audio retention and local discovery metadata for Vosk, faster-whisper, and configured whisper.cpp-style runtimes.
- Added Vision Intelligence foundation with safe image validation, metadata extraction, CLI commands, local-only enforcement, and Provider Router integration.
- Added evidence-based Ollama vision capability discovery without changing the existing text model.

### Security

- Sync rejects credentials, secret-shaped values, absolute local paths, raw/binary file content, unsupported fields, oversized payloads, and uncontrolled nesting before queueing and again before transmission.
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
