# MCP Tool Policy

Discovered tools are independently classified as read, search, retrieve, create, modify, delete, execute, send, publish, upload, download, or unknown. Server-provided read-only hints are advisory; local policy decides side effects, permission, risk, approval, trust, and availability.

Inputs and outputs are bounded and validated. Side effects use `mcp_executor`; direct calls are rejected. Unknown tools, arbitrary shell, unrestricted filesystem, secret export, administration, installation, and scheduled execution remain disabled.
