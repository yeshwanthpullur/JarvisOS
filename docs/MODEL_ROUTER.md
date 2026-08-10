# Model Provider Registry and Router

## Batch 2 Capabilities

The metadata router represents document Q&A, browser summarization, scheduler planning, communication drafting, adapter planning, research, and summarization. Advanced-provider profiles remain planning-only and do not alter existing Ollama execution paths.

Updated: 2026-08-10

Model Router provides provider-neutral metadata and deterministic route planning. Existing Ollama chat and local Ollama vision execution paths remain intact; the Phase 3 router does not replace or invoke them.

## Providers

The registry can describe Ollama, llama.cpp, vLLM, LiteLLM, NVIDIA NIM, Nemotron, OpenAI-compatible endpoints, local processes, and test stubs. Status is truthful:

- Ollama text and vision readiness is derived from existing initialized runtime metadata.
- llama.cpp and vLLM are not configured.
- LiteLLM and NVIDIA NIM are disabled or not configured.
- Nemotron is planned but not installed or configured.
- Cloud providers are disabled by default and require a future explicit policy.

No provider is installed, downloaded, contacted, or given credentials by registry or route commands.

## Routing Policy

Routes are local-only by default. A preferred provider is advisory and must be enabled, ready, local when required, and capability-compatible. Missing routes return an unavailable result with bounded fallback metadata.

Research planning requests map to the local reasoning capability. This route is advisory metadata only: it neither performs research nor calls a model. Ollama may be selected only when the existing local provider is ready; Nemotron, vLLM, llama.cpp, cloud, and external-search routes remain unavailable unless separately configured in a future milestone.

Coding requests map to the `coding` capability as advisory metadata. When no ready local coding provider is detected, `model route "coding"` reports unavailable or a truthful fallback. The router does not install a coding model, call a cloud provider, or grant code-execution authority.

Safe hardware discovery reports only broad CPU, memory, architecture, GPU/CUDA availability hints. It does not expose machine identifiers.

## Commands

Use `model status`, `model providers`, `model capabilities`, `model route "<task>"`, `model explain "<task>"`, `model hardware`, and `model policy`.

Routing is a decision, not model execution.
