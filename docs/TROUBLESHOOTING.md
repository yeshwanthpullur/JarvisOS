# Troubleshooting

Start with `status`, `project status`, `provider status`, `local status`, and `engineering status`. A `DEGRADED` or `UNCONFIGURED` result is preferable to a fabricated success.

- No local model: use typed/plan-only workflows; do not enable cloud fallback implicitly.
- No microphone/model: use typed input; hidden listening is never a fallback.
- Research unavailable: use project documents and a plan-only result; do not invent citations.
- Tool/MCP unavailable: inspect metadata only; discovery does not grant trust or execution.
- Runtime failure: stop safely, inspect bounded logs, and use recovery/checkpoint commands.
- Customer work: verify the isolated workspace before opening any source or artifact.

Never fix a runtime problem by weakening approval, privacy, or path boundaries.
