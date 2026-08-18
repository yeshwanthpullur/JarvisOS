# Coding Agent Foundation

Phase 6 keeps the built-in Coding Agent authoritative for planning, repository metadata, diff review, and test recommendations. External tool detection adds no authority. Writes require a future exact approval and Broker handoff; arbitrary shell, secret access, force push, and destructive operations remain blocked.

Coding model routes are advisory and do not grant command, file, Git, dependency, or deployment authority.

Coding may inspect local plugin manifests or source without running third-party install, build, or test scripts.

Coding may use trusted developer-oriented MCP reads but cannot bypass Command Sandbox, local Git Executor, approval, or Broker.

Coding Agent distinguishes local Git from scoped GitHub services. It may plan bounded reads and guarded issue/PR/release actions, but cannot silently edit, commit, push, merge, or administer repositories.

## Phase 4 Boundary

The Coding Agent remains plan-only. Dedicated file, command, and Git executors may perform only their narrow approved operations; Coding Agent output cannot silently edit, run, commit, push, install, or deploy.

## Batch 2 Integration

Coding plans may describe adapters and future model-provider integration, but cannot install plugins/models, start runtimes, create scheduler jobs, send communication, or bypass existing write/command/commit/push blocks.

Updated: 2026-08-11

## Scope

Prompt 52 adds a local-first Coding Agent for bounded planning and read-only repository diagnostics. It classifies coding requests, inspects safe Git metadata, identifies likely affected areas, proposes implementation and test plans, reviews bounded diff metadata, and explains risk and approval requirements.

The Coding Agent is not an autonomous programmer. Its default and only implemented execution mode is `plan_only`. It has no file-writing, command-execution, commit, push, deployment, dependency-installation, or secret-access method.

## Architecture

The `jarvis/coding/` package contains typed task, plan, inspection, diff-review, result, risk, intent, and status models; a deterministic planner and safety classifier; a read-only Git inspector; a metadata-only diff reviewer; bounded metadata history; and safe CLI rendering.

Prime Agent routes coding and repository-review requests to `coding_agent`. The Agent Registry marks it ready for plan-only support. The Skill Registry exposes safe planning, inspection, diff-review, test-planning, and release-review skills while edit, command, commit, push, and dependency-install skills remain disabled. Model routing for `coding` is advisory and reports unavailable honestly when no ready local coding route exists.

## Repository Inspection

Inspection may read only the current branch, HEAD, short Git status, bounded changed/staged/untracked names, and a short recent-commit summary. Sensitive filenames are redacted, absolute paths are rejected from output, and Git failures return a safe unavailable state. Source files, `.env`, runtime databases, models, and generated artifacts are not copied into output or history.

## Diff Review

Diff review reads bounded `git diff --numstat HEAD` metadata. It reports file names, insertions, deletions, broad risk areas, and test recommendations. It does not copy full diff content. Oversized or binary changes produce warnings and require a narrower future review for content-level analysis.

## Risk Policy

- Low: explanation, status inspection, and test planning.
- Medium: local-file or diff review, refactor planning, and dependency review.
- High: edits, command execution, commits, pushes, deployments, dependency installation, and configuration changes. These remain plan-only and require approval metadata.
- Critical: secret access, broad deletion, force-push, unsafe security-policy changes, destructive production actions, and credential exposure. These are blocked.

Explicit approval metadata does not enable execution in Prompt 52. Future write support requires a separate milestone with scoped permissions, review, tests, and rollback controls.

## Commands

```text
coding status
coding help
coding inspect
coding plan "<request>"
coding risk "<request>"
coding diff
coding review
coding tests "<request>"
coding show <coding_job_id>
coding history
```

All outputs are bounded. `coding history` stores job ID, intent, status, risk, and timestamp only. It does not store the full request or source content.

## Configuration

The `coding` section supports `enabled`, `default_mode`, `max_plan_steps`, `max_files_listed`, `max_diff_chars`, `max_history_items`, `allow_write_operations`, `allow_command_execution`, `require_approval_for_write`, `require_approval_for_push`, and `block_secrets_access`.

Safe defaults enable metadata and planning while disabling writes and command execution. `.env` is not required or modified.

## Runtime Storage

Optional job metadata is written under ignored `data/coding/`. It contains no full source copies, full requests, secrets, private absolute paths, or command output. Git ignores all `data/*` runtime content.

## Deferred Work

Autonomous edits, shell execution, dependency installation, commits, pushes, deployments, broad code-content analysis, and provider-backed coding execution are not implemented. They require separate approved milestones and cannot be inferred from plan-only readiness.
