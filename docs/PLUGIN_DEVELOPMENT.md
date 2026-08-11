# Plugin Development

Local development plugins may register metadata for inspection, but still obey manifest validation, permissions, integrity, approval, Broker, and execution policy. There is no universal unsafe flag.

Prefer declarative integrations, then bounded adapters, then isolated subprocess or MCP designs only after a dedicated security review. External packages belong in ignored runtime storage, not the repository. Never include credentials, generated output, private data, or install scripts in tracked plugin metadata.
