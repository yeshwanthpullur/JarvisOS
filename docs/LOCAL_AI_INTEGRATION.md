# Local AI Integration

Local AI Integration extends the existing Provider Router and Provider Execution Framework with real local-runtime discovery, model inventory, execution, normalization, and truth-preserving failure reporting.

## Purpose

This layer lets JARVIS use locally available models without bypassing Executive JARVIS, Provider Router policy, or any existing authority boundaries.

## Architecture

- Provider Router remains the only model gateway.
- `providers/local_provider.py` supports a local OpenAI-compatible HTTP runtime.
- `providers/ollama_provider.py` supports the Ollama local HTTP API.
- `provider_execution/` prepares selection, fallback, and health metadata.
- `core/startup_manager.py` and `core/health_checker.py` expose readiness and health.
- `commands/` exposes local status, listing, refresh, selection explanation, and local-only toggles.

## Supported Local Provider Types

- Ollama when reachable on a local endpoint.
- Local OpenAI-compatible runtimes on loopback or explicitly trusted local endpoints.

## Locality Verification

Local-only execution is allowed only when locality can be established from loopback, approved local executables, or explicitly trusted local configuration. Unverified remote endpoints are rejected.

## Model Discovery

Discovery reads the real runtime model inventory and records provider-owned model metadata. Unknown values stay unknown.

## Selection And Execution

Provider selection considers locality, availability, health, capability fit, context limits, and explicit user preference. Actual requests are sent through `ProviderRouter` only.

## Local-Only Policy

If the user or request metadata requires local-only execution, the router filters to verified local providers and does not fall back to cloud providers.

## Streaming, Cancellation, And Timeouts

Streaming, cancellation, and timeout handling are supported when the underlying runtime and adapter expose those behaviors safely. Partial output is never reported as a complete result.

## Failure Handling

The system reports truthful states such as unavailable runtime, missing model, malformed response, timeout, cancellation, policy rejection, and context-limit failure.

## Limitations

- No cloud providers are implemented in this prompt.
- Real runtime generation can only be verified when a compatible local runtime and model are actually installed on the machine.
- Automatic model download is intentionally out of scope.
