# Command Execution Sandbox

Command execution uses argument arrays with `shell=False`, a configured allowlist, a scoped working directory, a sanitized environment, bounded output, and a hard timeout.

Shell interpreters, metacharacters, network commands, package installation, destructive utilities, Git writes, and secret access are blocked. This is a policy sandbox, not an operating-system security boundary.

Use `command status`, `command allowlist`, `command plan`, and approved `command execute`. Commands remain disabled outside the narrow allowlist.
