# Adding Providers

Providers are replaceable adapters. A provider implementation must depend on the `BaseProvider` contract, not on agents, desktop code, or task persistence.

## Required Interface

Every provider must implement:

- `capabilities()`
- `is_available()`
- `estimate_cost(request)`
- `execute(request)`

The current provider classes are placeholders:

- `OpenAIProvider`
- `AnthropicProvider`
- `GoogleProvider`
- `OpenRouterProvider`
- `LocalProvider`
- `FutureProvider`

They exist to establish naming and extension points. They do not call provider APIs.

## Configuration

Provider configuration belongs in `config.yaml`:

```yaml
providers:
  default_provider: ""
  enabled_providers: []
  timeout_seconds: 30
  max_retries: 2
  track_costs: true
  definitions: {}
```

Future provider-specific settings should be stored under `definitions` by provider name. Secrets should be supplied through environment variables or a future secrets manager, not committed to source control.

## Router Responsibilities

Future router behavior should include:

- Provider selection
- Failover
- Retry policy
- Timeout handling
- Cost tracking
- Capability detection
- Model selection

The router should make these decisions from provider capabilities, settings, and request context. It should not hardcode one provider as special.

