# Agent Worktree Isolation

Repository-modifying workers receive a worktree plan with a bounded task ID, a `jarvis/task-...` branch, and an opaque workspace reference. Plans reject path escapes and automatic merge.

Worktree creation and cleanup call a delegated authorization check. The default check denies every operation. A caller must bridge this check to the existing Approval, Execution Policy, Broker, and Git authority before any Git subprocess can run. Cleanup retains the branch for explicit review; merge and branch deletion are never automatic.

Stale mappings are detectable when a recorded created workspace no longer exists. Artifact references remain bounded and untrusted until independently reviewed.

