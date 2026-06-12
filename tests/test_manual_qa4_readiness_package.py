import re
from pathlib import Path

import core.real_execution as real_execution
from core.execution.service import AdapterRunModeError, run_adapter_scenario


ROOT = Path(__file__).resolve().parents[1]
REAL_EXECUTION_DOCS = ROOT / "ai" / "real-execution"
REAL_EXECUTION_CODE = ROOT / "core" / "real_execution"

PACKAGE_DOCS = (
    "manual-qa4-readiness-package.md",
    "manual-qa4-operator-script-template.md",
    "manual-qa4-approval-template.md",
    "manual-qa4-evidence-template.md",
)


def _read_doc(name):
    return (REAL_EXECUTION_DOCS / name).read_text(encoding="utf-8")


def test_manual_qa4_readiness_package_docs_exist_and_are_ascii():
    for name in PACKAGE_DOCS:
        path = REAL_EXECUTION_DOCS / name
        assert path.exists(), name
        path.read_text(encoding="ascii")


def test_templates_use_placeholders_and_required_contract_fields():
    operator = _read_doc("manual-qa4-operator-script-template.md")
    approval = _read_doc("manual-qa4-approval-template.md")
    evidence = _read_doc("manual-qa4-evidence-template.md")

    for text in (operator, approval, evidence):
        assert re.search(r"<[A-Z0-9_]+>", text)

    for field in (
        "approved",
        "risk_acceptance",
        "approver_ref",
        "ticket_ref",
        "approved_api_id",
        "approved_environment",
        "approved_at_ref",
    ):
        assert field in approval

    for field in (
        "session_ref",
        "api_id",
        "method",
        "environment",
        "decision",
        "approval_reference",
        "ticket_reference",
        "correlation_reference",
        "risk_status",
        "readiness_decision",
        "allowlist_decision",
        "real_call_executed",
        "body_recorded",
    ):
        assert field in evidence


def test_manual_package_does_not_contain_real_value_shapes():
    combined = "\n".join(_read_doc(name) for name in PACKAGE_DOCS)
    lower_text = combined.lower()

    assert "http://" not in lower_text
    assert "https://" not in lower_text
    assert not re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", combined)
    assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", combined)
    assert not re.search(r"\b\d{10,}\b", combined)
    assert "bearer " not in lower_text
    assert "cookie:" not in lower_text


def test_manual_package_keeps_execution_human_only_and_non_automated():
    package = _read_doc("manual-qa4-readiness-package.md").lower()
    operator = _read_doc("manual-qa4-operator-script-template.md").lower()

    assert "nao autoriza execucao real" in package
    assert "nenhuma execucao automatica" in package
    assert "nao um script executavel" in operator
    assert "nenhuma chamada oracle" in package


def test_real_execution_public_package_still_hides_manual_real_call_paths():
    assert not hasattr(real_execution, "RealHttpClient")
    assert not hasattr(real_execution, "execute_first_qa4_call_manual")
    assert "RealHttpClient" not in real_execution.__all__
    assert "execute_first_qa4_call_manual" not in real_execution.__all__


def test_http_import_policy_remains_isolated_to_real_client_module():
    http_marker = "urllib" + ".request"
    matches = []
    for path in REAL_EXECUTION_CODE.glob("*.py"):
        if http_marker in path.read_text(encoding="utf-8"):
            matches.append(path.name)

    assert matches == ["real_http_client.py"]


def test_adapter_run_real_mode_remains_blocked():
    try:
        run_adapter_scenario({"id": "manual-qa4-readiness"}, mode="real")
    except AdapterRunModeError as exc:
        assert "mode real bloqueado" in str(exc)
    else:
        raise AssertionError("adapter-run mode=real must remain blocked")
