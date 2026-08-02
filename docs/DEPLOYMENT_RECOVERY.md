# Deployment Recovery

This branch preserves the historical voice-cleanup milestone and adds only the
safe, status-only Vercel boundary. `main.py` remains CLI-only and historical
failed deployments remain unchanged.

## Recovery 3 - Voice Cleanup

- Original commit: `ea3bc871e70e5d3355cb5628a96bbed1da749dbe`
- Replacement branch: `deployment-recovery/03-voice-cleanup-jarvis-os`
- Canonical project: `jarvis-os`
- Duplicate historical project: `jarvis-os-6oy2` was not used or reconnected
- Replacement commit: pending initial recovery commit
- Deployment URL: pending deployment
- Status: pending verification

Recovery 3 replaces both historical failures tied to this original commit.
Recovery 4 reuses this deployment and does not create a duplicate.

## Safety Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static responses never
read secrets, environment values, user data, local paths, or runtime state.
