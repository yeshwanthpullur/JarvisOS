"""Bounded CLI output for Prompt 85 validation."""

from .evaluator import ReleaseReadinessEvaluator


def render_release_command(evaluator: ReleaseReadinessEvaluator, command: str, args=()) -> str:
    report = evaluator.evaluate()
    if command == "release-readiness status":
        return f"Release readiness: status={report.status.value} passed={report.passed}/{len(report.gates)} blocked={report.blocked} missing_phase5={len(report.missing_components)} release_authorized=no"
    if command == "release-readiness gates":
        return "Release gates: " + "; ".join(f"{g.gate_id}={g.status.value}" for g in report.gates)
    if command == "release-readiness contracts":
        return "System contracts: " + "; ".join(f"{c.component}={c.verification_status.value}" for c in report.contracts)
    if command == "release-readiness missing":
        return "Missing Phase 5 components: " + (", ".join(report.missing_components) or "none")
    if command == "release-readiness candidate":
        c = evaluator.candidate()
        return f"Release candidate: version={c.version} status={c.status.value} branch={c.branch} blocking={','.join(c.blocking_gate_ids) or 'none'} tag_created=no release_created=no"
    if command == "release-readiness help":
        return "release-readiness status|gates|contracts|missing|candidate. Validation only; no tag, release, deployment, or execution."
    return "Release-readiness command unavailable."
