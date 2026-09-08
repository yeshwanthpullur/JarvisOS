# Laptop Baseline

## Status

Engineering baseline: `READY_FOUNDATION`. Production readiness: `NOT READY`. Commercial readiness: `NOT READY`. Default operating mode is `DEVELOPMENT/TESTING`.

## Hardware and runtime

Record machine-specific values locally during a validation session; do not commit identifiers or private paths. The baseline requires a supported Python runtime, sufficient disk for the repository and optional local models, CPU/RAM appropriate to the selected local model, and an optional GPU only when independently detected. Windows is the current verified host; Linux responsibilities are documented as a portability target, not a verified deployment.

Python and dependency versions are defined by the repository environment. Ollama, Vosk/Faster-Whisper, SAPI/Piper, OCR, and external connectors are optional and must report their actual health. No model download, cloud account, or paid service is required for the CLI foundation.

## Capability availability

| Capability | State | Boundary |
| --- | --- | --- |
| Conversation/context/goals/tasks/DAG | AVAILABLE | Local, bounded, policy-controlled. |
| Workers/providers/Prime routing | AVAILABLE | Metadata and plan-only by default. |
| Research/documents/RAG/memory | DEGRADED | Local planning/lexical paths; live search/semantic providers optional. |
| Voice | DEGRADED | TTS/local controls available; physical STT hardware validation pending. |
| Vision | DEGRADED | Local still-image path requires configured provider. |
| Browser/MCP/tools | DEGRADED | Read/discovery foundations; action and tool execution disabled by default. |
| Scheduler/communication | UNCONFIGURED | No autonomous runner or external credentials. |
| Observability/security/recovery/Control Room | AVAILABLE | Bounded local metadata and policy surfaces. |
| Old phone / VPS | BLOCKED | Planning only; no migration or cloud dependency. |

## Baseline gate

The laptop remains the primary platform. A phone transition is forbidden until backup restore, authentication/revocation, migration, network, failure, and rollback tests pass.
