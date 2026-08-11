# Workflow Recovery

Workflow recovery prepares metadata and bounded state for retry and rollback behavior.

Supported recovery actions:
- retry step
- retry workflow planning
- rollback metadata
- resume
- skip or alternative-path planning

Recovery starts only from a validated checkpoint. The runtime rebuilds step state from identifiers, restores bounded resource counters, validates the dependency graph, and pauses at a safe boundary for explicit continuation. An interrupted step is restarted as a whole; partial external side effects are not inferred or replayed.

Recovery cannot grant approval, add permissions, bypass Execution Policy, or invoke an executor. Broker and provider readiness are revalidated by their authoritative subsystems. Failed recovery preserves diagnostics and valid checkpoints and returns a safe error. Partial completion is represented explicitly instead of being reported as success.
