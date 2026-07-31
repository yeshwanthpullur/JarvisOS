# Sync Strategy

This document defines the implemented local foundation and the future encrypted remote direction. Real remote synchronization is not configured.

The Vercel status foundation is not a sync implementation. Its root and API responses are static, safe deployment metadata and accept no JARVIS records. The duplicate `jarvis-os-6oy2` project should be disconnected or deleted manually after `jarvis-os` is confirmed as the canonical deployment.

## Implemented Foundation

- Sync defaults to `off`; `sync on` enables manual local queue mode only.
- `data/sync/queue.json` uses bounded versioned JSON and atomic replacement. Runtime files remain ignored by Git.
- Only project/health/release, task/goal/memory/preference summaries, and checkpoints are eligible through explicit field allowlists.
- Policy runs before enqueue and again before transmission. It rejects secret-shaped fields and values, absolute paths, binary/base64 content, oversized strings/items, deep nesting, and unknown fields.
- Payload hashes prevent duplicate queue entries. Completed history and audit events are count-bounded.
- Hash/version mismatch produces an unresolved conflict under the default `manual` strategy; remote records never mutate authoritative local systems.
- The unavailable remote adapter cannot mark an item synced. No background scheduler or automatic upload exists.

## Local-First Principle

The local device remains authoritative by default. JARVIS must start, chat locally, use approved local tools, and access local records while offline. Sync is optional, disabled until configured, and must never become a startup dependency.

## Data Allowed to Sync

Only explicit, versioned, allowlisted records should be eligible:

- User-approved project, goal, milestone, and task summaries.
- User-approved durable preferences that are already appropriate for Personal Intelligence.
- Bounded conversation summaries, not complete raw histories by default.
- Knowledge references or user-selected documents where licensing and privacy permit.
- Project-health, release, and device-sync metadata.
- Audit receipts needed to explain synchronization decisions.

## Data That Must Stay Local

- API keys, passwords, tokens, credentials, private environment variables, and authorization headers.
- Raw provider prompts/responses unless explicitly approved for a defined purpose.
- Raw audio, microphone recordings, temporary speech files, runtime logs, caches, and local databases.
- Hidden reasoning, private agent scratch data, and unredacted tool payloads.
- Machine-specific paths, process details, and device secrets.

## Security Requirements

- Encrypt data in transit and at rest.
- Use per-device identity and revocable scoped credentials.
- Keep encryption keys outside synchronized payloads.
- Redact and validate every record before queueing.
- Treat the server and incoming records as untrusted.
- Maintain an append-only audit receipt for upload, download, conflict, rejection, and deletion events.
- A future adapter remains disabled unless HTTPS, authenticated requests, encryption at rest, integrity validation, key rotation, and device revocation are supported and verified.

## Sync Queue

A future bounded queue should hold record references, versions, hashes, attempt counts, next-attempt time, and safe errors. It must not copy entire authoritative databases. Retries must be bounded, cancellation must be possible, and poison records must move to a review state.

## Offline and Conflict Behavior

- Local work continues offline and produces versioned changes.
- Conflicts create explicit records; they do not silently overwrite either side.
- Merge only fields with defined safe semantics.
- Project/task/workflow mutations still use their authoritative local interfaces.
- Deletions use tombstones with retention and confirmation rules.
- Clock time alone is insufficient to resolve important conflicts.

## Future Server Options

Options may include a small self-hosted service, an encrypted object store, or a managed database with row-level access. Selection should be based on threat model, data residency, offline support, operational cost, and export/delete guarantees. No server option is selected by this milestone.

## User Controls

Users must be able to see eligible data, pending records, conflicts, devices, last successful sync, and failures; pause sync; revoke a device; export records; and request deletion. Sync status must never imply success without an acknowledged remote receipt.
