# Vision Intelligence

Vision Intelligence provides optional real local image analysis through the registered Ollama provider. It validates images, applies privacy and safety policy, and submits approved requests through the existing Provider Router. It does not create a second provider or execution authority.

Local Ollama LLaVA image description and image question answering are manually verified on the current machine. This establishes working local still-image analysis, not live camera/video vision, reverse image search, image generation, identity recognition, or guaranteed OCR accuracy.

## Current Capability

- Validates PNG, JPEG, and WebP files by path, extension, signature, scope, size, and non-empty content.
- Extracts bounded metadata such as safe basename, size, modified time, and dimensions when available.
- Discovers installed Ollama models and accepts only a configured model that advertises the `vision` capability.
- Sends image bytes as request-scoped base64 to the local Ollama `/api/chat` path through Provider Router.
- Normalizes completed, unavailable, invalid, blocked, failed, and timed-out results.
- Keeps a bounded metadata-only audit. Image bytes, base64, prompts, and absolute paths are not retained.

The verified machine currently runs Ollama with `llama3.2:1b` only. That text model does not advertise vision, so real image analysis is unavailable on this machine. Mocked adapter tests prove the request and normalization path, not a real model result.

## Local Setup

1. Install Ollama separately and keep it bound to the local machine.
2. Install a vision-capable model yourself, for example `ollama pull llava` or a specific compatible tag such as `llava:7b`.
3. Set `vision.model` to the installed model name. JARVIS defaults to `llava` and accepts the installed tagged form when the base name matches.
4. Keep `vision.ollama_host` aligned with the registered Ollama provider host. The default is `http://127.0.0.1:11434`.
5. Run `vision models`, then `vision status`. Real analysis is ready only when both Ollama and the configured model are available.

JARVIS never downloads a model automatically and does not require an internet connection after Ollama and the model are installed.

## Commands

- `vision status`
- `vision models`
- `vision analyze <image_path>`
- `vision describe <image_path>`
- `vision ask <image_path> <question>`
- `vision audit`
- `vision cleanup`

Quote paths containing spaces. `vision cleanup` clears JARVIS vision audit metadata only; it never deletes user images.

## Configuration

| Key | Default | Purpose |
| --- | --- | --- |
| `vision.enabled` | `true` | Makes explicit vision CLI commands available; it never starts background capture. |
| `vision.local_only` | `true` | Restricts image analysis to local providers. |
| `vision.provider` | `ollama` | Selected provider family for this adapter. |
| `vision.model` | `llava` | Required local vision model name. |
| `vision.ollama_host` | `http://127.0.0.1:11434` | Expected local Ollama endpoint. |
| `vision.timeout_seconds` | `60` | Bounded model-call timeout. |
| `vision.max_image_size` | `20000000` | Maximum accepted image bytes. |
| `vision.audit_enabled` | `true` | Records bounded metadata-only events. |
| `vision.audit_retention` | `100` | Maximum retained audit events. |
| `vision.store_image_content` | `false` | Fixed privacy default; image content is not persisted. |
| `vision.allowed_directories` | `[]` | Optional path allowlist; repository scope is used when empty. |

## Safety And Privacy

Images remain local and are never sent to cloud providers. Vision requests that ask for real-person identification, face recognition, sensitive-trait inference, medical diagnosis, or legal/forensic certainty are blocked before provider dispatch. A model may describe visible non-sensitive details, but its output is probabilistic and must be verified for important decisions.

Vision output cannot execute tools, approve actions, control a screen, mutate state, or authorize web/mobile automation. Audit records contain no image data, full path, full prompt, credential, or base64 payload.

## Troubleshooting

- `ollama_unavailable`: start the local Ollama service and retry `vision status`.
- `model_missing`: install/configure a model that advertises vision; a model name alone is not accepted as proof.
- `unsupported_image_format`: convert the file to PNG, JPEG, or WebP.
- `image_path_outside_allowed_scope`: move the file into an allowed directory or explicitly configure a safe scope.
- `timed_out`: retry with a smaller image or increase the bounded timeout conservatively.

Vercel remains status-only. It does not call Ollama, accept image uploads, or perform vision analysis. Deployment Protection may redirect anonymous status requests without affecting local vision.

## Not Implemented

Live camera capture, real-time video, face recognition, person identification, biometric or sensitive-trait classification, guaranteed OCR, medical diagnosis, legal/forensic certainty, cloud vision, surveillance, autonomous visual decisions, and Vercel-hosted vision are not implemented.
