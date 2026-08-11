# Prime Agent

Research requests route to `research_agent`; retrieved text cannot grant approval or authority, and Research cannot execute discovered actions.

Prime requests capability profiles such as reasoning, coding, research, or vision; the Model Router selects physical routes under policy.

Prime may inspect and plan plugin capabilities, but cannot enable, install, execute, or broaden plugin authority silently.

Prime routes MCP requests through Adapter Agent and registry trust/policy. It cannot grant trust or call side-effect tools directly.

Prime routes GitHub service requests to Coding Agent or read-only Research context. Ordinary commit, tag, and push remain local Git operations, and Prime receives no direct provider authority.

Prime recognizes Telegram status and send intent, routes it to the Communication Agent, and preserves high-risk approval requirements. Routing never sends a message or chooses a Telegram-specific model.

Prime may route drafts and send plans to Communication Agent, but cannot authorize or dispatch an external message. Bulk and secret-send intents remain blocked.

## Controlled Execution Routing

Prime recognizes execution, approval, and notification intents, but its decisions remain plans. Force-push, broad deletion, secret access, and similar critical requests are blocked. A Prime route never substitutes for exact approval or the broker's immediate policy validation.

## Batch 2 Routing

Prime routes document, webpage, reminder, draft communication, MCP/plugin, and advanced model requests to governed foundations. CAPTCHA bypass, secret access, spam, private-person monitoring, destructive adapter execution, and credential requests are critical-risk blocked. Routing remains advisory.

Updated: 2026-08-10

The Prime Agent is a controlled routing and delegation-planning layer under Executive JARVIS. It classifies broad intent and risk, inspects the Agent Registry, consults Model Router metadata, references Skill Registry metadata, and returns a bounded decision or plan.

It does not replace Conversation Intelligence, bypass command permissions, call models directly, execute tools, mutate memory, or perform background work.

## Routing

Selection order is an explicit valid agent, capability match, deterministic intent match, then a safe fallback. Unavailable agents produce an unavailable explanation rather than fake success. Image and video requests can route to workflow foundations; communication, robotics, drone, and social requests route to disabled future entries.

Research requests route to `research_agent` for plan-only handling. Prime may include the advisory local reasoning route and registered research skills, but it does not fetch sources, call an external search API, or save results to Persistent Memory.

Coding, repository, diff, bug-triage, refactor, and safe integration-planning requests route to `coding_agent`. Prime preserves `plan_only`, raises approval metadata for edits, commands, commits, pushes, installations, and deployments, and blocks critical destructive or secret-access requests. Routing never edits code or runs a coding command.

## Risk and Approval

Risk levels are `low`, `medium`, `high`, and `critical`. High-risk requests require approval metadata. Critical requests are blocked by Phase 3 policy. Approval states are explicit, but Phase 3 does not add an approval UI or approved side-effect execution.

`plan_only` is the default. `dry_run` is side-effect free. `approved_execution` remains governed by existing subsystem permissions and is not enabled as a general agent mode in this phase.

## Commands

- `prime status`
- `prime route "<request>"`
- `prime plan "<request>"`
- `prime risk "<request>"`
- `prime explain "<request>"`

These commands only classify, route, explain, and plan.
