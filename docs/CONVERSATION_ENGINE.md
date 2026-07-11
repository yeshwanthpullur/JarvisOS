# Conversation Engine

The Conversation Engine is the operating interface in front of Executive JARVIS. It receives user input, maintains a session, records history, routes commands, and sends natural language requests to `JarvisCore`.

It now also carries goal-intelligence context when the active request is goal-related, so the user can ask for clarification, progress, blockers, next steps, or a goal review without restating the whole project.

It performs no AI calls and no automation.

It also provides the capture point for explicit personal-information statements so that relevant user preferences can be stored through the Memory Engine and later retrieved in a controlled way.

It now also provides the entry point for Context Intelligence. The active objective, active work reference, recent context history, pending continuation state, and ambiguity metadata stay attached to the existing conversation session and can be answered locally or passed forward into Executive JARVIS.
