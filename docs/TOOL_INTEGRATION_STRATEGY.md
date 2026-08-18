# Tool Integration Strategy

Optional tools live behind adapters and never become trusted merely because a package or executable is detected. Each registry entry records its role, environment, Python compatibility, adapter type, bounded input/output limits, timeout, network/file/command flags, approval requirement, health, error, and fallback.

The Tool Environment Registry has metadata authority only. Existing Execution Policy, Approval System, Execution Broker, governance, and subsystem-specific validators retain action authority. External tools cannot silently read secrets, write files, run commands, access the network, download models, or start services.

Primary and backup choices are diagnostic hints, not automatic failover permission. Fallbacks remain within existing safe functionality, such as read-only HTTP, lexical retrieval, plain-text parsing, Vosk, Windows SAPI, the native Provider Registry, and plan-only Coding Agent behavior.
