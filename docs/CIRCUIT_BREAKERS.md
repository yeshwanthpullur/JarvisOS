# Circuit Breakers

Circuit breakers are bounded routing signals with closed, open, half-open, and recovering states. Repeated failures open a circuit; an explicit probe enters half-open; configured consecutive successes close it. A breaker never changes provider configuration, starts a runtime, or grants execution authority.
