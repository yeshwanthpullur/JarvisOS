# Local Desktop Interface

## Purpose

Prompt 31.5 adds a usable browser interface for the existing JARVIS runtime. It is a presentation and interaction layer, not a new intelligence, command, provider, tool, planning, voice, approval, or persistence authority.

The default URL is `http://127.0.0.1:8765`. The interface is disabled during normal CLI startup and is enabled explicitly with:

```powershell
python main.py --ui
```

The Windows launcher provides the same path:

```powershell
.\start_jarvis_ui.ps1
```

Use `--no-browser` or `-NoBrowser` when the URL should be printed without opening the default browser.

## Architecture

The implementation uses the Python standard library `ThreadingHTTPServer` and dependency-free HTML, CSS, and JavaScript. It needs no Node.js, Docker, frontend build, external CDN, or internet connection.

The request path is:

```text
Browser action
-> localhost interface validation
-> session and CSRF token validation
-> ConversationManager.handle_input
-> Command Engine or Executive JARVIS
-> existing reasoning, provider, tool, planning, multi-agent, and voice paths
-> normalized interface response
-> safe DOM rendering
```

Ordinary chat and command text share the existing Conversation Engine classifier. The browser never calls providers, Ollama, Windows SAPI, tools, agents, plans, workflows, or storage directly.

## Local Security Boundary

- The service binds to `127.0.0.1` by default.
- Remote binding and `allow_remote` are rejected in this milestone.
- Client address, `Host`, and `Origin` are validated.
- Mutating requests require a random per-launch `X-Jarvis-Session` token.
- The token is injected into the served HTML, never placed in a URL, logged, persisted, or stored in browser storage.
- No wildcard CORS header is emitted.
- CSP, frame denial, MIME sniffing prevention, no-referrer, and no-store headers are applied.
- Request, response, stream, activity, history, and log sizes are bounded.
- Model, command, tool, plan, agent, voice, and log content is treated as untrusted and inserted into the page with DOM text nodes.
- API keys, bearer values, authorization values, hidden reasoning markers, and common secret assignments are redacted from the safe log view.

This milestone does not implement account authentication or remote access.

## Interface

The desktop layout uses a navigation sidebar, primary work area, and activity panel. Below 1120 pixels the activity panel becomes a drawer. Below 760 pixels the navigation also becomes a drawer, the chat composer remains usable, and record grids reflow without horizontal page overflow.

Views include:

- Chat with multiline input, Enter/Shift+Enter behavior, copy, safe code blocks, retry-friendly errors, cancellation, timestamps, request correlation, and provider/model metadata.
- Activity with safe request, provider, tool, coordination, plan, voice, failure, and cancellation summaries.
- Tools sourced from the authoritative Tool Intelligence registry.
- Plans sourced from Autonomous Planning records.
- Multi-Agent coordinations sourced from the existing orchestration store.
- Voice status and synthesis through Voice Intelligence.
- Health for the runtime, conversation, provider execution, Ollama, tools, multi-agent, planning, voice, SAPI, STT, persistence, temporary storage, and interface.
- Safe bounded logs with level, subsystem, and request-ID filtering.
- Settings for theme, density, auto-scroll, notifications, provider policy/preferences, voice output/privacy/language/rate/volume, and governed tool, multi-agent, and planning modes.
- Action-specific plan approvals routed through existing planning commands.

The color system supports dark and light themes, visible focus, semantic controls, reduced motion, accessible live regions, and restrained status indicators.

## API

Read operations include bootstrap, health, status, conversations, request status, activity, logs, providers, voice, tools, plans, coordinations, approvals, settings, static assets, and Server-Sent Events.

Mutating operations include message acceptance, cancellation, conversation creation/activation, voice synthesis/interruption, approval decisions, allowlisted settings updates, and authenticated graceful shutdown. There is no shell, eval, raw-file, arbitrary command, generic execution, upload, provider-call, tool-call, or SAPI endpoint.

Messages are accepted with a server-generated interface request ID and processed on a bounded worker. The client polls the typed request status while observable activity is delivered by bounded SSE. If SSE is unavailable, polling and final responses remain functional.

Normalized responses expose safe observable fields including status, response type, content, request IDs, conversation ID, provider/model, command, tool, coordination, plan, workflow, approval, warnings, errors, timing, and cancellation state. Hidden reasoning and private scratch data are excluded.

## Conversation History

ConversationManager remains authoritative. Prompt 31.5 extends it to retain bounded in-memory sessions using existing `ConversationSession` and `ConversationHistory` objects. The interface can create, list, activate, and display these sessions without a second database. History is not durable across application restarts unless the existing conversation subsystem later adds that policy.

## Voice

Voice output uses the Prompt 31 Voice Intelligence service and real Windows SAPI. The interface does not invoke SAPI directly. Output must be enabled before synthesis. Sensitive/code response policy remains enforced by Voice Intelligence.

No microphone capture adapter or offline STT model is configured. The interface therefore reports microphone and STT as unavailable and exposes no working recording control. It does not download models or simulate transcription.

## Approvals and Cancellation

Pending autonomous plans in review/approval states appear as action-specific approvals. Approve and reject decisions are revalidated and submitted through the Command Engine. Closing or ignoring the interface never approves work.

Cancellation targets only correlated interface requests, tool invocations, multi-agent coordinations, plans, or voice sessions through their existing cancellation methods. Provider work that has already completed remains completed; no process-kill shortcut is used.

## Configuration and Limits

`interface` settings in `config.yaml` and the typed schema cover enablement, loopback host, port, browser opening, theme, default view, SSE, request/response limits, log/activity/history limits, timeouts, origins, token lifetime, safe Markdown, metadata visibility, activity panel, and density.

Conservative defaults keep the service disabled, loopback-only, bounded, and safe. File uploads are not implemented. UI setting updates are allowlisted and do not rewrite `config.yaml` silently.

## Persistence and Observability

Only non-sensitive display preferences live in interface memory. The browser does not persist tokens, keys, credentials, private memory, logs, raw audio, prompts, or hidden reasoning.

Safe structured events cover initialization, start/stop, request receipt/validation/completion/failure/cancellation, stream connect/disconnect, approvals, settings, voice, and security rejection. Event data is bounded and redacted.

## Failure Handling

Port conflicts, malformed input, oversized requests, invalid sessions, invalid origins, unavailable JARVIS components, provider failures, voice failures, stale approvals, unsafe settings, event-stream disconnects, and missing records return explicit normalized failures. Interface failure does not change normal `python main.py` CLI operation.

## Verification

Automated tests cover the loopback boundary, Host/Origin/session enforcement, API behavior, command separation, correlation, cancellation, histories, tools, voice, logs, output safety, settings, SSE, responsive assets, shutdown, and CLI/provider boundaries. The acceptance procedure additionally checks the rendered UI at desktop and mobile widths, real Ollama chat, real Tool Intelligence arithmetic, real Windows SAPI synthesis, themes, refresh, logs, and port release.

## Known Limitations and Future Work

- Conversation history is currently in-memory.
- Provider token streaming is represented by activity events and final normalized responses; incremental model token rendering is not yet exposed.
- Provider generation cannot always be interrupted after the underlying non-streaming adapter call begins.
- Exact character reproduction remains model-dependent. During acceptance, the installed `llama3.2:1b` model returned `INTERFACECHAT_OK` for the required `INTERFACE_CHAT_OK` prompt even though routing, request correlation, and provider completion were verified. The interface does not rewrite provider output or echo the requested literal to hide that limitation.
- Tool approvals are shown only when an authoritative pending record exists; no duplicate approval store was added.
- Microphone input and offline STT remain unavailable.
- No remote access, account authentication, uploads, notifications, camera, Vision, Desktop Automation, Browser Automation, or Phone Integration is implemented.

Prompt 32 may integrate Vision through existing boundaries. Desktop Automation, Browser Automation, and Phone Integration remain separate future milestones. Prompt 36 can build on this stable API and layout for higher visual polish without replacing authority or execution paths.
