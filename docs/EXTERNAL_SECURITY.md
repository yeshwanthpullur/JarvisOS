# External Integration Security

MCP servers are untrusted and cannot self-authorize. Local subprocesses receive a minimal environment; remote endpoints require explicit policy and cannot weaken Browser Read SSRF controls.

GitHub access is allowlisted to explicit repositories. External code is untrusted, structured `gh` calls never use a shell, and service mutations require egress checks, exact approval, and Broker validation.

Telegram applies private-owner pairing, replay protection, fixed endpoints, bounded input, content-free audit, and exact approval/Broker gates. Unknown users, groups, unsupported media, and policy-changing prompts remain untrusted or blocked.

External communication adds exact destination, content fingerprint, attachment, rate, and duplicate checks. Material recipient, content, or attachment changes require a new future approval.

Phase 4 Approval System, Execution Policy, and Broker remain the only authorities for side effects. The control plane cannot grant approval or execute an action.

External actions declare capability, permissions, risk, approval, side effects, data classification, provider health, and cost. High-risk operations require exact approval in future owning prompts. Critical, secret-access, unconfigured, disabled, paid, MCP, plugin, and remote actions remain blocked.

Retries are bounded and must never retry authentication, authorization, policy, approval, or secret-egress failures. Diagnostics contain metadata only.
