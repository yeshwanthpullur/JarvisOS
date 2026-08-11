# Tool and Skill Registry

Prompt 73 adds Telegram status, identity, pairing, destination, text receive/send, and bounded polling skill declarations. Send and network permissions remain approval-gated; attachments, voice, video, groups, channels, scheduling, and webhook skills are future/disabled.

## Phase 4 Skills

Metadata now describes execution policy, approvals, broker validation, scoped files, allowlisted commands, approved Git writes, controlled browser reads, local notifications, and manual scheduler execution. These skills declare side effects and permissions explicitly. Registry readiness does not authorize execution.

## Batch 2 Skills

Batch 2 registers metadata-only skills for documents, browser reads, schedule validation, communication drafting, adapter manifests, advanced model comparisons, and local evaluation. Runtime counterparts for OCR/cloud parsing, browser writes, active scheduling, sending, MCP/plugins, provider startup, and model downloads remain disabled.

Updated: 2026-08-10

The Skill Registry is a metadata-only foundation for native capabilities and future plugins. Every manifest declares inputs, outputs, side effects, permissions, provider requirements, locality, risk, approval requirements, status, and limitations.

## Trust Boundary

Skills are not trusted automatically. External plugins and MCP are disabled by default. The registry does not import arbitrary Python, install dependencies, start MCP servers, connect to the network, or execute a skill.

Sensitive permissions such as file writes, commands, browser writes, communication, deployment, and hardware writes require approval. `secrets_access` is blocked by default. Camera and microphone permissions remain explicit and cannot create hidden capture.

## Current and Future Skills

Built-in manifests describe safe current status, conversation, memory retrieval, vision status, image/video workflow planning, read-only web, local sync, explicit voice capabilities, research planning, source policy, project research, and bounded evidence summaries. Future disabled placeholders describe academic search, citation management, external search APIs, Telegram, Discord, email, calendar, browser writes, coding, documents, robotics, drones, social media, MCP, and scheduling.

Research skills remain metadata and plan-only capabilities. `web_research_skill` declares read-only browser permission; it cannot log in, submit forms, bypass paywalls, or invent retrieved sources. External search APIs remain disabled and require a future separately approved integration.

Prompt 52 adds ready metadata-only skills for coding planning, repository inspection, diff review, test planning, and release review. The `code_edit_skill`, `command_execution_skill`, `auto_commit_skill`, `auto_push_skill`, and `dependency_install_skill` remain disabled future manifests. Git-read permission is explicit; Git-write and command permissions remain approval-required and unavailable for execution.

## Commands

Use `skill status`, `skill list`, `skill capabilities`, `skill show <id>`, `skill find <query>`, `skill permissions <id>`, and `skill diagnostics`.

These commands inspect bounded metadata only.
