# Provider Execution Framework

The Provider Execution Framework is the intelligence layer above the existing Provider Router.
It decides whether a request should use provider execution, which provider is most suitable,
which model metadata should be selected, and what fallback or recovery metadata should be prepared.

The framework does not implement AI calls, network calls, authentication, or provider APIs.
Every future provider request must still pass through the existing `ProviderRouter`.

## Architecture

`provider_execution/` contains small, replaceable components:

- `ExecutionManager` coordinates request analysis, provider selection, model selection, validation, recovery, diagnostics, and history.
- `ProviderExecutionRequest` and `ProviderExecutionResponse` are provider-neutral envelopes.
- `ProviderSelector` ranks providers by capabilities, health, priority, locality, latency, cost metadata, and reliability.
- `ModelSelector` ranks configured model metadata by capabilities, context window, latency, cost, reliability, and preferences.
- `ProviderExecutionRegistry` stores execution-time provider metadata imported from the existing `ProviderManager`.
- `ProviderCapabilities`, `ProviderExecutionHealth`, and `ProviderExecutionMetrics` provide selection data without invoking APIs.
- `ProviderRecovery` prepares fallback and retry metadata without executing retries.
- `ProviderDiagnostics`, `ProviderBenchmark`, `ProviderCache`, and `ProviderExecutionHistory` support future observability and analytics.

## Execution Flow

User input flows through Conversation Engine and Executive JARVIS first. If provider work is needed, the path is:

Conversation Engine -> Executive JARVIS -> Intent -> Decision -> Execution Planner -> Provider Selector -> Model Selector -> Provider Router -> Provider -> Provider Router -> Response Pipeline.

The new framework only prepares this flow. Real provider calls remain intentionally unimplemented.

## Provider Router Boundary

The Provider Router remains the only gateway to AI providers. The execution framework may select providers and models, but it must not call OpenAI, Anthropic, Gemini, Ollama, local models, or any other backend directly.

## Fallback And Recovery

Fallback metadata supports retrying the same model, trying a different model, switching providers, preferring local or cloud providers, queueing recovery, and graceful failure. These are architecture hooks only.

## Startup Integration

Startup initializes the Provider Execution Framework after the existing Provider Router. The startup summary reports registered providers, enabled providers, healthy providers, registered models, execution count, and framework status.

## Extension Guide

Future implementations should add provider-specific execution only inside provider adapters and route those calls through `ProviderRouter`. To extend selection behavior, add metadata to `ProviderExecutionRecord`, `ProviderCapabilities`, or `ModelMetadata`, then update selector ranking rules without changing provider adapters.
