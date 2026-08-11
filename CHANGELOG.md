# Changelog

## Unreleased - Prompt 74 Outbound Connectors

- Added outbound-only Discord, email, and Slack text connectors with bounded health, rate limits, duplicate checks, and metadata-only history.
- Added provider CLI/config, routing, policy actions, and approval-gated Broker tools.
- Defaults stay off; inbound access, attachments, bulk/scheduled sends, webhooks, enumeration, and credential output stay disabled.

## Unreleased - Prompt 73 Secure Telegram Connector

- Added text-only Telegram Bot API transport, identity validation, private-owner pairing, authorization, replay protection, explicit polling lifecycle, message chunking, rate limits, and metadata-only observability.
- Added bounded `telegram` CLI controls plus Prime, Communication, Agent, Skill, Execution Policy, Approval, and Broker integration.
- Independent sends require exact approval and Broker dispatch. The connector is disabled and unconfigured by default; attachments, voice, groups, channels, webhook, scheduled sends, and permanent daemons remain disabled.

## Unreleased - Prompt 72 External Communication Provider Foundation

- Added provider-neutral communication profiles, destination validation, message planning/validation models, attachment policy, outbound rate metadata, duplicate protection, and bounded CLI diagnostics.
- Preserved strict draft/send separation and Phase 4 Approval/Broker authority. No external provider, contact discovery, upload, bulk send, scheduled send, or real message delivery is enabled.

## Unreleased - Prompt 71 External Integration Control Plane

### Added

- Added typed external-provider, capability, health, policy, action, route, cost, and data-egress models.
- Added a central metadata-only registry for communication, GitHub, model, MCP, and plugin placeholders plus bounded CLI diagnostics.
- Added credential-reference-only reporting, shared redaction, endpoint validation, health caching, and local-first non-executing route policy.

### Safety

- Every external provider remains disabled and unconfigured; paid/cloud execution, MCP, plugins, sending, remote GitHub actions, and remote models remain unavailable.
- Phase 4 approvals, Execution Policy, and Broker remain authoritative. No credentials are read and no network calls occur.

## Unreleased - Prompt 85 Production-Readiness Validation

### Added

- Added typed release gates, system authority contracts, a blocked release-candidate model, and deterministic Phase 5 prerequisite detection.
- Added bounded `release-readiness` CLI diagnostics and safe release-validation configuration with tag, release, and deployment actions disabled.
- Added production-readiness and operations documentation.

### Status

- Prompt 85 validation is implemented, but Phase 5 readiness is blocked because Prompts 71-84 remain unimplemented specifications.
- No provider, MCP, plugin, governance, reliability, or workflow capability was fabricated; no tag or release was created.

## Unreleased - Phase 4 Controlled Execution Foundation

### Added

- Added bounded approval lifecycle, exact authorization matching, central execution policy, and a controlled execution broker.
- Added workspace-scoped file operations, allowlisted shell-free commands, dedicated approved Git writes, SSRF-protected public-page reads, local console notifications, and a manual-only notification scheduler.
- Added `execution`, `approval`, `broker`, `file-exec`, `command`, `git-exec`, `notification`, browser execution, and scheduler runtime CLI controls.
- Integrated controlled execution metadata with Prime routing, Agent Registry, Skill Registry, configuration, and project status.

### Safety

- Default execution remains `plan_only`; high-risk actions require exact approval and critical actions are blocked.
- Secret access, force-push, arbitrary shells, broad deletion, browser writes, external communication, hidden capture, autonomous workers, and scheduled commands remain unavailable.
- Vercel remains status-only and no executor is exposed online.

### Verification

- Added focused policy, approval, broker, executor, CLI, and cross-system regression coverage. Final totals are recorded after the complete Prompt 70 verification pass.

## Unreleased - Phase 3 Batch 2 Foundations

### Added

- Added typed, bounded Document, Browser, Scheduler, Communication, Adapter, Advanced Model, and Evaluation foundations with complete safe CLI command groups.
- Integrated plan-only specialists with Prime routing, Agent Registry, Skill Registry, Model Router, project status, configuration, and local-only observability.
- Added safe text extraction for explicit bounded local text files, draft-only communication, disabled provider/runtime manifests, recurrence validation, advanced-provider comparisons, and deterministic routing/safety/truthfulness fixtures.

### Safety

- Browser writes, scheduling runtimes, communication sending, MCP/plugin execution, credentials, cloud model use, downloads, runtime startup, telemetry, and remote logging remain disabled.
- Runtime metadata folders remain ignored; no document dumps, cookies, sessions, contacts, tokens, model files, or evaluation logs are committed.

### Verification

- Batch 2 focused integration: 115 passed; tracking and Vercel contracts: 32 passed.
- Full suite: 1,727 passed, 0 skipped, 0 failed, 0 errors.
- Compilation, JSON/docs validation, leakage scans, CLI output bounds, and `git diff --check` passed.

## Unreleased - Coding Agent Foundation

### Added

- Added typed coding tasks, plans, repository inspections, diff reviews, results, intent/risk/status models, and bounded metadata-only history.
- Added deterministic coding planning, safe read-only Git inspection, metadata-only diff review, test recommendations, risk classification, and sensitive-file redaction.
- Added `coding status`, `coding help`, `coding inspect`, `coding plan`, `coding risk`, `coding diff`, `coding review`, `coding tests`, `coding show`, and `coding history`.
- Integrated `coding_agent` with Prime routing, the Agent Registry, Skill Registry, Model Router, project status, and typed configuration.

### Safety

- Coding remains `plan_only`. File writes, command execution, dependency installation, commits, pushes, deployments, secret access, broad deletion, and force-push are disabled or blocked.
- Runtime coding history is ignored and metadata-only; full requests, source copies, diffs, secrets, command output, and private paths are not stored.

### Verification

- Focused Coding Agent tests: 24 passed, 0 skipped, 0 failed, 0 errors.
- Coding/Phase 3/tracking integration tests: 98 passed, 0 skipped, 0 failed, 0 errors.
- Cross-subsystem regression suite: 420 passed, 0 skipped, 0 failed, 0 errors.
- Full suite: 1,703 passed, 0 skipped, 0 failed, 0 errors.
- Compilation, JSON/document consistency, secret-shaped-value, absolute-path leakage, and `git diff --check` gates passed.

## Unreleased - Research Agent Foundation

### Added

- Added typed research questions, plans, evidence, summaries, results, safety decisions, source policy, and bounded metadata-only history.
- Added deterministic research intent, depth, risk, restricted-domain, clarification, evidence-requirement, and source planning.
- Added `research status`, `research help`, `research plan`, `research safety`, `research sources`, `research summarize`, `research evidence`, `research show`, and `research history`.
- Integrated the Research Agent with Prime routing, the Agent Registry, the Model Router, the Skill Registry, project status, and typed local-first configuration.

### Safety

- Research remains read-only and plan-first. External search APIs are disabled, web claims require citations, private-person targeting is blocked, restricted domains carry uncertainty and confirmation boundaries, and Persistent Memory is never mutated automatically.
- Runtime history is ignored by Git and stores bounded metadata only; it contains no full query, source dump, transcript, secret, or private absolute path.

### Verification

- Focused Prompt 51 and integration/tracking checks: 96 passed, 0 skipped, 0 failed, 0 errors.
- Full suite: 1,679 passed, 0 skipped, 0 failed, 0 errors.
- Compilation, JSON/document consistency, secret-shaped-value, absolute-path leakage, and `git diff --check` gates passed.

## Unreleased - Multi-Agent OS Foundation

### Added

- Added typed Agent Protocol models, a deterministic Agent Registry, duplicate validation, and bounded diagnostics.
- Added truthful current/foundation/future specialist entries with explicit capabilities, risks, permissions, approvals, locality, and limitations.
- Added Prime Agent deterministic intent/risk classification, approval metadata, plan-only delegation, safe fallbacks, and critical-risk blocking.
- Added a provider-neutral Model Provider Registry and Model Router with local-only routing, cloud-disabled defaults, unavailable provider metadata, and safe hardware hints.
- Added a permission-aware Skill Registry with current manifests, disabled future placeholders, and conceptual native/external/MCP provider contracts.
- Added bounded `agent`, `prime`, `model`, and `skill` CLI diagnostics and a concise Phase 3 project-status summary.
- Added Phase 3 architecture, agent, Prime Agent, model-router, and skill documentation.
- Stabilized bounded oversized local-interface request rejection on Windows by draining only modest rejected bodies before returning HTTP 413.

### Verification

- Focused Phase 3 integration/tracking suite: 66 passed.
- Cross-subsystem regression suite: 448 passed with 1 environment-dependent skip.
- Full suite: 1,658 passed with 3 environment-dependent skips, 0 failed, and 0 errors (1,661 total).

### Safety

- No new command executes agents, tools, models, plugins, MCP servers, network requests, hardware actions, communication actions, or background workers.
- Default execution remains `plan_only`; high-risk capabilities require approval metadata and critical future actions are blocked.
- Cloud providers, external plugins, and MCP remain disabled. Existing local chat, vision, voice, memory, web, sync, image, and video paths retain their established authorities.
- Vercel remains a bounded status-only surface.

## Unreleased - Video Editing Workflow Foundation

- Added a governed local-first video editing workflow foundation with prompt validation, safety review, provider abstraction, dry-run planning, bounded history, and truthful unavailable-provider handling.
- Added `video status`, `video help`, `video providers`, `video plan`, `video safety`, `video history`, and `video show`.
- Added ignored local runtime storage for bounded video metadata without committing generated media or export files.
- Verified the focused video-editing tests and the 1,600 passed full regression suite on the current local branch.

## Unreleased - Image Generation Workflow Foundation

- Added a governed local-first image-generation workflow foundation with prompt validation, safety review, provider abstraction, dry-run planning, bounded history, and truthful unavailable-provider handling.
- Added `image status`, `image help`, `image providers`, `image plan`, `image safety`, `image generate`, `image history`, and `image show`.
- Added ignored local runtime storage for bounded image metadata without committing generated files.
- Verified 13 focused image-generation tests and the 1,600-test full suite with three environment-dependent skips.

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
- Research Agent foundation for bounded planning, safety filtering, source policy, and read-only summaries.
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
