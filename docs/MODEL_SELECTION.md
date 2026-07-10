# Model Selection

The Model Selector ranks configured models for a selected provider without invoking model APIs.

Selection inputs include:
- capabilities
- context window
- reasoning support
- tool calling
- vision support
- embeddings support
- latency metadata
- estimated cost metadata
- historical performance

The selector returns the best model metadata or `None` when no model is suitable.
