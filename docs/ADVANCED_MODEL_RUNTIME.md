# Advanced Model Runtime

Prompt 78 separates model profiles, inference runtimes, provider endpoints, hardware plans, and routing policy. Ollama, vLLM, llama.cpp, NVIDIA NIM, and generic OpenAI-compatible endpoints are peer runtime options. Detection and status are read-only; no runtime, container, driver, model, or dependency is installed or started automatically.

Routing defaults to local-preferred with remote and paid routes disabled. It considers capabilities, runtime availability, endpoint locality, secrets, context limits, resource plans, fallback limits, and circuit state. Model output is bounded and cannot execute tools or change policy.
