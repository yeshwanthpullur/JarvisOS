# Compatibility Matrix

| Source | Target | Supported | Restricted |
|---|---|---|---|
| Executive | Prime | Routing and bounded planning | Direct execution |
| Prime | Workflow Engine | Bounded workflow plans | Approval grants |
| Workflow Engine | Orchestrator | Metadata coordination | Authority transfer |
| Orchestrator | Research | Request-scoped tasks | Hidden external calls |
| Research | Browser | Governed public reads | Browser writes |
| Research | Knowledge | Evidence candidates and retrieval | Automatic Memory writes |
| Knowledge | Memory | Explicit references | Silent promotion |
| Coding | GitHub | Metadata reads and exact approved writes | Silent push |
| Browser | Providers | Validated public GET | Credentials, login, or forms |
| Plugins | Broker | Registered exact approved calls | Arbitrary loading |
| MCP | Broker | Trusted exact approved calls | Global trust |
| Workflow | Approval | Pause for exact approval | Session-wide approval |
| Workflow | Governance | Identity and policy metadata | Governance execution |
| Workflow | Reliability | Health and recovery plans | Automatic privileged recovery |
| Provider Registry | Model Router | Capability-based routes | Implicit provider enablement |

Future providers, plugins, MCP servers, communication accounts, and runtime nodes remain disabled or unconfigured until separately authorized and validated.
