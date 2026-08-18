# Environment Isolation

Prompt 88 introduces passive per-tool environment records and `environment audit`. The current global Python 3.13 process is not treated as the authoritative optional-tool environment. Python 3.11/3.12 isolated environments are recommended; none are created or modified by diagnostics.

Final validation created the ignored core `.venv` with Python 3.11.15 and installed only PyYAML 6.0.3 from `requirements.txt`. Its `pip check` passes. Known global Python 3.13 optional browser-package conflicts remain untouched and non-authoritative.

JARVIS OS keeps its core runtime separate from optional AI tools. Installation is not authorization: every detected tool remains disabled until its adapter, policy, permissions, approval requirements, and broker route allow a specific action.

## Runtime layout

The intended environments are `tools/browser/.venv`, `tools/research/.venv`, `tools/documents/.venv`, `tools/memory/.venv`, `tools/voice/.venv`, `tools/coding/.venv`, and `tools/experimental/.venv`. These virtual environments are runtime-local and ignored by Git. Python 3.11 or 3.12 is preferred for the core and most tool environments; voice and coding tools with narrow compatibility should use Python 3.11.

JARVIS does not create these environments or install packages automatically. `environment audit` and `tool environments` perform passive checks only. `environment audit --pip-check` may run the read-only `python -m pip check`; it never repairs or uninstalls packages.

## Recovery policy

When an optional package fails on Python 3.13, stop retrying in the global interpreter. Record the failure, create the appropriate isolated Python 3.11/3.12 environment only with explicit user approval, install the tool there, run its minimal import/version check, then connect it through a subprocess, local HTTP, provider, plugin, MCP, CLI, skill, or workflow adapter.

Known constraints:

- Open Interpreter and Aider belong in `tools/coding/.venv`; command execution and writes remain disabled by default.
- Coqui XTTS is deferred to Python 3.11; Piper or Windows SAPI remain preferred.
- Open WebUI is deferred until a supported isolated deployment is available.
- vLLM is a future Linux/CUDA route and is not installed on this Windows runtime.
- llama.cpp requires a separate clone/build and is only a backup after verification.

No global package is automatically removed, downgraded, or repaired.
