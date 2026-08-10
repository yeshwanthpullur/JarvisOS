# Approved Git Execution

Git writes are handled by a dedicated executor, not the command executor. Supported actions are explicit stage, unstage, commit, and push operations on configured branches and remotes.

Protected/private files and secret-shaped staged content block the operation. Force-push, history rewriting, broad destructive cleanup, tag/release mutation, credential access, and hidden commits or pushes are not supported.

Use `git-exec status`, planning commands, and an exact approval before execution. Normal repository review remains read-only.
