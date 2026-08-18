# Connector Ecosystem

Phase 6 provides one normalized metadata view for built-in GitHub, Telegram, Discord, email, Slack, MCP, and plugin adapters. Installed, discovered, configured, credential-present, enabled, policy-allowed, authenticated, healthy, and connected are separate states. Discovery never implies readiness.

Credential fields are references only. Connectors do not auto-enable, auto-authenticate, auto-install, auto-update, start MCP servers, or send data. Existing provider-specific policy, approval, Broker, retry, and audit boundaries remain authoritative.
