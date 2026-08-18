# Phase 6 Commands

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
```

Unknown subcommands return namespace help and never fall through to chat.
