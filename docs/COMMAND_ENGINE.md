# Command Engine

The Command Engine parses, validates, registers, and dispatches commands. Built-ins are registered through `CommandRegistry`, so future plugins can add commands without changing the parser.

Commands flow through Conversation Engine before reaching Executive JARVIS or subsystem metadata.

