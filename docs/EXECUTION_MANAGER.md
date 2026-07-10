# Execution Manager

`ExecutionManager` coordinates the Provider Execution Framework.

Responsibilities:
- build normalized execution requests
- infer execution strategy metadata
- select providers
- select models
- validate requests and responses
- record execution history
- prepare fallback and recovery metadata

The manager does not call AI providers directly. It only prepares execution metadata and returns architectural responses.
