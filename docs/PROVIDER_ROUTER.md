# Provider Router

The Provider Router is the intelligence gateway of JARVIS OS. Every future AI interaction must flow through `ProviderRouter`; agents and higher-level systems must never call a vendor SDK directly.

## Architecture

The provider layer is split into small responsibilities:

- `BaseProvider` defines the provider interface.
- `ProviderConfig` stores configuration from `config.yaml`, environment variables, and future secret managers.
- `ProviderLoader` discovers configured providers.
- `ProviderFactory` creates provider adapters without making API calls.
- `ProviderRegistry` stores provider records and lifecycle state.
- `ProviderManager` coordinates discovery, registration, health checks, enable, disable, reload, remove, and startup statistics.
- `ProviderRouter` selects the best provider for a task.
- `ProviderHealth` tracks availability, latency, failures, retry count, and last successful request.
- `ProviderMetrics` tracks tokens, estimated cost, response time, requests, and failures.
- `ProviderCache` defines future response, model, and capability cache interfaces.

## Supported Provider Interfaces

The framework includes no-network interfaces for:

- OpenAI
- Anthropic
- Google Gemini
- Ollama
- DeepSeek
- Mistral
- Groq
- OpenRouter
- LM Studio
- Custom providers
- Future providers

No provider API calls are implemented.

## Capability System

Providers advertise capabilities:

- chat
- reasoning
- coding
- vision
- speech
- embedding
- transcription
- image generation
- function calling
- streaming
- JSON mode

Providers also support future model metadata, including context window, maximum tokens, and preferred task types.

## Routing

Routing is capability based. A request declares a task type such as coding, reasoning, vision, speech, embedding, transcription, or image generation. The router filters providers by:

- enabled state
- health
- required capability
- local-only or offline requirements
- preferred provider
- preferred model

If the preferred provider is unavailable or incapable, the router falls back to another matching provider.

Local AI support is provider-neutral and adapter-backed. The router can discover and select local providers such as Ollama or a trusted local OpenAI-compatible endpoint, but only when locality and capability checks succeed.

## Provider Lifecycle

Provider lifecycle is managed through `ProviderManager`:

- discover
- register
- initialize
- enable
- disable
- reload
- remove
- shutdown

Health checks in this foundation are local adapter checks only. They do not contact external services.

Local-only policy must be enforced in the router, not in Executive JARVIS or the conversation layer. If a request requires local execution and no verified local provider is available, the router must fail truthfully instead of silently falling back elsewhere.

## Configuration

Provider behavior is configuration-driven. API keys, provider URLs, and model names must never be hardcoded. Provider definitions belong in `config.yaml` or environment-backed configuration, and secrets should use environment variables or a future secrets manager.

## Future Provider Implementation Guide

To implement a real provider later:

1. Add or extend a provider class that inherits from `BaseProvider`.
2. Keep SDK and network details inside that provider class.
3. Advertise capabilities accurately.
4. Read secrets by environment variable name, not literal key value.
5. Return provider-neutral `ProviderResponse` objects.
6. Record metrics and health state.
7. Add tests without requiring live network access.

Agents, Brain modules, Tasks, Memory, Knowledge, Plugins, and future automation should depend on `ProviderRouter`, not on a specific provider.
