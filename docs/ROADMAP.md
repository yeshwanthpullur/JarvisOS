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
- Prompt 31.8 - Clean Tracking, Sync-Ready Status, and Project Health Foundation.
- Prompt 31.9 - Voice Input and Audio Storage Cleanup foundation.
- Prompt 32 - Vision Intelligence Foundation: safe image intake, metadata, CLI, policy, and provider routing.
- Prompt 32.1 - Safe Vercel status foundation, isolated from the local CLI. This is deployment readiness, not online sync.
- Release `v0.3.0-alpha - Local Voice and CLI Stability`.

## Prompt 33 - Online Sync Foundation

**Goal:** Add optional encrypted, local-first synchronization for approved summaries and records.

**Expected deliverables:** sync schema, explicit allowlist, encrypted transport/storage, offline queue, conflict records, audit trail, device identity, user controls, and recovery tests.

**Risks:** secret leakage, data duplication, destructive conflict resolution, stale authority, account compromise, and unbounded history growth.

**Acceptance criteria:** sync disabled by default, secrets excluded, offline operation preserved, conflicts never silently overwrite authoritative data, bounded queues, revocable devices, and complete audit metadata.

**Release target:** TBD after auditing the existing legacy `v0.5.0` tag to avoid version confusion.

The status-only Vercel endpoint may host future public readiness metadata, but it is not a sync server and must not receive user data, secrets, local state, or assistant requests.

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
