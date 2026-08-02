# Deployment Recovery

## Recovery 19 - Prompt 29 Tool Intelligence

- Milestone: Implement Prompt 29 - Tool Intelligence
- Historical commit: `379fc5b719743b2a3b64dd244d9e615bfdd66480`
- Historical failed projects: `jarvis-os` and `jarvis-os-6oy2`
- Recovery branch: `deployment-recovery/19-tool-intelligence-jarvis-os`
- Canonical replacement project: `jarvis-os`
- Replacement commit: pending initial recovery commit
- Replacement deployment URL: pending deployment
- Status: pending verification
- Minimum files changed: `api/index.py`, `vercel.json`, and this bounded record
- Tests: Python compilation, deployment/status/CLI-boundary tests, and focused
  historical Tool Intelligence tests where practical

The old failures remain untouched. `jarvis-os-6oy2` was not used or
reconnected. Recovery 20 reuses this canonical replacement and creates no
additional branch or deployment.

## Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static status never
reads secrets, credentials, environment values, local paths, tool state, or
user data. Tool permissions and execution behavior are unchanged, and
`main.py` remains CLI-only.
