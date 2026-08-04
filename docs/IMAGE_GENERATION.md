# Image Generation Workflow

Updated: 2026-08-04

Image Generation in JARVIS OS is now a governed local-first workflow foundation. It validates prompts, applies a bounded safety policy, normalizes provider behavior, and stores only bounded metadata in local runtime state. It does not expose generation through Vercel, does not upload prompts or images to cloud services by default, and does not pretend generation is available when no real local provider is configured.

## Current Capability

- Structured request planning through `image plan <prompt>`.
- Prompt safety review through `image safety <prompt>`.
- Provider discovery through `image providers`.
- Truthful status reporting through `image status`.
- Dry-run generation routing through `image generate <prompt> --dry-run`.
- Bounded history and job inspection through `image history` and `image show <job_id>`.
- Local metadata persistence under ignored runtime storage only.

The foundation is real, but the default runtime still reports generation as unavailable until a compatible local provider is configured. The included stub provider exists only for tests and internal verification.

## Commands

- `image status`
- `image help`
- `image providers`
- `image plan <prompt>`
- `image safety <prompt>`
- `image generate <prompt>`
- `image generate <prompt> --dry-run`
- `image history`
- `image show <job_id>`

These commands produce bounded outputs and avoid leaking absolute private paths, secrets, provider credentials, raw image bytes, or unbounded prompt history.

## Safety Policy

The workflow blocks or rejects requests involving:

- explicit sexual content
- graphic violence
- self-harm content
- deepfake or real-person impersonation
- identity recognition
- non-consensual intimate imagery
- private personal data visualization
- exact copyrighted-character replication
- political persuasion content
- illegal weapon construction
- safety-bypass requests

Unsafe requests are blocked before provider dispatch. Safe alternatives may be suggested, but JARVIS does not fabricate an image result for blocked prompts.

## Provider Model

The workflow is provider-neutral by design:

- `unavailable` is the truthful default provider.
- Real local providers can be registered later without changing command authority.
- Local-only operation remains the default policy.
- Vercel remains status-only and never calls image generation.

No provider is auto-installed or auto-downloaded. JARVIS does not fetch models or sign in to external image platforms by itself.

## Storage And Privacy

- Runtime output lives under `data/image_generation/`, which is ignored by Git.
- Metadata is bounded and local.
- Full prompt/output provenance is normalized into safe job records.
- No base64 image payloads are stored in audit.
- No user images are modified or deleted.
- No secret-shaped values should appear in command output or metadata files.

## Configuration

Image generation configuration lives under `image_generation`:

| Key | Default | Purpose |
| --- | --- | --- |
| `enabled` | `false` | Enables command execution beyond status/help. |
| `default_provider` | `unavailable` | Selects the active provider. |
| `local_only` | `true` | Prevents non-local routing by default. |
| `output_dir` | `data/image_generation` | Local runtime output directory. |
| `max_prompt_chars` | `600` | Hard bound for prompt length. |
| `max_negative_prompt_chars` | `300` | Hard bound for negative prompt length. |
| `save_metadata` | `true` | Writes bounded local metadata for completed jobs. |
| `allow_overwrite` | `false` | Prevents accidental output replacement. |
| `safety_filter_enabled` | `true` | Applies the safety policy before dispatch. |

## Not Implemented

- Real default local image model integration
- Cloud image providers
- Background batch rendering
- Public sharing or upload flows
- Image editing workflows
- Video editing workflows
- Reverse image search
- Face recognition or identity inference
- Medical, legal, or forensic interpretation

Prompt 41 completes the workflow foundation only. Real local generation still requires a separately configured provider, and Prompt 42 remains responsible for video editing workflows.
