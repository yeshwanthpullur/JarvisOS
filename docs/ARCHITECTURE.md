# JARVIS OS Architecture

## External Worker Flow

`User -> Executive JARVIS -> Goal/Work Manager -> validated Task DAG -> worker/model selector -> non-authoritative adapter -> structured result -> independent review/evidence -> Executive JARVIS -> User`. The worker facade reuses internal registries and execution authorities. Munder is optional beside direct Codex, Hermes, OpenCode, and Aider adapters; no external harness becomes authoritative.

JARVIS OS is organized as a modular Python application. Local AI, conversation, memory, and specialist foundations sit behind explicit registries and authority boundaries so optional workers can be added without becoming Executive JARVIS.

## Design Principles

- Keep modules small and focused.
- Prefer explicit dependencies over global state.
- Use typed settings and centralized logging.
- Keep platform-specific work isolated behind desktop and mobile packages.
- Add AI providers, models, and agents only after the foundation is stable.

## Runtime Flow

1. `main.py` loads immutable settings.
2. Logging is configured from those settings.
3. The application starts and reports its environment.
4. Future modules will be composed from this entry point or a dedicated application service.

## Extension Points

- Add agent orchestration under `agents/`.
- Add workflow automation under `automation/`.
- Add model adapters under `models/`.
- Add reusable abilities under `skills/`.
- Add external integrations under `plugins/`.
- Add APIs under `server/`.
