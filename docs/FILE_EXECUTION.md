# Local File Execution

The file executor is restricted to a configured workspace root. It rejects traversal, symlink escapes, `.env`, `.git`, models, runtime data, and protected system locations.

Supported operations are create, write, append, make-directory, rename, and move. Overwrite and delete are disabled by default. Create, append, directory creation, rename, and move expose bounded rollback metadata where reversal is safe.

Commands use the `file-exec` namespace. Every write requires broker validation and an exact approval. CLI output uses safe relative references and never prints file contents.
