# Scheduler Agent

## Manual Runtime

The scheduler can now hold bounded in-memory notification jobs and run them only through explicit user commands and approval checks. There is no background daemon, OS scheduler installation, scheduled command execution, or persistence across restarts.

Prompt 55 adds deterministic one-time, recurring, and condition-watch schedule planning and cadence validation. Plans are metadata only.

There is no background runner, OS cron entry, Windows Task Scheduler task, unattended workflow, notification delivery, or hidden monitoring. Cadence below the safe configured minimum and private-person monitoring are blocked.

Commands: `scheduler status`, `help`, `plan`, `safety`, `validate`, `preview`, `capabilities`, `show`, and `history`.
