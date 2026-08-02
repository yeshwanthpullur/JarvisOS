# Deployment Recovery

## Recovery 15 - Prompt 31 Voice Intelligence

- Milestone: Implement Prompt 31 - Voice Intelligence
- Historical commit: `050380a70f5442841c7febcfbf70881fdf2b7048`
- Historical failed projects: `jarvis-os` and `jarvis-os-6oy2`
- Recovery branch: `deployment-recovery/15-voice-intelligence-jarvis-os`
- Canonical replacement project: `jarvis-os`
- Replacement commit: pending initial recovery commit
- Replacement deployment URL: pending deployment
- Status: pending verification
- Minimum files changed: `api/index.py`, `vercel.json`, and this bounded record
- Tests: Python compilation and three deployment/status/CLI-boundary tests

The old failed deployments remain untouched. The duplicate project
`jarvis-os-6oy2` was not used or reconnected. Recovery 16 reuses this single
canonical replacement and creates no additional branch or deployment.

## Boundary

The deployment exposes only `/`, `/api/health`, and `/api/status`. It returns
bounded static status and never reads secrets, environment values, local paths,
logs, voice data, audio, private configuration, or runtime state. Historical
Voice Intelligence behavior is unchanged and `main.py` remains CLI-only.
