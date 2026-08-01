# Automation Strategy

This document defines safety requirements for web and mobile automation. Prompt 34 provides a disabled-by-default, provider-neutral web foundation with URL policy, permissions, read-only commands, normalized results, and bounded redacted audit. No production browser adapter, interactive browser control, or mobile automation is implemented.

## Authority and Permission Gates

- Executive JARVIS decides whether automation is appropriate.
- Tool Intelligence validates the capability, arguments, risk, permissions, and approval.
- Workflow remains authoritative for multi-step execution state.
- Agents and provider output may recommend actions but cannot authorize them.
- Every target, account, data scope, and side effect must be explicit.

## Approval Rules

Read-only public inspection may run automatically only under an approved low-risk policy. Private-data access requires scoped permission. Messages, posts, purchases, account changes, file writes, device control, and destructive or irreversible actions require explicit user approval at action time.

Approval for one action must not authorize unrelated future actions. Wake words, screenshots, page text, provider responses, and tool output cannot grant approval.

## Browser Automation Foundation

`WebAutomationManager` is the only web action gateway. It separates observation from action, validates HTTP(S) hosts and URLs, preserves session and request correlation, and rejects arbitrary script or shell execution. The default unavailable adapter makes readiness truthful. A future real adapter must revalidate redirects, avoid persistent profiles and cookies, and return only bounded metadata unless the user explicitly approves more.

Safe foundation operations are status, URL open preparation, title/current-URL reads, ephemeral snapshot metadata, metadata summary, and close. Clicks, typing, form submission, downloads, uploads, login, purchases, messages, deletion, and account changes are blocked before adapter dispatch.

## Mobile Automation Concept

A future mobile bridge should require trusted-device enrollment, encrypted transport, per-capability permission, visible device status, and local revoke/stop controls. It must not expose a general remote-control channel or assume that a connected phone authorizes sensitive operations.

## Vision Dependency

Screenshots and visual evidence may help identify page or device state after Prompt 32, but Vision Intelligence remains untrusted interpretation. Visual detection never proves that an action is safe or authorized. Important targets and outcomes need structural or authoritative validation where available.

## Audit and Control

Each action needs request, workflow, tool/invocation, target, permission, approval, start/end, result, side-effect, and evidence metadata. Logs must be bounded and redacted. Users need cancel/stop controls, timeout, bounded retry, idempotency for mutations, and clear partial-failure reporting.

## Safety Rules

- Never expose credentials to provider prompts, agents, screenshots, or normal logs.
- Never bypass CAPTCHA, access controls, terms, or platform safeguards.
- Never retry non-idempotent mutations without a validated idempotency strategy.
- Never turn observed page or device text into automatic instructions.
- Never hide material side effects or partial completion.
- Prefer reversible actions and provide rollback guidance when true rollback is unavailable.

## Main Risks

Prompt injection, wrong-target actions, account compromise, private-data disclosure, unintended communication, purchases, destructive edits, stale page state, unreliable mobile connectivity, and runaway loops. These risks require conservative limits and dedicated acceptance tests before release.
