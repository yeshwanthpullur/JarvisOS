# Deployment Recovery

## Recovery 23 - Prompt 27 Basic Chat Execution

- Milestone: Complete Prompt 27 basic chat execution
- Verified historical commit: `35f2edeff112a7e8a2696278e2d5302d23f81799`
- Historical failed context: one failed production deployment whose project
  name was not clearly shown in the supplied GitHub summary
- Recovery branch: `deployment-recovery/23-basic-chat-execution-jarvis-os`
- Canonical replacement project: `jarvis-os`
- Replacement commit: `99a45498aff777bd182b139fafd0fa032778d65a`
- Replacement deployment URL: `https://jarvis-j6bemz9lf-jj1-e21e.vercel.app`
- Status: `READY`; `/api/status` returned HTTP 200 bounded JSON
- Minimum files changed: `api/index.py`, `vercel.json`, and this bounded record
- Tests: Python compilation; 3 deployment/status/CLI-boundary tests and 9
  credential-free historical cloud/basic-chat integration tests passed

The old failed deployment remains untouched. No duplicate project was used,
and `jarvis-os-6oy2` was not connected or contacted.

## Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static status never
reads credentials, environment values, local paths, provider state, prompts,
or user data. Provider routing is unchanged, no paid provider call is made,
and `main.py` remains CLI-only.
