# External Provider Registry

Telegram now has an implemented text adapter with distinct disabled, credential-missing, authentication-unverified, and ready runtime states. Token presence alone never means ready.

Prompt 72 communication profiles reference central provider IDs and cannot elevate central provider state or enable execution.

The registry stores typed provider identity, category, capabilities, risk, permissions, side effects, locality, cost class, credential references, health metadata, and policy. Duplicate identifiers and duplicate per-provider capabilities are rejected.

Registered does not mean ready. Prompt 71 entries are disabled and unconfigured, and their execution policy is false. Health is cached metadata and never performs a network probe from diagnostics.

Local model endpoints and remote service endpoints use separate validation rules. Credentials in URLs are blocked. Remote endpoints require HTTPS; local model endpoints must remain loopback-only.
