# External Agent Adapter Contract

`jarvis.workers.WorkerAdapter` is the vendor-neutral boundary for Codex, Hermes, OpenCode, Aider, Munder, and future workers. Its operations are `detect`, `health`, `capabilities`, `start_task`, `status`, `stream_events`, `poll`, `send_context`, `request_approval`, `cancel`, `resume`, `collect_artifacts`, `collect_result`, `report_status`, and `finish`.

Detection and health may run bounded metadata commands such as `--version`. Planning never starts an external process. No adapter may approve itself, read raw secrets, select unrestricted permissions, auto-commit, auto-push, auto-merge, or treat worker output as trusted evidence.

Every result has a task ID, worker ID, bounded status, summary, artifact and evidence references, warnings, and a structured safe error. Error codes cover installation, authentication, provider, workspace, permission, timeout, crash, unsupported-capability, worker-mismatch, and execution-authority failures. Missing and malformed workers fail with `unavailable`, `blocked`, or `failed` rather than an invented success. Secret-shaped values and private absolute paths are redacted or rejected at the worker boundary.
