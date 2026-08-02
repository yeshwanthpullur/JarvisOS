# Memory and Data Policy

## Sync Data Boundary

The sync queue may contain only small sanitized summaries allowed by `SyncItemType`. It must not contain raw memory records or databases, conversations, prompts, hidden reasoning, logs, audio/transcripts, images/screenshots, video, documents, provider payloads, credentials, environment values, or local paths. The anonymous installation UUID is random and local; it is not derived from a username, hardware identifier, MAC address, or IP address.

Queue and audit histories are bounded by configuration, duplicate summaries are suppressed by hash, completed records are pruned by `sync cleanup`, and malformed queue files are quarantined for local review rather than uploaded. Status output remains concise and never reveals the installation UUID.

## Purpose

Keep JARVIS useful without turning local storage into an unbounded archive. Authoritative systems own their records; tracking documents summarize project state and must not duplicate runtime databases.

## Store

- Structured goals, projects, milestones, tasks, workflow state, and approved durable memory through their authoritative interfaces.
- Confirmed user preferences with provenance and update/forget controls.
- Bounded conversation summaries when future continuity justifies them.
- Knowledge records with source references and licensing/provenance metadata.
- Execution, approval, and audit summaries needed for accountability.
- Current project status, roadmap, release notes, and compact health evidence in Git.

## Do Not Store

- API keys, passwords, tokens, credentials, authorization headers, or raw environment values.
- Hidden reasoning or private chain-of-thought.
- Every conversation turn as permanent global memory.
- Unredacted sensitive tool, provider, research, web, or personal payloads.
- Generated WAV files, microphone recordings, logs, caches, temporary downloads, or machine-specific runtime files in Git.
- Duplicate copies of authoritative task, workflow, goal, memory, knowledge, or profile records.

## Retention and Summarization

- Temporary request and active-context state expires when no longer relevant.
- Logs rotate using configured size and backup limits.
- Tool, agent, planning, and voice histories remain bounded by subsystem limits.
- Voice output uses direct playback by default. Explicitly saved audio is user-owned; temporary microphone audio stays in the configured temp directory, is not durable memory, and is cleaned by age/count policy or `voice cleanup`.
- Push-to-talk audio is processed in memory and is not persisted by default. A transcript is shown locally and remains transient unless the user explicitly submits it through the normal command or conversation path; the voice-input audit stores only bounded status metadata, never transcript text or audio bytes.
- Summaries preserve decisions, evidence, provenance, unresolved questions, and authoritative references; they omit repetitive chat and private scratch data.
- Numeric progress and health claims require evidence and a verification date.

## Archive and Deletion

- Completed historical records may move to an archive state instead of being deleted.
- Expired temporary artifacts should be removed by bounded cleanup.
- User forget/delete requests must use authoritative APIs and preserve only legally or operationally required audit receipts.
- Archives must remain searchable without being loaded into every request.

## Clean Folder Expectations

- `docs/`: concise maintained documentation and project-health summaries.
- `data/`: ignored local runtime data; only `.gitkeep` is tracked by default.
- `logs/`: ignored rotating logs; only `.gitkeep` is tracked.
- `memory/`: source code for memory authority; runtime databases remain outside Git.
- `downloads/`: temporary or user-controlled downloads, not release assets by default.
- `tests/`: deterministic fixtures only; no real secrets or paid calls.

## Avoiding Bloat

- Retrieve selectively instead of loading full history.
- Store references to authoritative records rather than copied content.
- Cap histories, payloads, output sizes, retries, and queue length.
- Review stale memories and unresolved context before promoting them to durable state.
- Keep `project_health.json` as the latest snapshot, not an event log.
- Use release history in `CHANGELOG.md`; do not append repeated status reports elsewhere.

## Keeping Status Accessible

`CURRENT_STATUS.md` is the human entry point, `PROJECT_HEALTH.md` explains evidence, `project_health.json` supports tools, `ROADMAP.md` defines the next milestones, and `CHANGELOG.md` records released changes. Update them together when verified capability changes.
