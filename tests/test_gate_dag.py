from copy import deepcopy

import pytest

from core.real_execution.gate_dag import (
    CANONICAL_DB_GATE_NAMES,
    CANONICAL_EVIDENCE_BLOCKED,
    CANONICAL_EVIDENCE_VALID,
    DB_CHECKPOINT_GATES_BLOCKED,
    DB_CHECKPOINT_GATES_READY,
    GATE_SCHEMA_VERSION,
    normalize_checkpoint_evidence,
    validate_api_db_gate_bundle,
    validate_canonical_evidence_record,
)


EVALUATED_AT = "2026-08-22T12:10:00+00:00"


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


def _acm_custom_result(**overrides):
    return _base_result(
        **{
            "profile": "smartoffers_basic_smoke",
            "checkpoint": "ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01",
            "resource_id": "acm_custom_db",
            "status": "CONNECT_AND_READ_OK",
            "environment_allowlist": "MATCH",
            "resource_allowlist": "MATCH",
            "destination_allowlist": "MATCH",
            "query_hash_validation": "MATCH",
            "read_only_validation": "PASS",
            "result_shape_validation": "MATCH",
            "fingerprint_validation": "MATCH",
            **overrides,
        }
    )


def _acm_result(**overrides):
    return _base_result(
        **{
            "profile": "smartoffers_qa4_full_smoke",
            "checkpoint": "ORACLE_ACM_TECHNICAL_READ_ONLY_01",
            "resource_id": "acm_db",
            "status": "CONNECT_AND_READ_OK",
            "environment_allowlist": "MATCH",
            "resource_allowlist": "MATCH",
            "destination_allowlist": "MATCH",
            "query_hash_validation": "MATCH",
            "read_only_validation": "PASS",
            "result_shape_validation": "MATCH",
            "preflight_validation": "MATCH",
            "fingerprint_validation": "MATCH",
            **overrides,
        }
    )


def _bda_result(**overrides):
    return _base_result(
        **{
            "profile": "smartoffers_qa4_full_smoke",
            "checkpoint": "ORACLE_BDA_TECHNICAL_READ_ONLY_01",
            "resource_id": "bda_db",
            "status": "BDA_DB_CHECKPOINT_OK",
            "environment_allowlist": "MATCH",
            "resource_allowlist": "MATCH",
            "destination_allowlist": "MATCH",
            "query_hash_validation": "MATCH",
            "read_only_validation": "PASS",
            "result_shape_validation": "MATCH",
            "preflight_validation": "MATCH",
            "fingerprint_validation": "MATCH",
            **overrides,
        }
    )


def _api_result(**overrides):
    return _base_result(
        **{
            "profile": "smartoffers_qa4_full_smoke",
            "checkpoint": "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01",
            "resource_id": "smartoffers_api",
            "status": "SMARTOFFERS_API_QA4_CHECKPOINT_OK",
            "allowlist_validation": "MATCH",
            "preflight_validation": "MATCH",
            "path_validation": "MATCH",
            "path_hash_validation": "MATCH",
            "fingerprint_validation": "MATCH",
            "db_gate_bundle_validation": "MATCH",
            "response_body_logged": False,
            "response_headers_logged": False,
            **overrides,
        }
    )


def _normalize(raw, context=None, evaluated_at=EVALUATED_AT):
    return normalize_checkpoint_evidence(
        raw,
        _context() if context is None else context,
        evaluated_at=evaluated_at,
    )


def _valid_db_records(context=None, evaluated_at=EVALUATED_AT):
    effective_context = _context() if context is None else context
    return [
        normalize_checkpoint_evidence(
            raw, effective_context, evaluated_at=evaluated_at
        )
        for raw in (_acm_custom_result(), _acm_result(), _bda_result())
    ]


def _rejected(reason):
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "record_type": "canonical_checkpoint_evidence",
        "evidence_status": "REJECTED",
        "rejection_reason": reason,
    }


def test_normalizes_each_exact_success_to_its_canonical_gate():
    cases = (
        (_acm_custom_result(), "ACM_CUSTOM_DB", "ACM_CUSTOM_DB_CHECKPOINT_OK"),
        (_acm_result(), "ACM_DB", "ACM_DB_CHECKPOINT_OK"),
        (_bda_result(), "BDA_DB", "BDA_DB_CHECKPOINT_OK"),
        (_api_result(), "SMARTOFFERS_API", "SMARTOFFERS_API_QA4_CHECKPOINT_OK"),
    )

    for raw, component, gate_name in cases:
        record = _normalize(raw)

        assert record["evidence_status"] == "VALID"
        assert record["component"] == component
        assert record["outcome"] == "OK"
        assert record["gate_name"] == gate_name
        assert record["orchestration_id"] == "alpha-run-ref"
        assert record["operational_window_ref"] == "qa4-window-ref"
        assert record["source_execution_id"] == "execution-ref"
        assert set(record["validations"]) <= set(raw)


@pytest.mark.parametrize(
    "field,value,reason",
    (
        ("resource_id", "bda_db", "UNKNOWN_CHECKPOINT_RESOURCE"),
        ("environment", "production", "SOURCE_IDENTITY_MISMATCH"),
        ("profile", "smartoffers_basic_smoke", "SOURCE_IDENTITY_MISMATCH"),
        ("status", "BDA_DB_CHECKPOINT_OK", "SOURCE_STATUS_MISMATCH"),
        ("attempts_used", 2, "ATTEMPT_POLICY_MISMATCH"),
        ("attempts_used", True, "ATTEMPT_POLICY_MISMATCH"),
        ("retry_count", 1, "ATTEMPT_POLICY_MISMATCH"),
        ("retry_count", False, "ATTEMPT_POLICY_MISMATCH"),
        ("sensitive_values_logged", True, "SENSITIVE_LOGGING_DENIED"),
        ("fingerprint_validation", "DENIED", "SUCCESS_VALIDATION_MISMATCH"),
    ),
)
def test_rejects_noncanonical_success_evidence(field, value, reason):
    raw = _acm_result()
    raw[field] = value

    assert _normalize(raw) == _rejected(reason)


@pytest.mark.parametrize(
    "raw,reason",
    (
        ({}, "UNKNOWN_CHECKPOINT_RESOURCE"),
        (
            _acm_result(checkpoint="ORACLE_UNKNOWN_TECHNICAL_READ_ONLY_01"),
            "UNKNOWN_CHECKPOINT_RESOURCE",
        ),
        (_acm_result(execution_id=""), "SOURCE_EXECUTION_ID_MISSING"),
        (_acm_result(timestamp="not-a-timestamp"), "SOURCE_TIMESTAMP_INVALID"),
        (
            _acm_result(timestamp="2026-08-22T11:59:59+00:00"),
            "SOURCE_OUTSIDE_OPERATIONAL_WINDOW",
        ),
        (
            _acm_result(timestamp="2026-08-22T12:15:01+00:00"),
            "SOURCE_OUTSIDE_OPERATIONAL_WINDOW",
        ),
        (
            _acm_result(timestamp="2026-08-22T12:11:00+00:00"),
            "SOURCE_TIMESTAMP_IN_FUTURE",
        ),
    ),
)
def test_rejects_unknown_or_invalid_provenance(raw, reason):
    assert _normalize(raw) == _rejected(reason)


@pytest.mark.parametrize(
    "checkpoint,resource_id",
    (
        ([], "acm_db"),
        ("ORACLE_ACM_TECHNICAL_READ_ONLY_01", []),
    ),
)
def test_normalizer_rejects_non_string_checkpoint_identity_without_raising(
    checkpoint, resource_id
):
    raw = _acm_result(checkpoint=checkpoint, resource_id=resource_id)

    assert _normalize(raw) == _rejected("UNKNOWN_CHECKPOINT_RESOURCE")


@pytest.mark.parametrize(
    "context,evaluated_at,reason",
    (
        ({}, EVALUATED_AT, "ORCHESTRATION_CONTEXT_INVALID"),
        (
            _context(window_started_at="not-a-timestamp"),
            EVALUATED_AT,
            "ORCHESTRATION_CONTEXT_INVALID",
        ),
        (
            _context(),
            "2026-08-22T12:15:01+00:00",
            "OPERATIONAL_WINDOW_EXPIRED",
        ),
        (_context(), "not-a-timestamp", "EVALUATED_AT_INVALID"),
    ),
)
def test_rejects_invalid_or_expired_context(context, evaluated_at, reason):
    assert _normalize(_acm_result(), context, evaluated_at) == _rejected(reason)


def test_successful_record_contains_only_the_canonical_safe_shape():
    raw = _acm_result(runtime_secret="must-not-be-copied", endpoint="not-safe")

    record = _normalize(raw)

    assert record == {
        "schema_version": GATE_SCHEMA_VERSION,
        "record_type": "canonical_checkpoint_evidence",
        "evidence_status": "VALID",
        "component": "ACM_DB",
        "outcome": "OK",
        "gate_name": "ACM_DB_CHECKPOINT_OK",
        "orchestration_id": "alpha-run-ref",
        "operational_window_ref": "qa4-window-ref",
        "window_started_at": "2026-08-22T12:00:00+00:00",
        "window_expires_at": "2026-08-22T12:15:00+00:00",
        "workflow_profile": "smartoffers_qa4_full_smoke",
        "source_execution_id": "execution-ref",
        "source_timestamp": "2026-08-22T12:05:00+00:00",
        "source_environment": "qa4",
        "source_profile": "smartoffers_qa4_full_smoke",
        "source_checkpoint": "ORACLE_ACM_TECHNICAL_READ_ONLY_01",
        "source_resource_id": "acm_db",
        "source_status": "CONNECT_AND_READ_OK",
        "sanitized_error_category": "NONE",
        "stop_reason": "CHECKPOINT_COMPLETED",
        "validations": {
            "environment_allowlist": "MATCH",
            "resource_allowlist": "MATCH",
            "destination_allowlist": "MATCH",
            "query_hash_validation": "MATCH",
            "read_only_validation": "PASS",
            "result_shape_validation": "MATCH",
            "preflight_validation": "MATCH",
            "fingerprint_validation": "MATCH",
            "sensitive_values_logged": False,
        },
    }


def test_revalidates_a_current_record_without_promoting_raw_or_rejected_input():
    valid = _normalize(_acm_result())

    assert validate_canonical_evidence_record(
        valid, _context(), evaluated_at=EVALUATED_AT
    ) == {"status": CANONICAL_EVIDENCE_VALID, "reason": "NONE"}
    assert validate_canonical_evidence_record(
        _acm_result(), _context(), evaluated_at=EVALUATED_AT
    )["status"] == CANONICAL_EVIDENCE_BLOCKED
    assert validate_canonical_evidence_record(
        _rejected("SOURCE_STATUS_MISMATCH"),
        _context(),
        evaluated_at=EVALUATED_AT,
    )["status"] == CANONICAL_EVIDENCE_BLOCKED


@pytest.mark.parametrize(
    "raw,outcome",
    (
        (
            _acm_result(
                status="FAILED",
                sanitized_error_category="READ_ONLY_POLICY_VIOLATION",
                stop_reason="IMMEDIATE_STOP",
                result_shape_validation="DENIED",
            ),
            "FAILED",
        ),
        (
            _api_result(
                status="SMARTOFFERS_API_QA4_CHECKPOINT_BLOCKED",
                sanitized_error_category="DB_CHECKPOINT_GATE_MISSING",
                stop_reason="IMMEDIATE_STOP",
                db_gate_bundle_validation="DENIED",
            ),
            "BLOCKED",
        ),
    ),
)
def test_normalizes_sanitized_non_ok_terminal_evidence_without_promoting_it(raw, outcome):
    record = _normalize(raw)

    assert record["evidence_status"] == "VALID"
    assert record["outcome"] == outcome
    assert validate_canonical_evidence_record(
        record, _context(), evaluated_at=EVALUATED_AT
    ) == {"status": CANONICAL_EVIDENCE_VALID, "reason": "NONE"}


@pytest.mark.parametrize("status", ("FAILED", "BLOCKED"))
def test_non_ok_evidence_rejects_unsanitized_validation_label_without_copying_it(
    status,
):
    raw = _acm_result(
        status=status,
        sanitized_error_category="READ_ONLY_POLICY_VIOLATION",
        stop_reason="IMMEDIATE_STOP",
        query_hash_validation="password=secret",
    )

    assert _normalize(raw) == _rejected("VALIDATION_VALUE_INVALID")


@pytest.mark.parametrize(
    "change,reason",
    (
        ({"runtime_secret": "not-canonical"}, "CANONICAL_RECORD_INVALID"),
        (
            {
                "validations": {
                    **_normalize(_acm_result())["validations"],
                    "endpoint": "unsafe",
                }
            },
            "CANONICAL_RECORD_VALIDATION_MISMATCH",
        ),
    ),
)
def test_revalidation_rejects_noncanonical_extra_fields(change, reason):
    record = {**_normalize(_acm_result()), **change}

    assert validate_canonical_evidence_record(
        record, _context(), evaluated_at=EVALUATED_AT
    ) == {
        "status": CANONICAL_EVIDENCE_BLOCKED,
        "reason": reason,
    }


@pytest.mark.parametrize(
    "source_checkpoint,source_resource_id",
    (
        ([], "acm_db"),
        ("ORACLE_ACM_TECHNICAL_READ_ONLY_01", []),
    ),
)
def test_revalidation_rejects_non_string_checkpoint_identity_without_raising(
    source_checkpoint, source_resource_id
):
    record = {
        **_normalize(_acm_result()),
        "source_checkpoint": source_checkpoint,
        "source_resource_id": source_resource_id,
    }

    assert validate_canonical_evidence_record(
        record, _context(), evaluated_at=EVALUATED_AT
    ) == {
        "status": CANONICAL_EVIDENCE_BLOCKED,
        "reason": "CANONICAL_RECORD_IDENTITY_MISMATCH",
    }


@pytest.mark.parametrize("status", ("FAILED", "BLOCKED"))
def test_revalidation_rejects_unsanitized_validation_label(status):
    record = _normalize(
        _acm_result(
            status=status,
            sanitized_error_category="READ_ONLY_POLICY_VIOLATION",
            stop_reason="IMMEDIATE_STOP",
            query_hash_validation="DENIED",
        )
    )
    record["validations"]["query_hash_validation"] = "password=secret"

    assert validate_canonical_evidence_record(
        record, _context(), evaluated_at=EVALUATED_AT
    ) == {
        "status": CANONICAL_EVIDENCE_BLOCKED,
        "reason": "CANONICAL_RECORD_VALIDATION_MISMATCH",
    }


@pytest.mark.parametrize(
    "change,reason",
    (
        ({"schema_version": "historical.v0"}, "CANONICAL_RECORD_INVALID"),
        ({"record_type": "raw_executor_result"}, "CANONICAL_RECORD_INVALID"),
        ({"evidence_status": "REJECTED"}, "CANONICAL_RECORD_INVALID"),
        ({"orchestration_id": "historical-run"}, "CONTEXT_MISMATCH"),
        ({"source_timestamp": "not-a-timestamp"}, "SOURCE_TIMESTAMP_INVALID"),
        (
            {"source_timestamp": "2026-08-22T12:11:00+00:00"},
            "SOURCE_TIMESTAMP_IN_FUTURE",
        ),
    ),
)
def test_revalidation_rejects_tampered_or_stale_records(change, reason):
    record = {**_normalize(_acm_result()), **change}

    assert validate_canonical_evidence_record(
        record, _context(), evaluated_at=EVALUATED_AT
    ) == {"status": CANONICAL_EVIDENCE_BLOCKED, "reason": reason}


def test_api_bundle_requires_exactly_three_current_structured_ok_gates():
    records = _valid_db_records()
    ready = validate_api_db_gate_bundle(
        records, _context(), evaluated_at=EVALUATED_AT
    )

    assert ready == {
        "status": DB_CHECKPOINT_GATES_READY,
        "reason": "NONE",
        "gate_names": list(CANONICAL_DB_GATE_NAMES),
    }

    invalid_inputs = (
        list(CANONICAL_DB_GATE_NAMES),
        records[:2],
        records + [records[0]],
        [{**records[0], "orchestration_id": "historical-run"}, *records[1:]],
        [deepcopy(records[0]), deepcopy(records[0]), deepcopy(records[2])],
        [{**records[0], "outcome": "BLOCKED"}, *records[1:]],
        [_normalize(_api_result()), *records[1:]],
    )
    for invalid in invalid_inputs:
        blocked = validate_api_db_gate_bundle(
            invalid, _context(), evaluated_at=EVALUATED_AT
        )
        assert blocked["status"] == DB_CHECKPOINT_GATES_BLOCKED
        assert blocked["gate_names"] == []


def test_api_bundle_rejects_expired_evaluation_and_cross_window_records():
    records = _valid_db_records()

    expired = validate_api_db_gate_bundle(
        records,
        _context(),
        evaluated_at="2026-08-22T12:15:01+00:00",
    )
    mixed_window = validate_api_db_gate_bundle(
        [
            {
                **records[0],
                "operational_window_ref": "historical-window",
            },
            *records[1:],
        ],
        _context(),
        evaluated_at=EVALUATED_AT,
    )

    assert expired == {
        "status": DB_CHECKPOINT_GATES_BLOCKED,
        "reason": "OPERATIONAL_WINDOW_EXPIRED",
        "gate_names": [],
    }
    assert mixed_window == {
        "status": DB_CHECKPOINT_GATES_BLOCKED,
        "reason": "CONTEXT_MISMATCH",
        "gate_names": [],
    }
