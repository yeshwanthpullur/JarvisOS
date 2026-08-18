# JARVIS Project Context

JARVIS OS is a local-first, CLI-primary assistant. The authoritative runtime chain is Conversation/Command routing, Prime or the owning subsystem, Execution Policy, explicit Approval, Execution Broker, Governance, audit, and Reliability. Adapters may inspect, plan, diagnose, and hand off exact work; they do not grant authority.

## Current Checkpoint

Phase 6 Prompts 86-100 are implemented through final validation. The local core uses Ollama, existing Vosk push-to-talk, Windows SAPI playback, LLaVA still-image analysis, persistent local Memory, and the Phase 3-5 control planes. Vercel remains status-only.

Optional Phase 6 tools are isolated and disabled unless separately configured. Rich document/OCR tooling, semantic vector/graph backends, Faster-Whisper, Piper, Aider, Open Interpreter, interactive browser tooling, external connectors, MCP servers, plugins, and cloud providers may be detected but are not automatically installed, enabled, authenticated, or executed.

## Safety Boundary

No hidden microphone/camera use, wake word, continuous listening, silent memory write, cloud fallback, arbitrary shell, unrestricted file/browser/coding action, connector send, plugin load, MCP start, model download, telemetry upload, or privileged recovery is enabled. `.env`, credentials, models, runtime data, logs, caches, and generated artifacts stay outside Git.

## Continuation

Phase 7 has not started. Future work requires explicit authorization and must preserve roadmap order and all existing authority boundaries.
