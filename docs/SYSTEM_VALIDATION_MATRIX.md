# System Validation Matrix

| Component | Authority / ownership | Dependencies | Supported interface | Known boundary | Status |
|---|---|---|---|---|---|
| Executive JARVIS | Final request authority | Core runtime | Validate, respond | No implicit side effects | Passed |
| Prime Agent | Coordination only | Agent and Model registries | Route, plan | Does not execute | Passed |
| Workflow Engine | Workflow state | Approval, Policy | Graph, checkpoint, recover | Does not approve | Passed |
| Multi-Agent Orchestrator | Coordination only | Prime, Workflow | Bounded task scheduling | No side effects | Passed |
| Research Runtime | Evidence synthesis | Browser, Knowledge | Plan, retrieve, cite | No Memory write | Passed |
| Knowledge Runtime | Retrieval index | Research | Admit explicit sources, retrieve | Evidence is not Memory | Passed |
| Coding Agent | Plan-only repo intelligence | GitHub provider | Inspect, review, plan | No silent edit/commit/push | Passed |
| Document Intelligence | Explicit-file analysis | Document adapters | Inspect, extract, summarize | No hidden file access | Passed |
| Browser Runtime | Public read-only retrieval | Provider policy | Validate URL, public GET | No login/forms/write | Passed |
| Integration providers | Provider-specific adapters | Registry, Broker | Bounded reads, exact approved writes | Disabled/unconfigured by default | Passed |
| Plugin and MCP runtimes | Metadata/trust registries | Broker | Inspect, validate, exact approved call | No auto-install/global trust | Passed |
| Model Router | Advisory model routing | Provider Registry | Route and fallback metadata | No download/runtime start | Passed |
| Execution Policy | Action policy authority | None | Classify and block | Cannot grant approval | Passed |
| Approval System | Exact authorization authority | Policy | Grant, deny, expire, revoke | Cannot execute | Passed |
| Execution Broker | Dispatch authority | Policy, Approval | Validate and dispatch exact executor | Cannot grant permission | Passed |
| Reliability Runtime | Observational health | Workflow, Providers | Diagnose and plan recovery | No privileged self-healing | Passed |
| Enterprise Governance | Policy coordination | Policy, Approval, Broker | Identity, authorize, audit, compliance | Cannot execute or approve | Passed |
| Vercel API | Bounded status only | Static project metadata | Status and health | No local runtime capability | Passed |

Inputs, outputs, permissions, privacy scope, resource budgets, failure behavior, and ownership are represented by `SystemContract` in the release-readiness evaluator.
