# Deployment Recovery

This branch preserves the historical voice-playback/interface milestone and
adds only the safe, status-only Vercel boundary. Voice and interface behavior
are unchanged, `main.py` remains CLI-only, and old failures remain untouched.

## Recovery 9 - Voice Playback and Interface Redesign

- Original commit: `cada14eeac82f5a35337886aa45e13702ae993e5`
- Replacement branch: `deployment-recovery/09-voice-playback-interface-jarvis-os`
- Canonical project: `jarvis-os`
- Duplicate historical project: `jarvis-os-6oy2` was not used or reconnected
- Replacement commit: pending initial recovery commit
- Deployment URL: pending deployment
- Status: pending verification

Recovery 9 replaces both historical failures tied to this original commit.
Recovery 10 reuses this deployment and does not create a duplicate.

## Safety Boundary

Only `/`, `/api/health`, and `/api/status` are exposed. Static responses never
read secrets, environment values, user data, local paths, or runtime state.
