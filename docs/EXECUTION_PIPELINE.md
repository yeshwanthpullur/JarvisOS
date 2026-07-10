# Execution Pipeline

The Executive request pipeline is deterministic and provider-independent:

`JarvisRequest -> JarvisContext -> JarvisIntentEngine -> JarvisDecisionEngine -> JarvisPlanning -> JarvisDispatcher -> JarvisResponseBuilder -> JarvisResponseFormatter -> JarvisResponse`

Every stage is represented by a typed class and can be replaced later without changing callers.

## Future Roadmap

Future versions can attach provider-backed reasoning through Provider Router, workflow DAGs, and dynamic specialist creation through Agent Creator.

