# Tool Intelligence

Tool Intelligence extends Executive JARVIS's existing `JarvisTools` registry with governed discovery, validation, planning, execution, and result normalization. Executive JARVIS remains the decision authority; Workflow, Task Intelligence, Multi-Agent Intelligence, providers, and permissions retain their existing ownership.

## Flow and boundaries

Normal conversation is assessed after Reasoning. Provider-only requests remain on the basic-chat path. A positively identified deterministic operation is matched by capability, checked for health and permissions, validated against its schema, converted to a bounded invocation plan, and executed only after Executive approval.

Agents and workflows receive references to the same registry. Agent requests are untrusted and may name only registered tools. Workflow invocations preserve workflow and request correlation. Tool output never grants permission, authorizes another invocation, or mutates goals, tasks, workflows, memory, or provider policy.

## Definitions and risk

Definitions include identity, capabilities, schemas, permissions, risk, mutation and side-effect classes, approval policy, timeout, retry limit, health, availability, lifecycle, and implementation ownership. Registration rejects invalid identifiers, missing executable capabilities, unsafe critical definitions, and duplicates.

Risk classes are `minimal`, `low`, `moderate`, `high`, and `critical`. Confirm mode requires approval for every invocation. Mutating, high-risk, and critical work always requires an approval reference. Critical tools may also be blocked by policy.

## Validation and execution

Input validation enforces required fields, types, enumerations, sizes, unknown-field rejection, safe relative paths, HTTP(S) URLs, and secret-field rejection. Dry runs validate and preview without calling the implementation. Execution has request, concurrency, timeout, output-size, history, retry, and chain-depth bounds. Results distinguish completed, partial, failed, timed out, cancelled, blocked, rejected, and invalid output.

The built-in calculator uses an AST allowlist and never evaluates arbitrary code. The text transformer performs deterministic local transformations. Both are non-mutating and credential-free.

## Commands

`tool list`, `tool show <id>`, `tool health [id]`, `tool match <capability>`, `tool permissions <id>`, `tool dry-run <id> <operation> [key=value]`, `tool history`, `tool invocation <id>`, `tool cancel <id>`, `tool mode <off|confirm|automatic-safe|automatic>`, and `tool limits` use the existing Command Engine and never enter provider chat.

No mode bypasses mandatory permissions or approvals. Cancellation is cooperative: it suppresses completion for a matching active invocation but cannot forcibly stop an implementation that does not support cancellation.

## Persistence and security

Bounded observable history is stored under the existing data directory. Structured payloads and validated arguments are omitted from disk to minimize sensitive-data retention. Credentials, authorization headers, and secret-named arguments are rejected or excluded. Persisted running actions are not automatically resumed.

Tool metadata, arguments, and output are untrusted. Arbitrary shell execution, recursive invocation, hidden mutation, permission escalation, and automatic follow-on actions are not supported.

## Limitations

The current public natural-language assessment intentionally recognizes only narrow deterministic calculator and text-transformation requests. Broader file, browser, communication, database, device, and process tools require future registered implementations and their authoritative permission adapters. Cancellation is cooperative and retries are represented conservatively; mutating retries require idempotency and remain disabled unless explicitly implemented.
