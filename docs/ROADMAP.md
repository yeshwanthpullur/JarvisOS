# Roadmap

Updated: 2026-08-04

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
- Prompt 32 - Vision Intelligence Foundation.
- Prompt 32.1 - Safe Vercel status foundation, isolated from the local CLI.
- Prompt 33 - Online Sync Foundation.
- Prompt 33.1 - Limitations Audit and Fix Pass.
- Prompt 34 - Web Automation Foundation.
- Prompt 34.1 - Real Read-Only Web Adapter and Page Inspection.
- Prompt 34.2 - JARVIS Master Use Cases and Product Vision.
- Prompt 35 - Mobile Automation Foundation.
- Prompt 36 - Real Local STT and Voice Input Foundation.
- Prompt 37 - Real Vision Model Integration.
- Prompt 38 - Local Memory Upgrade and Persistent Personal Context.
- Prompt 39 - Conversation Intelligence.
- Prompt 40 - Limitations Review, Prioritization, and Safe Fix Pass.
- Prompt 41 - Image Generation Workflow Foundation.
- Release `v0.3.0-alpha - Local Voice and CLI Stability`.

## Next Milestone

### Prompt 42 - Video Editing Workflow Foundation

**Goal:** Add scripts, shot lists, clip organization, captions, and non-destructive editing plans before editor integration.

**Acceptance:** No silent uploads or destructive edits; source files and exports remain explicit and reviewable.

## Future Milestones

### Prompt 43 - Real Encrypted Remote Sync Backend

**Goal:** Implement an authenticated encrypted adapter behind the existing local-first Sync foundation.

**Acceptance:** End-to-end encryption, strict schemas, conflict handling, revocation, audit, offline queues, and no secret synchronization.

### Prompt 44 - Cross-Device Sync

**Goal:** Synchronize approved summaries and project state among trusted devices.

**Acceptance:** Device enrollment, least privilege, deletion propagation, conflict resolution, and offline behavior are verified.

### Prompt 45 - Async Voice and Push-to-Talk Conversation

**Goal:** Improve conversational ergonomics after the STT and playback foundations.

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

## Product-Direction Themes

The master product vision in [`JARVIS_USE_CASES.md`](JARVIS_USE_CASES.md) still tracks longer-range themes such as study support, builder workflows, Raspberry Pi guidance, creative media, communication assistance, and the unified personal workspace. Those themes remain valid even when the exact prompt numbering evolved over time.

## Roadmap Rules

- Finish and verify one milestone before beginning the next.
- Update `CURRENT_STATUS.md`, `PROJECT_HEALTH.md`, `project_health.json`, and `CHANGELOG.md` with every release-worthy change.
- Do not advance status based only on architecture or mocked tests.
- Keep the CLI usable when optional providers, models, sync, vision, image generation, or automation are unavailable.
