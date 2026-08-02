# Deployment Recovery

## Recovery 23 - Prompt 27 Basic Chat Execution

- Milestone: Complete Prompt 27 basic chat execution
- Verified historical commit: `35f2edeff112a7e8a2696278e2d5302d23f81799`
- Historical failed context: one failed production deployment whose project
  name was not clearly shown in the supplied GitHub summary
- Recovery branch: `deployment-recovery/23-basic-chat-execution-jarvis-os`
- Canonical replacement project: `jarvis-os`
- Replacement commit: pending initial recovery commit
- Replacement deployment URL: pending deployment
- Status: pending verification
- Minimum files changed: `api/index.py`, `vercel.json`, and this bounded record
- Tests: Python compilation, deployment/status/CLI-boundary tests, and focused
  credential-free historical basic-chat tests where practical

The old failed deployment remains untouched. No duplicate project was used,
and `jarvis-os-6oy2` was not connected or contacted.

## Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static status never
reads credentials, environment values, local paths, provider state, prompts,
or user data. Provider routing is unchanged, no paid provider call is made,
and `main.py` remains CLI-only.
