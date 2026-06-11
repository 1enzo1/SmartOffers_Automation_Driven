import copy

from core.real_execution.runtime import validate_runtime_contract


def _safe_runtime():
    return {
        "QA4_HOST_REF": "runtime-ref:endpoint-approved-for-manual-review",
        "AUTH_REF": "runtime-ref:auth-material-approved-for-manual-review",
        "SENSITIVE_HEADERS_REF": "runtime-ref:headers-approved-for-manual-review",
        "TEST_PAYLOAD_REF": "runtime-ref:body-approved-for-manual-review",
        "CORRELATION_ID": "corr-safe-001",
    }


def test_incomplete_runtime_blocks():
    result = validate_runtime_contract({"QA4_HOST_REF": "runtime-ref:endpoint"})

    assert result["valid"] is False
    assert "missing_auth_ref" in result["blocked_reasons"]
    assert "missing_sensitive_headers_ref" in result["blocked_reasons"]
    assert "missing_test_payload_ref" in result["blocked_reasons"]
    assert "missing_correlation_id" in result["blocked_reasons"]


def test_raw_endpoint_auth_and_body_values_block():
    cases = [
        {"HOST": "redacted-runtime-reference"},
        {"TOKEN": "redacted-runtime-reference"},
        {"body": {"real_payload": True}},
        {"target": "999.999.999.999"},
    ]

    for fragment in cases:
        runtime = _safe_runtime()
        runtime.update(fragment)

        result = validate_runtime_contract(runtime)

        assert result["valid"] is False
        assert result["blocked_reasons"]


def test_safe_references_pass_to_sanitized_context():
    result = validate_runtime_contract(_safe_runtime())

    assert result["valid"] is True
    assert result["blocked_reasons"] == []
    assert result["sanitized_runtime"] == {
        "valid": True,
        "endpoint_reference": True,
        "auth_reference": True,
        "headers_reference": True,
        "body_reference": True,
        "correlation_reference": "cor***001",
    }


def test_runtime_validation_does_not_mutate_input_and_is_deterministic():
    runtime = _safe_runtime()
    original = copy.deepcopy(runtime)

    first = validate_runtime_contract(runtime)
    second = validate_runtime_contract(runtime)

    assert runtime == original
    assert first == second
