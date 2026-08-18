# Local AI Stack

Phase 6 records GENERAL, FAST, REASONING, CODING, VISION, EMBEDDING, and fallback roles without downloading models. Ollama health is probed only on explicit diagnostics; llama.cpp, LiteLLM, and vLLM remain truthful disabled/unconfigured routes unless separately installed and enabled.

Ollama remains the primary local model runtime. The native JARVIS Provider Registry remains authoritative; LiteLLM is an optional disabled gateway and cannot override local-only, approval, egress, or provider policies. llama.cpp is an unconfigured backup, while vLLM is deferred to a suitable Linux/CUDA host.

Model metadata declares the roles `general_chat`, `reasoning`, `coding`, `summarization`, `document_qa`, `research_synthesis`, `vision`, `fast_response`, `fallback`, and `embedding`. Selection prefers the smallest healthy local model that supports the requested role. Availability, detection, configuration, enablement, policy permission, approval, and health are separate states.

`llama3.2:1b` is the lightweight general-chat baseline when installed. `llava:latest` is the local vision baseline when installed. Coding and embedding models remain unselected until an installed model truthfully advertises those roles.

Commands such as `provider inspect ollama`, `provider test ollama`, `model list`, `model health`, `model inspect <model>`, `model roles`, `model select <role> <model>`, and `model test <model>` expose bounded metadata. Model test does not download a model or execute inference; normal chat is the governed inference path.
