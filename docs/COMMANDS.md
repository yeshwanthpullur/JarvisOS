# Phase 6 Commands

## Pre-Old-Phone Worker Foundation

`worker status|list|show|health|inventory|models|model-refresh|providers|route|select|task-plan` exposes bounded detection and planning. `work status|plan|show|graph|worktree-plan|context|messages` exposes bounded coordination metadata. These commands never start worker execution, grant approval, create a worktree, commit, push, merge, read secrets, or start Phase 7.

Phase 6 commands expose bounded metadata and policy decisions. Detection is not authorization.

```text
environment status
environment audit [--pip-check]
tool status
tool environments
tool inspect <tool_id>
tool audit
provider inspect <provider_id>
provider test <provider_id>
model list
model health
model inspect <model_id>
model roles
model select <role> <installed_model>
model test <installed_model>

browser health
browser permissions
browser session list
browser session inspect <id>
browser session close <id>
crawl status
crawl health
crawl plan <public_https_url>
crawl run <public_https_url>
crawl inspect <id>
research health
research source list
research audit
research clear-session

document health
document parse <explicit_file>
document inspect <document_id>
document summarize <document_id>
document chunks <document_id>
document sources
document audit
document clear-session
ocr status
ocr health
ocr parse <explicit_file>

memory health
memory conflicts
vector status
vector health
vector collections
vector inspect <collection>
graph status
graph health
graph inspect <entity>
embedding status
embedding health
embedding models

voice stt
voice tts
voice test-input
voice test-output
voice sessions
voice session inspect <id>

vision health
vision inspect <explicit_image>
camera status
camera devices
camera start
camera stop
camera session inspect <id>

coding health
coding tools
coding tool inspect <tool>
coding apply <task_id>
coding cancel <task_id>
coding audit
git status
git diff
git history
git verify
github branch
github commits

system status
system health
system processes
system disks
system memory
system gpu
app status
app list
app open <app_id>
app close <app_id>
file status
file read <path>
file write <path>
file move <source> <target>
file copy <source> <target>
file delete <path>
automation status
automation permissions

connector status
connector list
connector health
connector inspect <id>
connector capabilities
connector permissions <id>
connector test <id>
connector audit

runtime traces
runtime circuits
performance status
performance startup
performance providers
performance models
performance memory
performance voice
operations status
operations alerts
operations audit

phase6 status
phase6 candidate [--probe]
phase6 checklist

mcp status
mcp servers
mcp server-show <server_id>
mcp server-health <server_id>
mcp start <server_id>
mcp discover <server_id>
mcp tools [server_id]
mcp tool-show <server_id> <tool_name>
mcp classify <server_id> <tool_name>
mcp resources [server_id]
mcp resource-read <server_id> <resource_ref>
mcp prompts [server_id]
mcp stop <server_id>
```

Unknown subcommands return namespace help and never fall through to chat.

`tool environments` and `tool inspect` distinguish installation, detection, configuration, integration, enablement, and execution authorization. Set `JARVIS_INSTALLATIONS_ROOTS` to an `os.pathsep`-separated list only when installations are outside the repository or mounted-drive discovery locations; CLI output uses safe aliases rather than private absolute paths.

`mcp start <server_id>` performs the handshake and bounded metadata discovery in the current CLI session. `mcp discover <server_id>` explicitly refreshes the same tool/resource registry. Neither command calls tools or grants trust. These commands do not install packages, download models, start hidden capture, authorize execution, send connector payloads, upload telemetry, or bypass Policy, Approval, Broker, Governance, Memory, Conversation, Workflow, or Reliability authority.
