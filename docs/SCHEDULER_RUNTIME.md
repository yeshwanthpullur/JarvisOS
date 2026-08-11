# Manual Scheduler Runtime

Prompt 72 does not permit scheduled external sends; scheduler execution remains limited to its existing local notification boundary.

The scheduler stores bounded in-memory notification jobs and runs them only when the user explicitly invokes a run command. It supports one-time jobs, recurrence of at least 60 minutes, due inspection, run, run-due, pause, resume, and cancel.

There is no daemon, hidden worker, OS Task Scheduler integration, cron installation, scheduled command execution, scheduled Git operation, or external communication. Running a job still requires the notification approval and broker checks. Restarting JARVIS clears the in-memory schedule.
