# Deployment Recovery

This branch preserves the historical Prompts 27 through 31.5 stabilization
milestone and adds only the safe, status-only Vercel boundary. Existing
stabilization behavior is unchanged and `main.py` remains CLI-only.

## Recovery 11 - Prompts 27 Through 31.5 Stabilization

- Original commit: `095bd26292722ae4fa7715e70714df315b23abd5`
- Replacement branch: `deployment-recovery/11-prompts-27-31-5-jarvis-os`
- Canonical project: `jarvis-os`
- Duplicate historical project: `jarvis-os-6oy2` was not used or reconnected
- Replacement commit: `4d85bc2da907046dbd0f920f2053aa32a321a0e7`
- Deployment URL: `https://jarvis-oo24bxu1d-jj1-e21e.vercel.app`
- Status: `READY`

Recovery 11 replaces both historical failures tied to this original commit.
Recovery 12 reuses this deployment and does not create a duplicate.

## Safety Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static responses never
read secrets, environment values, user data, local paths, or runtime state.
