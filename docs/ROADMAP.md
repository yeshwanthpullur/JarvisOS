# Roadmap

Updated: 2026-08-01

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
- Release `v0.3.0-alpha - Local Voice and CLI Stability`.

## Prompt 32 - Vision Intelligence

**Goal:** Add governed understanding of user-supplied images and screenshots without enabling autonomous screen control.

**Expected deliverables:** image intake and validation, local/provider capability routing, OCR or visual analysis where genuinely available, normalized evidence, privacy controls, commands/public flow, health, tests, and documentation.

**Risks:** sensitive image exposure, prompt injection inside images, unsupported capability claims, high memory use, and accidental coupling to automation.

**Acceptance criteria:** real bounded image analysis through Provider Router, truthful unavailable states, source correlation, no hidden actions, selective context, clean startup without a vision runtime, and passing regression tests.

**Candidate release target:** `v0.4.0-alpha` after real local or explicitly authorized provider verification.

## Prompt 33 - Online Sync Foundation

**Goal:** Add optional encrypted, local-first synchronization for approved summaries and records.

**Expected deliverables:** sync schema, explicit allowlist, encrypted transport/storage, offline queue, conflict records, audit trail, device identity, user controls, and recovery tests.

**Risks:** secret leakage, data duplication, destructive conflict resolution, stale authority, account compromise, and unbounded history growth.

**Acceptance criteria:** sync disabled by default, secrets excluded, offline operation preserved, conflicts never silently overwrite authoritative data, bounded queues, revocable devices, and complete audit metadata.

**Release target:** TBD after auditing the existing legacy `v0.5.0` tag to avoid version confusion.

## Prompt 34 - Web Automation

**Goal:** Add permission-gated browser automation through authoritative Tool and Workflow paths.

**Expected deliverables:** browser tool contract, target allowlists, read/action separation, screenshot evidence, approval prompts, cancellation, rollback guidance, and safe audit history.

**Risks:** prompt injection, account actions, accidental purchases/messages, credential exposure, destructive navigation, and terms-of-service violations.

**Acceptance criteria:** sensitive actions require explicit approval, provider/agent output cannot authorize actions, stop controls work, every action is correlated and auditable, and no arbitrary script execution exists.

**Release target:** TBD after Vision and Sync foundations are stable.

## Prompt 35 - Mobile Automation

**Goal:** Add a narrow, permission-scoped mobile companion and device-action bridge.

**Expected deliverables:** trusted-device enrollment, scoped capabilities, confirmation UX, secure transport, status reporting, action receipts, revoke/stop controls, and recovery behavior.

**Risks:** device takeover, notification/message leakage, unsafe background actions, location exposure, and unreliable connectivity.

**Acceptance criteria:** explicit device trust, least privilege, no silent actions, local revocation, encrypted communication, bounded retries, complete action audit, and safe offline behavior.

**Release target:** TBD after Web Automation security review.

## Roadmap Rules

- Finish and verify one milestone before beginning the next.
- Update `CURRENT_STATUS.md`, `PROJECT_HEALTH.md`, `project_health.json`, and `CHANGELOG.md` with every release-worthy change.
- Do not advance status based only on architecture or mocked tests.
- Keep the CLI usable when optional providers, models, sync, vision, or automation are unavailable.
