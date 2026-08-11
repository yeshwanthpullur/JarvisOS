# Self Healing

Automatic recovery is intentionally narrow: health-cache refresh, metadata refresh, initialization retry planning, and temporary-state cleanup may be proposed. Package installation, model download, source/config changes, provider enablement, Git changes, deployment, and privileged restart remain prohibited automatically.

Privileged recovery must follow Reliability Runtime to Execution Policy to Approval System to Execution Broker to an authorized runtime. Recovery history is bounded metadata only.
