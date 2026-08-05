# Video Editing Workflow

Updated: 2026-08-06

Video Editing in JARVIS OS is a governed local-first video editing workflow foundation. It validates prompts, applies a bounded safety policy, normalizes provider behavior, and stores only bounded metadata in local runtime state. It does not expose editing through Vercel, does not upload project media to cloud services by default, and does not pretend live editor control exists when no real local provider is configured.

## Current Capability

- Structured non-destructive edit planning through `video plan <prompt>`.
- Prompt safety review through `video safety <prompt>`.
- Provider discovery through `video providers`.
- Truthful status reporting through `video status`.
- Bounded history and plan inspection through `video history` and `video show <plan_id>`.
- Local metadata persistence under ignored runtime storage only.

The foundation is real, but the default runtime still reports editing as unavailable until a compatible local provider is configured. The included stub provider exists only for tests and internal verification.

## Commands

- `video status`
- `video help`
- `video providers`
- `video plan <prompt>`
- `video safety <prompt>`
- `video history`
- `video show <plan_id>`

These commands produce bounded outputs and avoid leaking absolute private paths, secrets, provider credentials, raw media bytes, or unbounded prompt history.

## Safety Policy

The workflow blocks or rejects requests involving:

- explicit sexual content
- self-harm content
- graphic violence
- deepfake or real-person impersonation
- identity recognition
- non-consensual intimate imagery
- private personal data visualization
- illegal weapon construction
- political persuasion content
- safety-bypass requests
- hidden recording or surveillance
- misleading evidence or deceptive edits

Unsafe requests are blocked before provider dispatch. Safe alternatives may be suggested, but JARVIS does not fabricate a plan result for blocked prompts.

## Provider Model

The workflow is provider-neutral by design:

- `unavailable` is the truthful default provider.
- Real local providers can be registered later without changing command authority.
- Local-only operation remains the default policy.
- Vercel remains status-only and never calls video editing.

No provider is auto-installed or auto-downloaded. JARVIS does not fetch editing models or sign in to external media platforms by itself.

## Storage And Privacy

- Runtime output lives under `data/video_editing/`, which is ignored by Git.
- Metadata is bounded and local.
- Full prompt/provenance is normalized into safe plan records.
- No raw media payloads are stored in audit.
- No user videos are modified or deleted.
- No secret-shaped values should appear in command output or metadata files.

## Configuration

Video editing configuration lives under `video_editing`:

| Key | Default | Purpose |
| --- | --- | --- |
| `enabled` | `false` | Enables command execution beyond status/help. |
| `default_provider` | `unavailable` | Selects the active provider. |
| `local_only` | `true` | Prevents non-local routing by default. |
| `output_dir` | `data/video_editing` | Local runtime output directory. |
| `max_prompt_chars` | `600` | Hard bound for prompt length. |
| `max_source_media_items` | `12` | Hard bound for input clip count. |
| `save_metadata` | `true` | Writes bounded local metadata for completed plans. |
| `allow_overwrite` | `false` | Prevents accidental plan replacement. |
| `safety_filter_enabled` | `true` | Applies the safety policy before dispatch. |

## Not Implemented

- Real default local editor integration
- Cloud video providers
- Background batch rendering
- Public sharing or upload flows
- Non-destructive clip rendering
- Reverse media search
- Face recognition or identity inference
- Medical, legal, or forensic interpretation

Prompt 42 completes the workflow foundation only. Real local editing still requires a separately configured provider, and Prompt 43 remains responsible for encrypted remote sync.
