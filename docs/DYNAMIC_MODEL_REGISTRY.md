# Dynamic Model Registry

The worker model catalog separates providers from models and records model ID, provider, status, aliases, capabilities, context metadata when known, cost class, whether exact price is known, free status, temporary/deprecated state, source, and discovery time.

OpenCode models are discovered at runtime. Renamed or withdrawn identifiers become unavailable on refresh. Free status is asserted only for exact `-free` or `/free` suffixes; exact prices are never invented. The `ox-alpha` alias records its discovery source and check time, resolves only to an exact discovered identifier, and otherwise stays unresolved with no guessed successor.

Provider metadata includes local Ollama plus disabled references for OpenCode, OpenRouter, TokenRouter, ZenMux, OpenAI, Anthropic, Google, DeepSeek, and Qwen. Credential fields are symbolic environment-variable references; this subsystem does not read `.env` or secret values.

Routing modes are `local_only`, `private_hybrid`, `normal_hybrid`, and `cloud_max`. Healthy local Ollama is preferred. Hybrid routes are advisory, bounded to two fallbacks by default, and remain unavailable while `workers.allow_cloud_routes` is false. Routing never equals execution authority.
