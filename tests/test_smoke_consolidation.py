from copy import deepcopy
from pathlib import Path

import pytest

from core.real_execution.gate_dag import normalize_checkpoint_evidence
from core.real_execution.smoke_consolidation import consolidate_smoke_results


NORMALIZED_AT = "2026-08-22T12:10:00+00:00"
CONSOLIDATED_AT = "2026-08-22T12:12:00+00:00"
COMPONENT_ORDER = (
    "ACM_CUSTOM_DB",
    "ACM_DB",
    "BDA_DB",
    "SMARTOFFERS_API",
)


def _context(**overrides):
    context = {
        "orchestration_id": "alpha-run-ref",
        "operational_window_ref": "qa4-window-ref",
        "window_started_at": "2026-08-22T12:00:00+00:00",
        "window_expires_at": "2026-08-22T12:15:00+00:00",
        "environment": "qa4",
        "workflow_profile": "smartoffers_qa4_full_smoke",
    }
    context.update(overrides)
    return context


def _base_result(**overrides):
    result = {
        "execution_id": "execution-ref",
        "timestamp": "2026-08-22T12:05:00+00:00",
        "environment": "qa4",
        "attempts_used": 1,
        "retry_count": 0,
        "sensitive_values_logged": False,
        "sanitized_error_category": "NONE",
        "stop_reason": "CHECKPOINT_COMPLETED",
    }
    result.update(overrides)
    return result


def _raw_result(component):
    shared_db_validations = {
        "environment_allowlist": "MATCH",
        "resource_allowlist": "MATCH",
        "destination_allowlist": "MATCH",
        "query_hash_validation": "MATCH",
        "read_only_validation": "PASS",
        "result_shape_validation": "MATCH",
        "fingerprint_validation": "MATCH",
    }
    by_component = {
        "ACM_CUSTOM_DB": _base_result(
            profile="smartoffers_basic_smoke",
            checkpoint="ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01",
            resource_id="acm_custom_db",
            status="CONNECT_AND_READ_OK",
            **shared_db_validations,
        ),
        "ACM_DB": _base_result(
            profile="smartoffers_qa4_full_smoke",
            checkpoint="ORACLE_ACM_TECHNICAL_READ_ONLY_01",
            resource_id="acm_db",
            status="CONNECT_AND_READ_OK",
            preflight_validation="MATCH",
            **shared_db_validations,
        ),
        "BDA_DB": _base_result(
            profile="smartoffers_qa4_full_smoke",
            checkpoint="ORACLE_BDA_TECHNICAL_READ_ONLY_01",
            resource_id="bda_db",
            status="BDA_DB_CHECKPOINT_OK",
            preflight_validation="MATCH",
            **shared_db_validations,
        ),
        "SMARTOFFERS_API": _base_result(
            profile="smartoffers_qa4_full_smoke",
            checkpoint="SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01",
            resource_id="smartoffers_api",
            status="SMARTOFFERS_API_QA4_CHECKPOINT_OK",
            allowlist_validation="MATCH",
            preflight_validation="MATCH",
            path_validation="MATCH",
            path_hash_validation="MATCH",
            fingerprint_validation="MATCH",
            db_gate_bundle_validation="MATCH",
            response_body_logged=False,
            response_headers_logged=False,
        ),
    }
    return deepcopy(by_component[component])


def _record(component, outcome="OK", *, reason=None):
    raw = _raw_result(component)
    terminal_statuses = {
        "ACM_CUSTOM_DB": {
            "FAILED": "CONNECT_AND_READ_FAILED",
            "BLOCKED": "CONNECT_AND_READ_BLOCKED",
        },
        "ACM_DB": {
            "FAILED": "CONNECT_AND_READ_FAILED",
            "BLOCKED": "CONNECT_AND_READ_BLOCKED",
        },
        "BDA_DB": {
            "FAILED": "BDA_DB_CHECKPOINT_FAILED",
            "BLOCKED": "BDA_DB_CHECKPOINT_BLOCKED",
        },
        "SMARTOFFERS_API": {
            "FAILED": "SMARTOFFERS_API_QA4_CHECKPOINT_FAILED",
            "BLOCKED": "SMARTOFFERS_API_QA4_CHECKPOINT_BLOCKED",
        },
    }
    default_reasons = {
        "ACM_CUSTOM_DB": "QUERY_HASH_MISMATCH",
        "ACM_DB": "READ_ONLY_POLICY_VIOLATION",
        "BDA_DB": "FINGERPRINT_DENIED",
        "SMARTOFFERS_API": "DB_CHECKPOINT_GATE_MISSING",
    }
    if outcome != "OK":
        raw.update(
            status=terminal_statuses[component][outcome],
            sanitized_error_category=reason or default_reasons[component],
            stop_reason="IMMEDIATE_STOP",
        )
    return normalize_checkpoint_evidence(
        raw,
        _context(),
        evaluated_at=NORMALIZED_AT,
    )


def _records_with_outcomes(outcomes):
    return [
        _record(component, outcome)
        for component, outcome in zip(COMPONENT_ORDER, outcomes)
    ]


@pytest.mark.parametrize(
    "outcomes,basic_status,full_status",
    (
        (("OK", "OK", "OK", "OK"), "BASIC_SMOKE_OK", "FULL_SMOKE_OK"),
        (
            ("OK", "OK", "BLOCKED", "OK"),
            "BASIC_SMOKE_OK",
            "FULL_SMOKE_PARTIAL",
        ),
        (
            ("BLOCKED", "FAILED", "BLOCKED", "FAILED"),
            "BASIC_SMOKE_FAILED",
            "FULL_SMOKE_FAILED",
        ),
        (
            ("BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"),
            "BASIC_SMOKE_BLOCKED",
            "FULL_SMOKE_BLOCKED",
        ),
    ),
)
def test_consolidation_precedence(outcomes, basic_status, full_status):
    result = consolidate_smoke_results(
        _records_with_outcomes(outcomes),
        _context(),
        evaluated_at=CONSOLIDATED_AT,
    )

    assert result["basic"]["status"] == basic_status
    assert result["full"]["status"] == full_status
    assert result["operational_readiness"] is False
    assert result["authoritative"] is False
    assert result["basic"]["authoritative"] is False
    assert result["full"]["authoritative"] is False


@pytest.mark.parametrize(
    "outcomes",
    (
        ("OK", "OK", "OK", "OK"),
        ("OK", "FAILED", "BLOCKED", "OK"),
    ),
)
def test_global_safety_stop_overrides_ok_and_partial_summaries(outcomes):
    result = consolidate_smoke_results(
        _records_with_outcomes(outcomes),
        _context(),
        evaluated_at=CONSOLIDATED_AT,
        global_safety_stop=True,
    )

    assert result["basic"] == {
        "status": "BASIC_SMOKE_BLOCKED",
        "reason": "GLOBAL_SAFETY_STOP",
        "authoritative": False,
        "components": ["ACM_CUSTOM_DB", "SMARTOFFERS_API"],
    }
    assert result["full"] == {
        "status": "FULL_SMOKE_BLOCKED",
        "reason": "GLOBAL_SAFETY_STOP",
        "authoritative": False,
        "components": list(COMPONENT_ORDER),
    }


def test_missing_and_rejected_inputs_are_blocked_without_promoting_raw_values():
    records = _records_with_outcomes(("OK", "OK", "OK", "OK"))[:-1]
    records.extend(
        (
            "SMARTOFFERS_API_QA4_CHECKPOINT_OK",
            normalize_checkpoint_evidence(
                _raw_result("SMARTOFFERS_API") | {"resource_id": "unknown"},
                _context(),
                evaluated_at=NORMALIZED_AT,
            ),
        )
    )

    result = consolidate_smoke_results(
        records,
        _context(),
        evaluated_at=CONSOLIDATED_AT,
    )

    assert result["components"]["SMARTOFFERS_API"] == {
        "outcome": "BLOCKED",
        "reason": "MISSING_CANONICAL_EVIDENCE",
    }
    assert result["basic"]["status"] == "BASIC_SMOKE_BLOCKED"
    assert result["full"]["status"] == "FULL_SMOKE_PARTIAL"
    assert result["input_rejections"] == [
        "CANONICAL_RECORD_INVALID",
        "CANONICAL_RECORD_INVALID",
    ]


def test_expired_evidence_blocks_every_component():
    result = consolidate_smoke_results(
        _records_with_outcomes(("OK", "OK", "OK", "OK")),
        _context(),
        evaluated_at="2026-08-22T12:15:01+00:00",
    )

    assert result["basic"]["status"] == "BASIC_SMOKE_BLOCKED"
    assert result["full"]["status"] == "FULL_SMOKE_BLOCKED"
    assert result["components"] == {
        component: {
            "outcome": "BLOCKED",
            "reason": "OPERATIONAL_WINDOW_EXPIRED",
        }
        for component in COMPONENT_ORDER
    }


def test_duplicate_component_evidence_is_rejected_deterministically():
    records = _records_with_outcomes(("OK", "OK", "OK", "OK"))
    records.append(deepcopy(records[0]))

    result = consolidate_smoke_results(
        records,
        _context(),
        evaluated_at=CONSOLIDATED_AT,
    )

    assert result["components"]["ACM_CUSTOM_DB"] == {
        "outcome": "BLOCKED",
        "reason": "DUPLICATE_COMPONENT_EVIDENCE",
    }
    assert result["basic"]["status"] == "BASIC_SMOKE_BLOCKED"
    assert result["full"]["status"] == "FULL_SMOKE_PARTIAL"


def test_component_failure_and_block_reasons_are_preserved_together():
    result = consolidate_smoke_results(
        (
            _record("ACM_CUSTOM_DB"),
            _record("ACM_DB", "FAILED", reason="QUERY_HASH_MISMATCH"),
            _record("BDA_DB", "BLOCKED", reason="FINGERPRINT_DENIED"),
            _record("SMARTOFFERS_API"),
        ),
        _context(),
        evaluated_at=CONSOLIDATED_AT,
    )

    assert result["components"]["ACM_DB"] == {
        "outcome": "FAILED",
        "reason": "QUERY_HASH_MISMATCH",
    }
    assert result["components"]["BDA_DB"] == {
        "outcome": "BLOCKED",
        "reason": "FINGERPRINT_DENIED",
    }
    assert result["basic"]["status"] == "BASIC_SMOKE_OK"
    assert result["full"]["status"] == "FULL_SMOKE_PARTIAL"


def test_consolidator_source_has_no_io_or_transport_dependencies():
    source = Path(consolidate_smoke_results.__code__.co_filename).read_text(
        encoding="utf-8"
    )

    for forbidden in (
        "import requests",
        "import urllib",
        "import socket",
        "import subprocess",
        "import os",
        "open(",
        ".send(",
        "popen(",
    ):
        assert forbidden not in source.lower()
