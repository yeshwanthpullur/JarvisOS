# Deployment Recovery

This branch preserves the historical project-health milestone and adds only
the safe, status-only Vercel boundary. `main.py` remains CLI-only and old
failed deployments remain unchanged.

## Recovery 5 - Project Health Tracking

- Original commit: `69d9521cad5266bf5048d2636faeea452774eeab`
- Replacement branch: `deployment-recovery/05-project-health-jarvis-os`
- Canonical project: `jarvis-os`
- Duplicate historical project: `jarvis-os-6oy2` was not used or reconnected
- Replacement commit: `80b94a2d2681567d06fb2fa03954892e8178120a`
- Deployment URL: `https://jarvis-ium6pgwlx-jj1-e21e.vercel.app`
- Status: `READY`

Recovery 5 replaces both historical failures tied to this original commit.
Recovery 6 reuses this deployment and does not create a duplicate.

## Safety Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static responses never
read secrets, environment values, user data, local paths, or runtime state.
