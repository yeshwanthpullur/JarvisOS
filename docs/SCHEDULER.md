# Scheduler

The existing Phase 4 scheduler remains authoritative. Phase 6 only links automation diagnostics to its manual, approval-gated notification runner. Scheduled tasks never inherit new permissions, and no new background daemon, arbitrary command runner, application controller, or external connector sender is created.
