# Execution Broker

Communication dry runs never dispatch. Future provider `send()` calls must enter through this Broker after exact approval and policy validation.

The broker is the single policy checkpoint for controlled execution. It validates system readiness, execution mode, risk, permissions, exact approval scope, and executor availability. It returns structured blocked, dry-run, ready, completed, or failed results.

The broker does not discover tools dynamically, install dependencies, run arbitrary plugins, or bypass subsystem policies. Diagnostics are available through `broker status`, `broker validate <action>`, and `broker dry-run <action>`.
