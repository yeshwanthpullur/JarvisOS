# Model Failover

Fallback is bounded, capability-preserving, and policy-aware. Remote fallback is excluded when data-egress policy forbids it, paid providers are never selected automatically, and the configured maximum fallback count is enforced. Provider timeouts and failures affect a circuit breaker; policy, user, and validation errors do not. Half-open recovery requires a successful provider response.
