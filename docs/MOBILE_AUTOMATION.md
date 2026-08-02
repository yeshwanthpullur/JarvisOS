# Mobile Automation

## Current Status

Mobile Automation is **Partial**. JARVIS provides a planning-only, provider-neutral manager, strict policy checks, redacted bounded audit records, and CLI commands. Live phone control is not implemented. No real phone adapter, ADB integration, Appium integration, or companion app is enabled.

## What Works Now

- `mobile status`, `mobile policy`, and `mobile capabilities` report honest readiness.
- `mobile setup` explains future Android connection options without executing commands.
- `mobile plan <task>` prepares only safe future workflow guidance.
- `mobile audit` shows bounded action/status metadata without private content.
- `mobile close` clears in-memory planning session state.
- Null and planning-only adapters provide stable extension points and truthful results.

Private mobile data is not accessed. No phone, emulator, Android SDK, ADB process, Appium server, browser profile, or companion service is required.

## Safety Principles

The manager is subordinate to Executive JARVIS and has no independent execution authority. All future requests must pass command or conversation parsing, policy validation, scoped permission validation, the Mobile Automation Manager, an approved adapter, result normalization, and audit recording.

The current foundation blocks messages, notifications, calls, contacts, photos, camera, microphone, location, app control, tap/type/swipe, file transfer, installation, settings, purchases, login, unlock, and background monitoring. An agent, plan, workflow, provider response, or tool output cannot approve these actions.

## Privacy Rules

JARVIS does not store message content, contacts, call details, photos, screenshots, location, recordings, app content, authentication tokens, IMEI, phone numbers, or hardware serial numbers. Audit entries contain only action category, risk, policy decision, status, adapter ID, a fixed safe summary, and an error code. Retention is bounded by `mobile.audit_retention`.

## Permission Model

Current read permissions cover status, policy, setup guidance, capability summaries, connection planning, and audit summaries. Every permission involving device connection, private data, communication, sensors, device input, files, apps, settings, payment, authentication, unlock, or monitoring remains blocked.

## Future Android Support

A future milestone may add one explicitly configured adapter using ADB, an Android emulator, Appium, or a local companion app. It must require visible device enrollment, a revocable local alias, scoped permissions, explicit approval for sensitive actions, encrypted transport where applicable, and a stop control. USB debugging or a local-network bridge must never imply blanket authorization.

Cross-device synchronization remains a separate authority. A companion app must not become a hidden remote-control channel and must not sync secrets or private phone content by default.

## Audit And Troubleshooting

Use `mobile status`, then `mobile policy` and `mobile audit`. `planning_only` with `real_phone_adapter=no` is the expected state. `MOBILE_ACTION_BLOCKED` and `MOBILE_PRIVATE_DATA_BLOCKED` mean policy stopped the request before device access. No bypass of Android permissions, lock screens, authentication, or application protections is supported.

## Known Limitations

- No real phone adapter or live device discovery.
- No approval-gated mobile action execution.
- No companion app.
- No mobile cross-device synchronization.
- No background operation, sensor access, communication, or private-data access.
