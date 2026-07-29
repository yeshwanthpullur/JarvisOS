# Autonomous Planning

Autonomous Planning turns complex objectives into reviewable plans while Executive JARVIS remains the decision authority. It does not execute tools, dispatch agents, create tasks, mutate goals, or start workflows.

The flow is Conversation and Context to Executive and Reasoning, followed by selective planning assessment, objective normalization, provider-backed summary generation, deterministic structural validation, and user review. Simple chat, commands, Tool Intelligence, and Multi-Agent requests retain their existing paths.

Objectives preserve the user request, desired outcome, constraints, prohibited actions, success criteria, references, assumptions, and unresolved questions. Plans contain versioned milestones, steps, dependencies, risk, permissions, approvals, evidence requirements, recovery guidance, and execution policy. Steps preserve unique IDs, ordering, dependencies, completion evidence, risk, timeout, retry, and rollback guidance.

Validation detects duplicate IDs, missing dependencies, cycles, limits, and unavailable tool references. Provider output is untrusted and supplies only the visible planning summary; the validated structure preserves policy and authority boundaries. High-risk work requires explicit scoped approval. Approval does not execute a plan: it enables an immutable handoff request for authoritative Goal, Task, or Workflow processing.

Commands include `plan status`, `list`, `show`, `steps`, `validate`, `alternatives`, `approve`, `reject`, `pause`, `resume`, `cancel`, `replan`, `history`, `mode`, and `limits`. Modes are `off`, `suggest`, `confirm`, and `automatic-safe`; none bypass mandatory approval.

Plans are persisted under the existing data directory. Replanning creates a new version, preserves completed evidence, supersedes the earlier plan, and is bounded. Interrupted execution is never resumed because planning owns no execution.

Current limitations: natural-language assessment is conservative; conversion returns validated authoritative requests but does not automatically create goals, tasks, or workflows; monitoring consumes status only when authoritative references are attached; alternatives are bounded advisory versions.
