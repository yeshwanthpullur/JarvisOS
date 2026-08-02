# Deployment Recovery

This branch preserves the historical CLI voice milestone and adds only the
safe, status-only Vercel boundary. Voice behavior is unchanged, `main.py`
remains CLI-only, and old failed deployments remain unchanged.

## Recovery 7 - CLI Voice Stabilization

- Original commit: `d2bcb28d988b098c73e98199fc646c08b95f248e`
- Replacement branch: `deployment-recovery/07-cli-voice-stabilization-jarvis-os`
- Canonical project: `jarvis-os`
- Duplicate historical project: `jarvis-os-6oy2` was not used or reconnected
- Replacement commit: pending initial recovery commit
- Deployment URL: pending deployment
- Status: pending verification

Recovery 7 replaces both historical failures tied to this original commit.
Recovery 8 reuses this deployment and does not create a duplicate.

## Safety Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static responses never
read secrets, environment values, user data, local paths, or runtime state.
