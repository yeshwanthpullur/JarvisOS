# Operations Runbook

## Startup And Shutdown

Start the primary local CLI with `python main.py`. Use `exit` for clean shutdown. Do not expose the CLI or local model endpoints publicly.

## Diagnostics

Use `project status`, `evaluation status`, `execution status`, and `release-readiness status`. Inspect gates, contracts, compatibility, scenarios, scorecard, and checklist with the bounded `release-readiness` diagnostics.

## Degraded Operation

Optional providers should report unavailable without preventing local CLI startup. Preserve local-only behavior, disable unsupported external actions, and keep critical operations blocked.

## Security Incident

Stop affected local runtimes, revoke applicable external credentials outside JARVIS, retain only bounded non-secret evidence, and inspect approval/execution metadata. Never print `.env` or credential values.

## Recovery

Use Git history and verified configuration backups. Runtime queues, model files, local memory, and generated artifacts are not release artifacts. Follow `DISASTER_RECOVERY_PLAN.md`; Prompt 85 does not install a self-healing daemon or distributed recovery service.

## Provider Outage

Inspect provider health and circuit state, keep cloud fallback disabled unless separately configured, and return a truthful unavailable or degraded result. Never expose a local model endpoint publicly.

## Workflow Recovery

Inspect bounded workflow and checkpoint metadata, validate Policy and Approval state again, and resume only through the owning workflow path. Recovery planning cannot grant permission.

## Configuration Validation

Validate `config.yaml` and machine-readable project health before startup. Restore reviewed non-secret configuration from version control; restore credentials only through their external authority.
