# Approval System

MCP side-effect approval binds server, tool, capability, input fingerprint, target, permission, and expiry. No MCP-local approval database exists.

GitHub write approvals bind repository, action, content fingerprint, permissions, and expiry. Repository or material content changes invalidate approval.

Telegram approval commands are interface concepts only; they must resolve an authorized, unexpired, exact-scope record in this authoritative system. Prompt 73 creates no parallel approval storage.

Prompt 72 keeps this system authoritative for future external sends. Approval must bind provider, exact destination, content fingerprint/summary, attachments, permission, and expiry; material changes require new approval.

Approvals are local, bounded, in-memory authorization records. A request records an action fingerprint, resource, permissions, risk, expiry, and state. Approval is exact: permission, action, and resource mismatches are rejected.

States include pending, approved, denied, cancelled, expired, revoked, and blocked. Approval does not execute an action; the execution broker independently revalidates policy immediately before dispatch.

Commands: `approval status`, `approval list`, `approval show <id>`, `approval approve <id>`, `approval deny <id>`, `approval cancel <id>`, and `approval cleanup`.

Approval records contain metadata only. They do not store secrets, file contents, command output, transcripts, or private absolute paths.
