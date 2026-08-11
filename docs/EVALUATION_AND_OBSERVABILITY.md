# Evaluation And Observability

Model observability records bounded route, latency, health, fallback, error, circuit, and resource metadata without full prompts or responses.

Plugin observability records bounded lifecycle counts and error categories only, never secrets or raw private payloads.

MCP telemetry is metadata-only: server/tool counts, state, trust, reads/calls, blocks, timeouts, rate limits, and safe errors. Raw content and credentials are not persisted.

GitHub observability stores bounded provider/action state, scope and policy failures, rate limits, and safe errors. It stores no tokens, bodies, patches, or repository copies.

Telegram observability is bounded metadata only: provider state, poll/update counts, authorization outcomes, sends, failures, rate limits, duplicates, and approval events. Tokens, message bodies, raw updates, and chat profiles are excluded.

External communication observability is bounded to provider/action/status/rate/error/approval-reference metadata. Message bodies, contact lists, credentials, sessions, and attachments are excluded.

## Execution Audit

Phase 4 audit metadata is bounded and content-free: action, state transition, counts, safe error codes, and duration. It excludes secrets, file contents, command output, notification bodies, transcripts, and private absolute paths. No cloud telemetry or remote logging is enabled.

Prompt 59 adds deterministic local routing and safety fixtures, provider/adapter truthfulness checks, bounded subsystem health metadata, and a local observability snapshot.

There is no cloud telemetry, remote logging, user tracking, background runner, prompt capture, log upload, or external dashboard. Results are metadata only and runtime history is ignored by Git.

Commands: `evaluation status`, `help`, `run`, `routing`, `safety`, `truthfulness`, `observability`, `show`, and `history`.
