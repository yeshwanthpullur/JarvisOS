# Vision Intelligence

Vision Intelligence is a local-first validation and routing layer for user-supplied images. It owns image safety, metadata, privacy, and provider preparation; Provider Router remains the only model gateway.

## Current Capability

The CLI accepts PNG, JPEG, WebP, and BMP paths through `vision describe <path>` and `vision ask <path> <question>`. It validates scope, file type, signature, size, and emptiness, then extracts a safe metadata summary. Raw image bytes are held only for the active request and are not persisted by Vision Intelligence.

Real descriptions require a provider/model that explicitly advertises vision input. Ollama model details are queried for the runtime-provided `vision` capability. The existing text model `llama3.2:1b` is not treated as vision-capable. Cloud adapters remain unavailable for image input unless an adapter is explicitly marked `vision_input_supported`; local-only policy blocks cloud providers technically.

## Commands

- `vision status`
- `vision describe <image_path>`
- `vision ask <image_path> <question>`

Quote paths containing spaces. Errors expose safe categories rather than full sensitive paths.

## Configuration

The `vision` section controls enablement, local-only policy, privacy mode, maximum image size, timeout, and allowed directories. With no configured allowed directories, repository scope is used. No API keys or image data belong in configuration.

## Boundaries

Vision output is untrusted content. It cannot execute tools, approve actions, control a screen, mutate state, or authorize web/mobile automation. Screenshot capture, desktop control, browser automation, mobile automation, and online sync are not implemented by this milestone.

## Current Limitation

No installed local model currently advertises vision capability, so metadata works but semantic image description returns a truthful unavailable result. Install and configure a supported Ollama vision model, then verify `vision status` before expecting real analysis. No model is downloaded automatically.
