# GitHub Provider

Phase 6 `github branch` and `github commits` can report bounded local Git metadata without requiring or exposing a token. Remote API operations continue through the existing disabled-by-default GitHub Provider and its repository scope, approval, and Broker policy.

Prompt 75 adds a repository-scoped GitHub service adapter. It is disabled and unverified by default. When configured, it supports bounded repository, issue, pull-request, release, workflow, and check reads. A working Git remote never implies GitHub API authentication.

Local Git remains authoritative for status, diff, stage, commit, tag, and push. GitHub issue, PR, and release mutations are separate data-egress actions requiring an enabled capability, exact repository/content approval, and an action-specific Execution Broker tool. PR merge, workflow execution, secret mutation, administration, force push, deletion, arbitrary cloning, and third-party code execution remain blocked.

The `github` CLI namespace exposes status, auth, health, repository scope, capabilities, rate state, bounded reads/plans, guarded create commands, and metadata-only history.
