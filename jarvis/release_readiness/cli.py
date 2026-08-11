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
    if command == "release-readiness matrix":
        return "Compatibility matrix: " + "; ".join(
            f"{item.source}->{item.target}={item.status}" for item in report.compatibility
        )
    if command == "release-readiness scenarios":
        return "Validation scenarios: " + "; ".join(
            f"{item.scenario_id}={item.status.value}" for item in report.scenarios
        )
    if command == "release-readiness scorecard":
        average = round(sum(item.score for item in report.scorecard) / len(report.scorecard))
        details = "; ".join(f"{item.category}={item.score}" for item in report.scorecard)
        return f"Production-readiness scorecard: average={average}; {details}"
    if command == "release-readiness checklist":
        mandatory = sum(g.blocking for g in report.gates)
        passed = sum(g.blocking and g.status.value == "passed" for g in report.gates)
        return f"Integration checklist: mandatory={passed}/{mandatory} contracts={len(report.contracts)} compatibility={len(report.compatibility)} scenarios={len(report.scenarios)} publication_authorized=no"
    if command == "release-readiness verify":
        return f"Phase 5 verification: mandatory_passed={'yes' if report.mandatory_passed else 'no'} status={report.status.value} missing={len(report.missing_components)} api_status_only=yes phase6_started=no"
    if command == "release-readiness help":
        return "release-readiness status|gates|contracts|missing|candidate|matrix|scenarios|scorecard|checklist|verify. Validation only; no tag, release, deployment, or execution."
    return "Release-readiness command unavailable."
