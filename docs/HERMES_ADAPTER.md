# Hermes Adapter

Hermes is integrated as an optional, non-authoritative external worker. The adapter exposes the full common lifecycle contract and detects the Windows launcher with a bounded version check. The local launcher responded as Hermes Agent `0.20.4` during verification; an isolated source checkout may have a different version, so runtime diagnostics report the launcher and detected version without exposing a private installation path or treating another checkout as canonical.

Hermes task execution remains disabled. `start_task` creates a plan-only record; `send_context` accepts opaque references only; `request_approval` redirects authority to JARVIS; cancellation and resume manage retained plan metadata. Hermes cannot bypass Prime, Approval, Policy, Broker, Git review, or worktree isolation.
