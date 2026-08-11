# Plugin Security

External code is untrusted. In-process external Python, subprocess plugins, unrestricted network/filesystem access, arbitrary shell commands, credential enumeration, `.env` access, automatic dependency installation, automatic updates, scheduled execution, and startup persistence are disabled.

SHA-256 mismatches block verification. Missing signatures are reported as unsigned. Credentials are references and may only be resolved inside a future approved adapter boundary. Plugin and MCP trust are independent. Plugin metadata, documentation, and output remain untrusted data and cannot override policy.
