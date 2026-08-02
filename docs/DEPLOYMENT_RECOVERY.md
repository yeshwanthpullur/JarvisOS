# Deployment Recovery

This branch preserves the historical Local Desktop Interface MVP milestone and
adds only the safe, status-only Vercel boundary. The interface is not
redesigned, `main.py` remains CLI-only, and historical failures are unchanged.

## Recovery 13 - Local Desktop Interface MVP

- Original commit: `da6f57a571afb76a9295cd978282ada2e54546dd`
- Replacement branch: `deployment-recovery/13-local-desktop-interface-jarvis-os`
- Canonical project: `jarvis-os`
- Duplicate historical project: `jarvis-os-6oy2` was not used or reconnected
- Replacement commit: pending initial recovery commit
- Deployment URL: pending deployment
- Status: pending verification

Recovery 13 replaces both historical failures tied to this original commit.
Recovery 14 reuses this deployment and does not create a duplicate.

## Safety Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static responses never
read secrets, environment values, user data, local paths, or runtime state.
