# Evaluation And Observability

## Execution Audit

Phase 4 audit metadata is bounded and content-free: action, state transition, counts, safe error codes, and duration. It excludes secrets, file contents, command output, notification bodies, transcripts, and private absolute paths. No cloud telemetry or remote logging is enabled.

Prompt 59 adds deterministic local routing and safety fixtures, provider/adapter truthfulness checks, bounded subsystem health metadata, and a local observability snapshot.

There is no cloud telemetry, remote logging, user tracking, background runner, prompt capture, log upload, or external dashboard. Results are metadata only and runtime history is ignored by Git.

Commands: `evaluation status`, `help`, `run`, `routing`, `safety`, `truthfulness`, `observability`, `show`, and `history`.
