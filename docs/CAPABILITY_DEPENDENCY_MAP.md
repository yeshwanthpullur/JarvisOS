# Capability Dependency Map

This map is a documentation contract for the recovered Engineering Steps 64-94
block. It does not grant execution authority.

| Capability | Primary | Alternative/local fallback | Authority boundary | Current state |
| --- | --- | --- | --- | --- |
| conversation | local Ollama/text path | bounded conversation fallback | Executive/Prime and conversation policy | local-first |
| research | Research Agent | project/repository sources | read-only source policy; no memory mutation | foundation |
| documents | canonical document pipeline | built-in text path | explicit path and citation policy | foundation/degraded optional parsers |
| knowledge | local lexical index | bounded metadata fallback | memory/knowledge authority | foundation |
| voice | explicit local STT/TTS adapters | Windows SAPI output | explicit PTT; no hidden listening | degraded by optional models |
| vision | local Ollama/LLaVA | truthful unavailable state | local image policy; no camera capture | foundation |
| browser | public read executor | plan-only browser agent | read/action separation; Broker | read-only |
| MCP | local stdio discovery | plan-only metadata | discovered != trusted != enabled != authorized | discovery-only |
| coding | repository inspection/planning | plan-only coding agent | no silent edits/commit/push | foundation |
| scheduling | manual local scheduler | plan-only schedule agent | approval/Broker; no daemon | degraded |
| communication | provider-neutral draft/send plans | local notification | approval, egress, destination, rate controls | degraded/unconfigured |
| model routing | provider registry/router | local-only unavailable state | privacy policy, health, cost metadata | foundation |
| execution | Policy -> Approval -> Broker -> executor | dry-run | no direct agent/tool authority | foundation |

Every side-effecting path must pass the Execution Policy, required approval, and
Execution Broker. External content remains untrusted input.
