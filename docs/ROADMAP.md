# Roadmap

Updated: 2026-08-02

## Completed Milestones

- Prompt 27 - Cloud AI and Provider foundation.
- Prompt 27 completion - Provider-backed ordinary chat.
- Prompt 28 - Multi-Agent Intelligence.
- Prompt 29 - Tool Intelligence.
- Prompt 30 - Autonomous Planning.
- Prompt 31 - Voice Intelligence.
- Prompt 31.5 - Local Desktop Interface MVP.
- Prompt 31.6 - Interface Redesign and Stabilization.
- Prompt 31.7 - Stable CLI Voice and Normal JARVIS Mode.
- Prompt 31.8 - Clean Tracking, Sync-Ready Status, and Project Health Foundation.
- Prompt 31.9 - Voice Input and Audio Storage Cleanup foundation.
- Prompt 32 - Vision Intelligence Foundation: safe image intake, metadata, CLI, policy, and provider routing.
- Prompt 32.1 - Safe Vercel status foundation, isolated from the local CLI. This is deployment readiness, not online sync.
- Prompt 33 - Online Sync Foundation: governed local queue, strict policy, manual CLI, conflict and adapter foundations; remote transfer remains unavailable.
- Prompt 33.1 - Limitations Audit and Fix Pass: evidence-backed limitations register, concise CLI counts, and consolidated setup guidance.
- Prompt 34 - Web Automation Foundation: provider-neutral policy, permissions, read-only CLI, normalized results, and bounded redacted audit; real browser control and sensitive actions remain deferred.
- Prompt 34.1 - Real Read-Only Web Adapter and Page Inspection: bounded public HTML/text inspection, DNS/IP SSRF controls, redirect revalidation, sanitized previews, and redacted audit.
- Prompt 35 - Mobile Automation Foundation: planning-only policy, adapters, commands, and bounded redacted audit without phone access.
- Prompt 36 - Real Local STT and Voice Input Foundation: optional Vosk recognition and explicit in-memory microphone capture path.
- Prompt 37 - Real Vision Model Integration: local Ollama model discovery and image execution through Provider Router with no image persistence.
- Release `v0.3.0-alpha - Local Voice and CLI Stability`.

## Web Automation - Remaining Work

**Goal:** Introduce narrowly scoped interactive operations only after approval UX and threat review. Read-only public page inspection is complete.

**Expected deliverables:** explicit approvals, controlled browser lifecycle, cancellation, rollback guidance, and safe evidence handling for narrowly scoped interactions.

**Risks:** prompt injection, account actions, accidental purchases/messages, credential exposure, destructive navigation, and terms-of-service violations.

**Acceptance criteria:** sensitive actions require explicit approval; provider/agent output cannot authorize actions; stop controls work; every action is correlated and auditable; no arbitrary script execution exists.

**Release target:** TBD after Vision and Sync foundations are stable.

## Prompt 35 - Mobile Automation

**Status:** Completed foundation. Planning-only manager, adapters, CLI, strict policy, and redacted audit exist; no phone control exists.

**Goal:** Add a narrow, permission-scoped mobile companion and device-action bridge.

**Delivered foundation:** provider-neutral models and adapters, planning-only commands, safe setup guidance, capability classification, sensitive-action blocking, and bounded audit. Trusted-device enrollment, secure transport, live adapters, confirmation UX for execution, and device actions remain future work.

**Risks:** device takeover, notification/message leakage, unsafe background actions, location exposure, and unreliable connectivity.

**Acceptance criteria:** explicit device trust, least privilege, no silent actions, local revocation, encrypted communication, bounded retries, complete action audit, and safe offline behavior.

**Release target:** TBD after Web Automation security review.

## Long-Term Milestones

These milestones express product direction, not current capability. Detailed use cases and safety boundaries are maintained in [`JARVIS_USE_CASES.md`](JARVIS_USE_CASES.md). Each milestone requires its own implementation prompt and acceptance evidence.

### Prompt 36 - Real Local STT and Voice Input

**Status:** Foundation complete. Vosk recognition, model validation, optional explicit microphone capture, CLI handoff, and privacy controls are implemented; live microphone verification remains blocked by missing local prerequisites.

**Goal:** Verify local push-to-talk microphone transcription through a supported offline model and bounded capture adapter.

**Acceptance:** Real transcription, no cloud audio, explicit capture state, no raw-audio persistence by default, cancellation, and truthful unavailable behavior.

### Prompt 37 - Real Vision Model Integration

**Status:** Adapter complete. Real local Ollama image requests, model capability checks, commands, policy, normalization, and audit are implemented; a real semantic result still requires installing a local vision model.

**Goal:** Connect a genuinely vision-capable local model through Provider Router.

**Acceptance:** Real descriptions and questions over validated images, local-only enforcement, model evidence, and no fabricated interpretation.

### Prompt 38 - Study Assistant and Research Workflows

**Goal:** Compose existing conversation, retrieval, research, goals, documents, and web inspection into evidence-aware study workflows.

**Acceptance:** Explanations, quizzes, plans, source comparison, citations, and reports remain attributable and academically honest.

### Prompt 39 - Conversation Intelligence

**Goal:** Add bounded multi-turn context, topic and entity tracking, follow-up intent, reference resolution, clarification, repair, summaries, confidence, and conversation modes.

**Acceptance:** Text and explicit voice handoff share one conversational path; memory remains authoritative and explicit; ambiguous references produce one clarification; context stays bounded and local.

### Prompt 40 - Raspberry Pi Deployment and Hardware Support

**Tracking note:** The approved Prompt 40 limitations review and safe-fix pass is complete. It did not start hardware implementation or alter the milestone sequence; this hardware goal remains future work.

**Goal:** Add hardware profiles, safe setup guidance, deployment checks, and bounded support for Raspberry Pi and related projects.

**Acceptance:** Device constraints are verified, physical risks are disclosed, and privileged or physical actions require confirmation.

### Prompt 41 - Image Generation Workflow Foundation

**Goal:** Add permission-controlled visual creation workflows through approved image tools.

**Acceptance:** Provenance, privacy, safe-content policy, file controls, and honest generated-content labeling are enforced.

### Prompt 42 - Video Editing Workflow Foundation

**Goal:** Add scripts, shot lists, clip organization, captions, and non-destructive editing plans before editor integration.

**Acceptance:** No silent uploads or destructive edits; source files and exports remain explicit and reviewable.

### Prompt 43 - Real Encrypted Remote Sync Backend

**Goal:** Implement an authenticated encrypted adapter behind the existing local-first Sync foundation.

**Acceptance:** End-to-end encryption, strict schemas, conflict handling, revocation, audit, offline queues, and no secret synchronization.

### Prompt 44 - Cross-Device Sync

**Goal:** Synchronize approved summaries and project state among trusted devices.

**Acceptance:** Device enrollment, least privilege, deletion propagation, conflict resolution, and offline behavior are verified.

### Prompt 45 - Async Voice and Push-to-Talk Conversation

**Goal:** Provide non-blocking playback and ergonomic push-to-talk after real STT exists.

**Acceptance:** Interruption, cancellation, text fallback, sensitive-content filtering, and correlated voice sessions work.

### Prompt 46 - Approval-Gated Interactive Web Automation

**Goal:** Add narrowly scoped clicking and typing behind explicit approval and the existing Web Automation Manager.

**Acceptance:** No login, submission, purchase, communication, or account change without scoped approval; stop and audit are complete.

### Prompt 47 - Safe Communication and Call Assistance Foundation

**Goal:** Support drafts, agendas, reminders, and future scoped connectors without impersonation or silent communication.

**Acceptance:** Nothing is sent or recorded without clear consent; private content is minimized and auditable.

### Prompt 48 - Wake Word and Continuous Listening Safety Layer

**Goal:** Evaluate opt-in wake word and bounded listening after push-to-talk is stable.

**Acceptance:** Disabled by default, visible capture state, local processing, immediate stop, and no secret background recording.

### Prompt 49 - Personal Workspace / Multi-Tool Replacement Layer

**Goal:** Unify approved chat, projects, study, research, creation, and automation workflows without duplicating authoritative systems.

**Acceptance:** One coherent workspace with selective context, user-controlled memory, clear status, and no hidden cross-tool data sharing.

### Prompt 50 - v1.0 MVP Hardening

**Goal:** Stabilize supported workflows, reduce open high-severity limitations, and prepare a trustworthy v1.0.

**Acceptance:** Full regression and security review, documented support matrix, migration/recovery checks, clean release artifacts, and real acceptance evidence.

## Roadmap Rules

- Finish and verify one milestone before beginning the next.
- Update `CURRENT_STATUS.md`, `PROJECT_HEALTH.md`, `project_health.json`, and `CHANGELOG.md` with every release-worthy change.
- Do not advance status based only on architecture or mocked tests.
- Keep the CLI usable when optional providers, models, sync, vision, or automation are unavailable.
