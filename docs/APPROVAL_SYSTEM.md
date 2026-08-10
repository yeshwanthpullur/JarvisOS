# Approval System

Approvals are local, bounded, in-memory authorization records. A request records an action fingerprint, resource, permissions, risk, expiry, and state. Approval is exact: permission, action, and resource mismatches are rejected.

States include pending, approved, denied, cancelled, expired, revoked, and blocked. Approval does not execute an action; the execution broker independently revalidates policy immediately before dispatch.

Commands: `approval status`, `approval list`, `approval show <id>`, `approval approve <id>`, `approval deny <id>`, `approval cancel <id>`, and `approval cleanup`.

Approval records contain metadata only. They do not store secrets, file contents, command output, transcripts, or private absolute paths.
