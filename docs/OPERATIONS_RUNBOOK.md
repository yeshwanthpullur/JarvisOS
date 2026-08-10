# Operations Runbook

## Startup And Shutdown

Start the primary local CLI with `python main.py`. Use `exit` for clean shutdown. Do not expose the CLI or local model endpoints publicly.

## Diagnostics

Use `project status`, `evaluation status`, `execution status`, and `release-readiness status`. Inspect detailed Prompt 85 gates with `release-readiness gates` and missing prerequisites with `release-readiness missing`.

## Degraded Operation

Optional providers should report unavailable without preventing local CLI startup. Preserve local-only behavior, disable unsupported external actions, and keep critical operations blocked.

## Security Incident

Stop affected local runtimes, revoke applicable external credentials outside JARVIS, retain only bounded non-secret evidence, and inspect approval/execution metadata. Never print `.env` or credential values.

## Recovery

Use Git history and verified configuration backups. Runtime queues, model files, local memory, and generated artifacts are not release artifacts. Prompt 85 does not install a self-healing daemon or distributed recovery service.
