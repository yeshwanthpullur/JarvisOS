# Workflow Observability

The runtime tracks bounded metadata: workflow states, ordered event types, checkpoints, retries, timeouts, parallel-ready counts, recovery counts, temporary artifact metadata, and resource counters. Event history and artifact counts have configured limits.

Audit records contain component, operation, result, policy decision, and resource summaries only. They exclude credentials, prompts, full provider responses, private paths, memory content, and transcripts. `workflow health`, `workflow metrics`, `workflow trace`, and `workflow events` expose bounded views.
