# Tool and Skill Registry

Updated: 2026-08-10

The Skill Registry is a metadata-only foundation for native capabilities and future plugins. Every manifest declares inputs, outputs, side effects, permissions, provider requirements, locality, risk, approval requirements, status, and limitations.

## Trust Boundary

Skills are not trusted automatically. External plugins and MCP are disabled by default. The registry does not import arbitrary Python, install dependencies, start MCP servers, connect to the network, or execute a skill.

Sensitive permissions such as file writes, commands, browser writes, communication, deployment, and hardware writes require approval. `secrets_access` is blocked by default. Camera and microphone permissions remain explicit and cannot create hidden capture.

## Current and Future Skills

Built-in manifests describe safe current status, conversation, memory retrieval, vision status, image/video workflow planning, read-only web, local sync, and explicit voice capabilities. Future disabled placeholders describe Telegram, Discord, email, calendar, browser writes, coding, research, documents, robotics, drones, social media, MCP, and scheduling.

## Commands

Use `skill status`, `skill list`, `skill capabilities`, `skill show <id>`, `skill find <query>`, `skill permissions <id>`, and `skill diagnostics`.

These commands inspect bounded metadata only.
