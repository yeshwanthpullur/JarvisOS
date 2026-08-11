# Checkpoint Runtime

Prompt 82 adds versioned, bounded, metadata-only workflow checkpoints. A checkpoint records workflow/schema versions, completed and remaining step identifiers, resource counters, a safe context reference, and an interrupted-step identifier. It never serializes provider credentials, approval tokens, prompts, private file contents, memory content, or external responses.

Checkpoints are created at configured safe boundaries, before waiting for authority, after completed steps, and on timeout/failure. History is capped. Restore validates the checkpoint identity, workflow/schema version, and step integrity before changing runtime state. Incompatible or missing checkpoints fail closed.

Runtime state is in memory. Persistent checkpoint storage, migration across incompatible workflow versions, unrestricted background execution, and automatic scheduled execution remain unavailable.
