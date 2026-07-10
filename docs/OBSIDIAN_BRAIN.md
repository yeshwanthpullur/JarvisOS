# Obsidian Brain Integration

The Brain layer is the human-readable knowledge layer of JARVIS OS. SQLite remains the source of structured truth for memory, knowledge, and task state. The Obsidian vault stores Markdown notes that people can inspect, edit, link, and organize.

## Why This Exists

The Memory Engine stores durable structured records in SQLite. The Knowledge Engine stores imported documents and searchable chunks. The Task Engine stores units of work. The Brain layer gives those systems a readable surface by creating linked Markdown notes with standard frontmatter.

This keeps storage responsibilities separate:

- SQLite owns structured data and IDs.
- Obsidian owns readable Markdown notes.
- Frontmatter links notes back to memory, knowledge, task, and future project IDs.
- Future vector databases can index either SQLite records or Markdown notes without changing these public contracts.

## Module Communication

`BrainManager` composes the Obsidian managers and exposes integration methods:

- `create_memory_note(memory)` links a note to a Memory Engine record.
- `create_knowledge_note(document)` links a note to a Knowledge Engine document.
- `create_task_note(task)` links a note to a Task Engine task.

The Brain layer does not duplicate structured storage. It stores identifiers, frontmatter, wiki links, and readable context.

## Vault Structure

The vault path is configured in `config.yaml` under `brain.vault_path`. On startup, JARVIS verifies or creates the configured vault and required folders:

- Daily Notes
- Knowledge
- Projects
- Research
- Skills
- Conversations
- Ideas
- Tasks
- Logs
- Prompts
- Architecture
- Decisions
- Attachments
- Templates

## Frontmatter Standard

Generated notes support:

- `uuid`
- `title`
- `created`
- `updated`
- `type`
- `tags`
- `aliases`
- `status`
- `importance`
- `source`
- `project_id`
- `task_id`
- `memory_id`
- `knowledge_id`
- `related_notes`
- `metadata`

## Search

`SearchManager` searches note titles, Markdown content, tags, frontmatter, wiki links, backlinks, and metadata using local file reads. It does not implement semantic search or embeddings.

## Graph Support

`GraphManager` records relationships and can infer wiki-link edges. It intentionally does not render graph visualizations. Future UI and vector/graph databases can consume these relationship records.

## Security Notes

The Brain layer restricts note operations to the configured vault path. It logs create, update, delete, search, vault connection, and relationship operations. It does not autonomously edit user notes outside explicit manager calls.
