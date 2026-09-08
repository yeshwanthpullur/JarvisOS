from pathlib import Path

from jarvis.final_block import FinalBlockRuntime, OperatingMode


ROOT = Path(__file__).resolve().parents[1]


def test_post122_operating_modes_default_is_safe():
    runtime = FinalBlockRuntime(root=ROOT)
    status = runtime.status()
    assert status["operating_mode"] == "DEVELOPMENT/TESTING"
    assert tuple(runtime.operating_modes()) == tuple(mode.value for mode in OperatingMode)


def test_post122_activation_documents_exist():
    required = (
        "POST_122_AUDIT.md", "LAPTOP_BASELINE.md", "STARTUP.md", "SHUTDOWN.md",
        "TROUBLESHOOTING.md", "REVENUE_READY_STATUS.md", "INCOME_AUTOMATION_ROADMAP.md",
        "TOOL_COSTS.md", "DEVICE_ARCHITECTURE.md", "PHONE_MIGRATION_PLAN.md",
        "DEVICE_SECURITY.md", "DEVICE_RECOVERY.md",
    )
    assert all((ROOT / "docs" / name).is_file() for name in required)


def test_post122_service_templates_are_complete():
    base = ROOT / "JARVIS_OS" / "10_AUTOMATION" / "SERVICES"
    services = ("ENGINEERING_RESEARCH_PACKAGE", "TECHNICAL_PROJECT_DOCUMENTATION", "SHORT_FORM_TECHNICAL_CONTENT")
    files = ("README.md", "workflow.md", "input_schema.md", "output_schema.md", "quality_gate.md", "cost_model.md", "privacy.md", "fallbacks.md")
    for service in services:
        for name in files:
            assert (base / service / name).is_file()


def test_post122_revenue_status_does_not_overclaim():
    text = (ROOT / "docs" / "REVENUE_READY_STATUS.md").read_text(encoding="utf-8")
    assert "R0 Foundation" in text and "READY_FOUNDATION" in text
    for milestone in ("R1 First useful deliverable", "R2 First external user", "R3 First legitimate payment", "R4 Repeat delivery", "R5 Positive unit economics", "R6 Subscription independence"):
        assert milestone in text
    assert "NOT_STARTED" in text


def test_post122_customer_and_device_boundaries_are_explicit():
    client = (ROOT / "JARVIS_OS" / "10_AUTOMATION" / "CLIENT_WORK" / "README.md").read_text(encoding="utf-8")
    phone = (ROOT / "docs" / "PHONE_MIGRATION_PLAN.md").read_text(encoding="utf-8")
    assert "separate" in client.lower() and "never" in client.lower()
    assert "planning-only" in phone and "untouched" in phone
