"""Bounded CLI rendering for the Coding Agent."""

from __future__ import annotations

from .agent import CodingAgent


def render_coding_command(agent: CodingAgent, command: str, arguments: tuple[str, ...]) -> str:
    if command == "coding status":
        status = agent.status()
        return "Coding status: " + " ".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in status.items())
    if command == "coding help":
        return "Coding commands: coding status, help, inspect, plan <request>, risk <request>, diff, review, tests <request>, show <id>, history. All operations are read-only or plan-only."
    if command == "coding inspect":
        result = agent.inspect(); item = result.repo_inspection
        return f"Coding repo: status={result.status.value} branch={item.branch} head={item.head[:12]} tracked_clean={'yes' if item.tracked_clean else 'no'} staged={len(item.staged_files)} changed={len(item.changed_files)} untracked={len(item.untracked_summary)} warnings={'; '.join(item.warnings) or 'none'}"
    if command in {"coding diff", "coding review"}:
        result = agent.review(); item = result.diff_review
        return f"Coding diff: status={result.status.value} files={len(item.files_changed)} insertions={item.insertions} deletions={item.deletions} summary={item.summary} risks={'; '.join(item.risks) or 'none'} warnings={'; '.join(item.warnings) or 'none'}"
    if command == "coding history":
        records = agent.history_records()[-10:]
        return "Coding history: " + (", ".join(f"{item.request_id}:{item.intent}:{item.status}:{item.risk_level}" for item in records) or "none")
    if command == "coding show":
        request_id = arguments[0] if arguments else ""
        result = agent.show(request_id)
        if result is None:
            record = agent.show_record(request_id)
            if record is None:
                return "Coding result not found."
            return f"Coding result: id={record.request_id} status={record.status} intent={record.intent} risk={record.risk_level} metadata_only=yes"
        intent = result.task.intent.value if result.task else "unknown"
        return f"Coding result: id={result.request_id} status={result.status.value} intent={intent} has_plan={'yes' if result.plan else 'no'} has_repo={'yes' if result.repo_inspection else 'no'} has_diff={'yes' if result.diff_review else 'no'}"
    request = " ".join(arguments).strip()
    if not request:
        return f"Usage: {command} <request>"
    if command == "coding risk":
        decision = agent.risk(request)
        return f"Coding risk: risk={decision.risk_level.value} allowed={'yes' if decision.allowed else 'no'} approval_required={'yes' if decision.approval_required else 'no'} reason={decision.reason}"
    result = agent.plan(request); plan = result.plan
    if plan is None:
        return f"Coding plan: status={result.status.value} error={result.error or 'unavailable'}"
    if command == "coding tests":
        return f"Coding tests: id={result.request_id} intent={plan.intent.value} recommendations=" + " | ".join(plan.required_tests)
    return f"Coding plan: id={result.request_id} intent={plan.intent.value} status={plan.status.value} risk={plan.risk_level.value} approval_required={'yes' if plan.approval_required else 'no'} files={','.join(plan.likely_files) or 'unknown'} steps=" + " | ".join(plan.proposed_steps)
