# JARVIS OS Architecture

JARVIS OS is organized as a modular Python application. The current foundation intentionally avoids AI implementation so the system can grow around stable boundaries first.

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

