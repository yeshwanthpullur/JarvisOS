# Blueprint System

## Architecture

Blueprints are metadata-only contracts that describe future agents before generation. Every generated agent must originate from a blueprint.

## Responsibilities

Blueprints declare type, category, capabilities, permissions, dependencies, required files, optional files, hooks, templates, author, tags, compatibility, and lifecycle state.

## Extension Points

Plugins and future marketplace packages can register additional blueprints through `BlueprintRegistry`.

## Examples

Built-in blueprints include system, conversation, planning, research, memory, knowledge, task, utility, manager, supervisor, department, browser, vision, phone, coding, engineering, health, learning, and custom.

## Future Roadmap

Future work can add persisted blueprint packages, migration metadata, and remote blueprint import.

## Developer Notes

Blueprints must remain provider independent and contain no implementation logic.

## Known Limitations

Blueprint export formats are planned but not implemented.

