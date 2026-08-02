# Deployment Recovery

This branch preserves a historical JARVIS OS milestone while adding only the
safe, status-only Vercel deployment boundary. The local `main.py` entry point
remains CLI-only. Historical failed deployments are retained unchanged.

## Recovery 1 - Vision Foundation

- Original commit: `c69bcab6a554846c5f2b13299bd11bac207134fd`
- Replacement branch: `deployment-recovery/01-vision-foundation-jarvis-os`
- Canonical project: `jarvis-os`
- Duplicate historical project: `jarvis-os-6oy2` was not used or reconnected
- Replacement commit: pending initial recovery commit
- Deployment URL: pending deployment
- Status: pending verification

Recovery 1 is the single replacement for both historical Vercel failures tied
to the original commit. Recovery 2 therefore reuses this record and does not
create a duplicate deployment.

## Safety Boundary

The deployment exposes only `/`, `/api/health`, and `/api/status`. Responses
contain static project-status metadata and do not read environment values,
credentials, user data, local paths, or runtime state.
