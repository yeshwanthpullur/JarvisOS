# Roadmap

Updated: 2026-08-10

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
- Prompt 42 - Video Editing Workflow Foundation.
- Prompt 43 - Phase 3 Intake and Current-State Reconciliation.
- Prompt 44 - Agent Protocol and Agent Registry Foundation.
- Prompt 45 - Prime Agent and Delegation Foundation.
- Prompt 46 - Model Provider Registry and Model Router Foundation.
- Prompt 47 - Tool and Skill Registry Foundation.
- Prompt 48 - Specialist Agent Stubs and Diagnostics.
- Prompt 49 - Phase 3 Integration, Tests, Documentation, and Verification.
- Prompt 50 - Phase 3 Release, Status Checkpoint, and Continuation Plan.
- Prompt 51 - Research Agent Foundation.
- Release `v0.3.0-alpha - Local Voice and CLI Stability`.

## Next Milestone

Prompt 52 has not started. Its implementation requires explicit user approval and a complete specification before any code or tracking change is made.

## Preserved Deferred Themes

The following earlier Prompt 43-49 assignments remain valid product-direction themes in their original order. Phase 3 reused those prompt numbers for the Multi-Agent OS Foundation; this record preserves the earlier sequence without claiming that any theme was implemented or reordering future work.

### Real Encrypted Remote Sync Backend

**Goal:** Implement an authenticated encrypted adapter behind the existing local-first Sync foundation.

**Acceptance:** End-to-end encryption, strict schemas, conflict handling, revocation, audit, offline queues, and no secret synchronization.

### Cross-Device Sync

**Goal:** Synchronize approved summaries and project state among trusted devices.

**Acceptance:** Device enrollment, least privilege, deletion propagation, conflict resolution, and offline behavior are verified.

### Async Voice and Push-to-Talk Conversation

**Goal:** Improve conversational ergonomics after the STT and playback foundations.

**Acceptance:** Interruption, cancellation, text fallback, sensitive-content filtering, and correlated voice sessions work.

### Approval-Gated Interactive Web Automation

**Goal:** Add narrowly scoped clicking and typing behind explicit approval and the existing Web Automation Manager.

**Acceptance:** No login, submission, purchase, communication, or account change without scoped approval; stop and audit are complete.

### Safe Communication and Call Assistance Foundation

**Goal:** Support drafts, agendas, reminders, and future scoped connectors without impersonation or silent communication.

**Acceptance:** Nothing is sent or recorded without clear consent; private content is minimized and auditable.

### Wake Word and Continuous Listening Safety Layer

**Goal:** Evaluate opt-in wake word and bounded listening after push-to-talk is stable.

**Acceptance:** Disabled by default, visible capture state, local processing, immediate stop, and no secret background recording.

### Personal Workspace / Multi-Tool Replacement Layer

**Goal:** Unify approved chat, projects, study, research, creation, and automation workflows without duplicating authoritative systems.

**Acceptance:** One coherent workspace with selective context, user-controlled memory, clear status, and no hidden cross-tool data sharing.

## Product-Direction Themes

The master product vision in [`JARVIS_USE_CASES.md`](JARVIS_USE_CASES.md) still tracks longer-range themes such as study support, builder workflows, Raspberry Pi guidance, creative media, communication assistance, and the unified personal workspace. Those themes remain valid even when the exact prompt numbering evolved over time.

## Roadmap Rules

- Finish and verify one milestone before beginning the next.
- Update `CURRENT_STATUS.md`, `PROJECT_HEALTH.md`, `project_health.json`, and `CHANGELOG.md` with every release-worthy change.
- Do not advance status based only on architecture or mocked tests.
- Keep the CLI usable when optional providers, models, sync, vision, image generation, or automation are unavailable.
