# Post-Phase-6 Runtime Repair

Date: 2026-08-19

Status: verified locally. This work is not Phase 7 and creates no tag, release, push, or deployment.

## Repairs

- Free-form routing classifies the original user input rather than conversation-enriched provider text. Ordinary capability questions therefore stay on the conversation path, while genuine planning requests remain validated plans.
- Genuine planning requests inherit the configured permitted provider and local-only policy instead of selecting an enabled but unconfigured provider.
- Planner failures use bounded normalized provider diagnostics, and malformed provider output is rejected without bypassing validation.
- MCP local stdio uses the pinned official Python SDK for initialization, discovery, resource reads, optional prompt discovery, guarded tool calls, timeout handling, and clean shutdown.
- Playwright MCP is configured with an isolated headless browser context and discovery-only trust. Its cached package may be resolved without invoking npm installation. The verified discovery returned 24 tools; zero are trusted or enabled, and global MCP tool execution remains disabled.
- MCP session wiring makes `mcp start` perform handshake plus discovery and retain classified metadata for subsequent inspection commands. Explicit `mcp discover` remains a safe refresh, and bounded history records both operations.
- Tool inventory distinguishes installed, detected, configured, integrated, enabled, and execution-authorized states. Discovery does not activate an isolated environment or grant authority.
- Voice diagnostics report Windows SAPI ready, Vosk degraded when available only outside the core interpreter, and detected Faster-Whisper/Piper adapters disabled until dedicated integrations exist.

## Authority And Privacy

Prime, Executive JARVIS, Execution Policy, Approval, Execution Broker, Governance, Workflow, provider policy, and explicit user approval remain authoritative. MCP uses no shell evaluation, arbitrary executable, automatic package installation, remote HTTP, scheduled execution, logged-in browser profile, or automatic trust. No hidden microphone use, continuous listening, wake word, cloud fallback, secret output, private-path output, or persistent audio was enabled.

## Manual Acceptance

The normal `main.py` startup path accepted `hi`, answered a five-bullet capability request through local Ollama, returned bounded project/provider/runtime diagnostics, completed Playwright MCP discovery, listed all discovered tools as untrusted and disabled, reported current voice states truthfully, and shut down cleanly. Playwright discovery was verified as `registered=yes`, `discovery=yes`, `tool_execution=no`.

## Verification

- Focused routing, provider, Prime/Executive, MCP, environment, document, memory, coding, research, and playback-control tests: 318 passed, 0 skipped, 0 failed, 0 errors.
- Documentation and tracking consistency tests: 43 passed, 0 skipped, 0 failed, 0 errors.
- Full suite: 2,137 passed, 0 skipped, 0 failed, 0 errors in 355.299 seconds.
- Official-SDK fixture tests covered initialization, discovery, resources, guarded calls, malformed transport handling, and shutdown.
- Configuration, JSON, dependency, documentation/tracking, secret, runtime-artifact, absolute-path, compilation, and `git diff --check` gates are closing requirements for this repair.

## Current Degradations

- Vosk and `sounddevice` are detected in an isolated voice environment but are not importable by the core in-process adapter, so explicit microphone STT is currently unavailable from this core environment.
- Faster-Whisper and Piper are installed but have no enabled JARVIS adapters.
- Optional browser, research, document, memory, coding, runtime, and external-agent packages may be detected without being configured, integrated, enabled, trusted, or execution-authorized.
- Exa and other credential-dependent external services are not activated or claimed as verified by this repair.
