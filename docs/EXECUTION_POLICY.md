# Execution Policy

Every orchestration node carries policy identity, version, effective permissions, and execution class. Delegation may narrow these fields but cannot broaden them.

Heavy model start, stop, install, and download are separate controlled side effects; ordinary configured local inference does not grant tool authority.

A plugin may add capability but never authority; all side effects still require local policy, exact permission, approval, and Broker validation.

MCP discovery, resource read, read tool, and side-effect tool calls are distinct classes. Arbitrary shell/filesystem, secret export, admin, and installation remain blocked.

GitHub issue, PR, and release writes use distinct high-risk actions. Merge, workflow execution, secrets, administration, repository deletion, and force push remain blocked.

Telegram reply, independent send, pairing, unpairing, polling start, and polling stop are distinct actions. Independent send is high-risk and approval-required; critical requests remain blocked regardless of transport.

External communication remains disabled globally and per provider. There is no broad external-action switch that bypasses provider policy.

The execution policy classifies actions by risk, permissions, locality, scope, and mode. The default mode is `plan_only`; critical actions are blocked.

An executable request must name its action, resource, permissions, risk, and expected effect. High-risk requests require an exact unexpired approval. Secret access, unrestricted deletion, force-push, external sending, hidden capture, and uncontrolled hardware actions remain blocked.

Use `execution status`, `execution policy`, `execution classify <action>`, and `execution explain <action>` for bounded diagnostics. These commands never execute the proposed action.
