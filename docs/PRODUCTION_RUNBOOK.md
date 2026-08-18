# Production Runbook

1. Start the CLI with `python main.py`.
2. Check `project status`, `phase6 status`, `runtime health`, `environment audit`, and `provider test ollama`.
3. Treat optional tool, OCR, connector, MCP, plugin, and cloud states as degraded when unconfigured.
4. Use only explicit voice, document, image, browser, and execution commands.
5. Before shutdown, stop voice playback and close any explicit browser sessions; normal shutdown owns runtime cleanup.
6. Never place credentials in commands, logs, docs, or Git. Vercel remains a bounded status-only surface.

No automated privileged recovery, package installation, model download, connector authentication, or release publication is part of this runbook.
