# Execution Policy

The execution policy classifies actions by risk, permissions, locality, scope, and mode. The default mode is `plan_only`; critical actions are blocked.

An executable request must name its action, resource, permissions, risk, and expected effect. High-risk requests require an exact unexpired approval. Secret access, unrestricted deletion, force-push, external sending, hidden capture, and uncontrolled hardware actions remain blocked.

Use `execution status`, `execution policy`, `execution classify <action>`, and `execution explain <action>` for bounded diagnostics. These commands never execute the proposed action.
