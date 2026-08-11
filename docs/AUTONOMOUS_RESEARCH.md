# Autonomous Research Runtime

Prompt 79 extends the Research Agent with a bounded evidence-driven runtime. `quick`, `standard`, and `deep` modes have finite query, source, retrieval, follow-up, character, and time budgets. Deep mode performs bounded decomposition and counterevidence planning; it is never an open-ended loop.

Live search is provider-neutral and disabled until a governed provider reports `ready`. Browser reads remain subject to the existing URL, DNS, redirect, timeout, and content limits. GitHub, trusted read-only MCP resources, and trusted plugin providers remain separate authoritative adapters. The Research Agent does not build a second unrestricted HTTP client.

External text is untrusted data. It cannot approve actions, execute tools, install software, alter policy, enable plugins, mutate memory, complete tasks, or change goals. Cancellation is request-scoped. Research history remains bounded metadata; raw pages and sensitive queries are not persisted by default.

Research knowledge candidates may be evaluated by Knowledge Intelligence, but admission is explicit, provenance-required, approval-aware, and disabled automatically.

Commands include `research providers`, `research provider-health`, `research budget`, `research quick`, `research standard`, `research deep`, `research search`, `research verify`, `research citations`, `research contradictions`, and `research knowledge-candidates`, in addition to the original Research Agent commands.
