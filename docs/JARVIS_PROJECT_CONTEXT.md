# JARVIS Project Context

JARVIS OS is a local-first, CLI-primary assistant. The authoritative runtime chain is Conversation/Command routing, Prime or the owning subsystem, Execution Policy, explicit Approval, Execution Broker, Governance, audit, and Reliability. Adapters may inspect, plan, diagnose, and hand off exact work; they do not grant authority.

## Current Checkpoint

Phase 6 Prompts 86-100 are implemented through final validation. The local core uses Ollama, Windows SAPI playback, LLaVA still-image analysis, persistent local Memory, and the Phase 3-5 control planes. The existing Vosk push-to-talk workflow remains configured but is currently degraded because its packages are detected only outside the core environment. Vercel remains status-only.

Optional Phase 6 tools are discovered from isolated environments or tool-managed installs without activation. Status separates detected, configured, integrated, enabled, and execution-authorized. Faster-Whisper, Piper, Aider, Open Interpreter, Browser Use, Playwright, Crawl4AI, Firecrawl, Docling, Marker, vector/memory libraries, runtime frameworks, Agent Reach, Hermes, GitHub CLI, and mcporter may be detected while still disabled for JARVIS execution.

Playwright MCP is the sole configured MCP server. It uses an already cached package through the official Python MCP SDK, starts with an isolated headless browser context, and is trusted only for discovery. Discovered tools do not become trusted or executable. Normal free-form conversation uses the original user input for planning classification and the configured local provider policy for genuine plans.

## Safety Boundary

No hidden microphone/camera use, wake word, continuous listening, silent memory write, cloud fallback, arbitrary shell, unrestricted file/browser/coding action, connector send, plugin load, MCP tool call, model download, telemetry upload, or privileged recovery is enabled. MCP discovery is explicit and bounded; the server is stopped on shutdown. `.env`, credentials, models, runtime data, logs, caches, and generated artifacts stay outside Git.

## Continuation

Phase 7 has not started. Future work requires explicit authorization and must preserve roadmap order and all existing authority boundaries.
