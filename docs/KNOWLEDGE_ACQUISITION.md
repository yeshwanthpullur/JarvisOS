# Knowledge Acquisition

Research may produce bounded knowledge candidates containing a statement, evidence IDs, source IDs, freshness, and TTL. Candidates are request-scoped recommendations, not authoritative memory. `memory_write_allowed` is always false in this runtime.

Time-sensitive claims should remain ephemeral or TTL-bound. Promotion to Persistent Memory requires the existing explicit memory authority and user action. Research cannot mutate tasks or goals; it can only provide evidence to their owning subsystems.
