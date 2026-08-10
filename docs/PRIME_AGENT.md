# Prime Agent

Updated: 2026-08-10

The Prime Agent is a controlled routing and delegation-planning layer under Executive JARVIS. It classifies broad intent and risk, inspects the Agent Registry, consults Model Router metadata, references Skill Registry metadata, and returns a bounded decision or plan.

It does not replace Conversation Intelligence, bypass command permissions, call models directly, execute tools, mutate memory, or perform background work.

## Routing

Selection order is an explicit valid agent, capability match, deterministic intent match, then a safe fallback. Unavailable agents produce an unavailable explanation rather than fake success. Image and video requests can route to workflow foundations; communication, robotics, drone, and social requests route to disabled future entries.

Research requests route to `research_agent` for plan-only handling. Prime may include the advisory local reasoning route and registered research skills, but it does not fetch sources, call an external search API, or save results to Persistent Memory.

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
