# Phase 4 Controlled Execution

Prompts 61-70 add a narrow local execution foundation. JARVIS remains `plan_only` by default. Execution is available only through the central broker, an exact pending approval, and a dedicated executor with its own scope and policy.

Implemented foundations:

- bounded approval lifecycle and metadata-only audit
- central execution-policy and broker validation
- workspace-scoped file operations with rollback where supported
- allowlisted local commands without a shell
- explicit Git stage, unstage, commit, and push controls
- controlled public HTTP(S) reads with SSRF protections
- local console notifications
- manual scheduler execution for notification jobs

Not implemented: autonomous execution, hidden background workers, arbitrary shell commands, broad deletion, force-push, secret access, browser writes, account actions, external messaging, cloud execution, or public local-model access.

The current release checkpoint remains `v1.7.0-alpha`. Phase 4 does not create a release; the next release requires separate approval.
