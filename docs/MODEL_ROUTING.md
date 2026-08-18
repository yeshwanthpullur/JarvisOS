# Model Routing

Model routing maps a task role to compatible, enabled, policy-allowed, healthy local model metadata. It does not grant model execution authority. Explicit per-process `model select` choices are accepted only for installed compatible models and are not persisted.

Automatic cloud fallback and automatic model downloads are disabled. A missing role returns unavailable with fallback metadata. Vision remains explicit and local; private image use follows the existing Vision Intelligence policy.
