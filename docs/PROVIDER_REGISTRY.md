# External Provider Registry

Model endpoints reuse provider security boundaries; remote inference requires explicit configuration, HTTPS, credential isolation, and data-egress policy.

Provider plugins may contribute metadata and adapters, but cannot self-report ready without independent runtime health verification.

`mcp_local` and `mcp_remote` remain provider-level profiles; MCP Registry owns granular server, tool, resource, trust, and lifecycle metadata.

The `github` provider exposes separate GitHub API authentication, repository access, and ready states. Git remote readiness is not API readiness; the runtime is disabled and unverified by default.

Telegram now has an implemented text adapter with distinct disabled, credential-missing, authentication-unverified, and ready runtime states. Token presence alone never means ready.

Prompt 72 communication profiles reference central provider IDs and cannot elevate central provider state or enable execution.

The registry stores typed provider identity, category, capabilities, risk, permissions, side effects, locality, cost class, credential references, health metadata, and policy. Duplicate identifiers and duplicate per-provider capabilities are rejected.

Registered does not mean ready. Prompt 71 entries are disabled and unconfigured, and their execution policy is false. Health is cached metadata and never performs a network probe from diagnostics.

Local model endpoints and remote service endpoints use separate validation rules. Credentials in URLs are blocked. Remote endpoints require HTTPS; local model endpoints must remain loopback-only.
