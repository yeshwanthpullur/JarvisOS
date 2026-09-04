# Goal and Work Manager

The pre-old-phone work layer provides bounded records for Goal, Project, Milestone, Task, Subtask, AgentRun, Artifact, Review, Approval, Evidence, and Result. It complements the existing Task Intelligence and Prompt 81 orchestration authorities; it does not replace either.

Task dependencies must reference tasks in the same session and form an acyclic graph. Ready tasks are limited by configured parallel capacity. State transitions cover planning, running, waiting, completion, cancellation, resume, timeout, failure, and blocking. Dependency failure blocks hard dependants.

Persistent state is metadata-only under ignored `data/workers/`. It omits objective text, source payloads, context content, secrets, and absolute paths. This makes restart diagnostics possible without creating another memory store.

