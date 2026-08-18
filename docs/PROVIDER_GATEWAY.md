# Provider Gateway

Provider routing is local-first and fail-closed. Ollama is the primary local runtime. LiteLLM may later normalize configured provider calls, but it is disabled by default and cannot bypass the JARVIS Provider Registry, Execution Policy, Approval System, data-egress checks, or local-only mode.

Provider status distinguishes configured, detected, enabled, policy-allowed, approval-required, and healthy. A cloud provider is never selected silently. Provider failures return bounded diagnostics and do not route ordinary chat into goals, auto-install software, download models, or retry indefinitely.
