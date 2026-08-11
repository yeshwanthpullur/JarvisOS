# Workflow Security

The Workflow Engine is a coordinator, not an authority. Executive JARVIS remains the entry authority, Prime remains the coordinator, Execution Policy decides what is permitted, the Approval System validates exact grants, and the Execution Broker is the only route to action-specific executors.

Workflow inputs, events, artifacts, and checkpoints are bounded and redacted. Credentials, approval tokens, cookies, raw provider responses, private files, raw memory, and transcripts are excluded. Privacy and data-egress scope can only stay the same or become more restrictive as a workflow progresses.

Critical actions remain blocked. Unrestricted background and scheduled execution, unbounded retries, self-modifying workflows, silent memory writes, hidden microphone/camera access, arbitrary plugin/MCP execution, and direct provider calls are not introduced.
