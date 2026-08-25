from pathlib import Path

from core.real_execution import qa4_standard_mock_facade
from core.real_execution import run_standard_qa4_application_mock

EVALUATED_AT = "2026-08-22T12:10:00+00:00"


def _context():
    return {
        "orchestration_id": "alpha-run-ref",
        "operational_window_ref": "qa4-window-ref",
        "window_started_at": "2026-08-22T12:00:00+00:00",
        "window_expires_at": "2026-08-22T12:15:00+00:00",
        "environment": "qa4",
        "workflow_profile": "smartoffers_qa4_full_smoke",
    }


def test_standard_application_mock_facade_runs_closed_canned_flow_in_gate_order():
    result = run_standard_qa4_application_mock(
        _context(), mode="mock", evaluated_at=EVALUATED_AT
    )

    assert [record["component"] for record in result["records"]] == [
        "ACM_CUSTOM_DB", "ACM_DB", "BDA_DB", "SMARTOFFERS_API"
    ]
    assert result["full"]["status"] == "FULL_SMOKE_OK"
    assert result["result"] == "PASS"
    assert result["authoritative"] is False
    assert result["operational_readiness"] is False


def test_standard_application_mock_facade_blocks_non_mock_mode_without_results():
    result = run_standard_qa4_application_mock(
        _context(), mode="real", evaluated_at=EVALUATED_AT
    )

    assert result["records"] == []
    assert result["full"]["status"] == "FULL_SMOKE_BLOCKED"
    assert result["result"] == "BLOCKED"
    assert result["authoritative"] is False
    assert result["operational_readiness"] is False


def test_standard_application_mock_facade_blocks_variant_copy_and_invalid_context():
    for context in (
        _context() | {"workflow_profile": "smartoffers_variant_smoke"},
        _context() | {"workflow_profile": "smartoffers_copy_smoke"},
        {"workflow_profile": "smartoffers_qa4_full_smoke"},
    ):
        result = run_standard_qa4_application_mock(
            context, mode="mock", evaluated_at=EVALUATED_AT
        )

        assert result["full"]["status"] == "FULL_SMOKE_BLOCKED"
        assert result["result"] == "BLOCKED"
        assert result["authoritative"] is False
        assert result["operational_readiness"] is False


def test_standard_application_mock_facade_output_never_contains_unsanitized_context_values():
    result = run_standard_qa4_application_mock(
        _context() | {"secret": "must-not-appear"},
        mode="mock",
        evaluated_at=EVALUATED_AT,
    )

    assert "must-not-appear" not in repr(result)


def test_standard_application_mock_facade_has_no_transport_or_runtime_imports():
    source = Path("core/real_execution/qa4_standard_mock_facade.py").read_text()

    for forbidden in ("subprocess", "requests", "urllib", "socket", "oracle", "runtime"):
        assert f"import {forbidden}" not in source


def test_standard_application_mock_facade_reports_fail_for_partial_full_smoke(
    monkeypatch,
):
    monkeypatch.setattr(
        qa4_standard_mock_facade,
        "run_standard_qa4_mock",
        lambda *_args, **_kwargs: {
            "records": [],
            "full": {"status": "FULL_SMOKE_PARTIAL"},
            "authoritative": False,
            "operational_readiness": False,
        },
    )

    result = run_standard_qa4_application_mock(
        _context(), mode="mock", evaluated_at=EVALUATED_AT
    )

    assert result["result"] == "FAIL"
    assert result["authoritative"] is False
    assert result["operational_readiness"] is False
