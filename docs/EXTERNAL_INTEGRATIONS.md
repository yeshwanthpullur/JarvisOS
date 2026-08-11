# External Integrations

Prompt 72 communication validation references this central registry and does not create a competing provider authority.

Prompt 71 adds a metadata-only External Integration Control Plane. It inventories communication, developer, model, MCP, and plugin providers and applies one bounded policy before any future adapter can be considered.

No external provider is enabled or executed. Telegram, Discord, email, Slack, WhatsApp, GitHub remote operations, remote models, MCP, and plugins remain unavailable. Existing local Git, Ollama, browser SSRF policy, Phase 4 approvals, Broker, and Execution Policy remain authoritative.

Use `integration status`, `integration policy`, `provider list`, `provider show <id>`, `provider capabilities`, `provider health <id>`, `provider policy`, `provider validate <id>`, `provider history`, `credential status <id>`, and `credential required` for bounded metadata.
