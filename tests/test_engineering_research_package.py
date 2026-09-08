from pathlib import Path

import pytest

from jarvis.research import ResearchEvidence, ResearchSourceType
from jarvis.revenue import EngineeringResearchPackage, ResearchPackageRequest
from jarvis.skills import build_default_skill_registry


def request(topic="compare local inference runtimes"):
    return ResearchPackageRequest(topic=topic, objective="Choose a bounded local engineering path")


def evidence():
    return (ResearchEvidence("e1", ResearchSourceType.USER, "Synthetic source", "synthetic://source-1", "Local evidence for testing.", .8),)


def test_skill_manifest_is_explicit_and_reusable():
    manifest = EngineeringResearchPackage().skill_manifest()
    assert manifest["skill_id"] == "EngineeringResearchPackage"
    assert "quality" in manifest["workflow"]
    assert "quality_report" in manifest["outputs"]


def test_run_creates_isolated_quality_gated_deliverable(tmp_path: Path):
    record, quality, result = EngineeringResearchPackage().run(request(), tmp_path / "r1-001", evidence=evidence(), provider_state="synthetic")
    assert record.status == "completed_review_required"
    assert quality.passed is True
    assert result.summary is not None
    assert (tmp_path / "r1-001" / "output" / "final_report.md").is_file()
    assert (tmp_path / "r1-001" / "audit" / "run_record.json").is_file()


def test_missing_evidence_is_degraded_and_honest(tmp_path: Path):
    record, quality, result = EngineeringResearchPackage().run(request(), tmp_path / "r1-002")
    assert record.status == "degraded"
    assert quality.passed is False
    assert "evidence_unavailable" in quality.failures
    assert result.summary is not None


def test_unconfigured_provider_cannot_pass_quality_gate(tmp_path: Path):
    _, quality, _ = EngineeringResearchPackage().run(request(), tmp_path / "r1-003", evidence=evidence(), provider_state="unconfigured")
    assert quality.passed is False
    assert "provider_not_verified" in quality.failures


def test_skill_registry_contains_research_package_skill():
    skill = build_default_skill_registry().get_skill("engineering_research_package_skill")
    assert skill is not None
    assert skill.enabled is True


def test_secret_shaped_request_is_rejected():
    with pytest.raises(ValueError, match="secret_shaped"):
        ResearchPackageRequest(topic="api_key=not-a-request", objective="test")
