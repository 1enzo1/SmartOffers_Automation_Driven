import copy

from core.real_execution import build_readiness_policy, evaluate_real_execution_readiness
from core.real_execution.policy import CANDIDATE_QA4_API_ID


def _ready_policy():
    return build_readiness_policy(
        runtime_flags={
            "REAL_EXECUTION_ENABLED": True,
            "REAL_EXECUTION_KILL_SWITCH": False,
        },
        allowed_api_ids=[CANDIDATE_QA4_API_ID],
        allowed_methods_by_api_id={CANDIDATE_QA4_API_ID: "POST"},
    )


def _ready_request():
    return {
        "api_id": CANDIDATE_QA4_API_ID,
        "method": "POST",
        "environment": "QA4",
        "requested_mode": "real",
        "explicit_opt_in": True,
        "timeout_seconds": 5,
        "retry_count": 0,
        "risk_assessment": {"risk_status": "future_controlled_required"},
    }


def test_blocks_by_default():
    result = evaluate_real_execution_readiness({}, build_readiness_policy())

    assert result["decision"] == "blocked"
    assert result["allowed"] is False
    assert result["ready_for_real_call"] is False
    assert "missing_explicit_opt_in" in result["blocked_reasons"]
    assert "real_execution_flag_disabled" in result["blocked_reasons"]


def test_blocks_incomplete_opt_in():
    request = _ready_request()
    request["explicit_opt_in"] = False

    result = evaluate_real_execution_readiness(request, _ready_policy())

    assert result["decision"] == "blocked"
    assert "missing_explicit_opt_in" in result["blocked_reasons"]


def test_blocks_environment_outside_qa4():
    request = _ready_request()
    request["environment"] = "DEV"

    result = evaluate_real_execution_readiness(request, _ready_policy())

    assert result["decision"] == "blocked"
    assert "environment_not_allowed" in result["blocked_reasons"]


def test_blocks_api_outside_allowlist():
    request = _ready_request()
    request["api_id"] = "post-nao-allowlisted"

    result = evaluate_real_execution_readiness(request, _ready_policy())

    assert result["decision"] == "blocked"
    assert "api_not_allowlisted" in result["blocked_reasons"]


def test_blocks_active_kill_switch():
    policy = _ready_policy()
    policy["runtime_flags"]["REAL_EXECUTION_KILL_SWITCH"] = True

    result = evaluate_real_execution_readiness(_ready_request(), policy)

    assert result["decision"] == "blocked"
    assert "kill_switch_active" in result["blocked_reasons"]


def test_blocks_risk_classifier_blocked():
    request = _ready_request()
    request["risk_assessment"] = {"risk_status": "blocked"}

    result = evaluate_real_execution_readiness(request, _ready_policy())

    assert result["decision"] == "blocked"
    assert "risk_classifier_blocked" in result["blocked_reasons"]


def test_blocks_sensitive_host_ip_token_secret_credential_and_payload():
    cases = [
        {"host": "qa4-host"},
        {"target": "999.999.999.999"},
        {"headers": {"token": "value"}},
        {"headers": {"secret": "value"}},
        {"headers": {"credential": "value"}},
        {"body": {"real_payload": True}},
    ]

    for sensitive_fragment in cases:
        request = _ready_request()
        request.update(sensitive_fragment)

        result = evaluate_real_execution_readiness(request, _ready_policy())

        assert result["decision"] == "blocked"
        assert any(reason.startswith("sensitive_") for reason in result["blocked_reasons"])


def test_accepts_only_conceptual_readiness_when_all_preconditions_pass():
    result = evaluate_real_execution_readiness(_ready_request(), _ready_policy())

    assert result["decision"] == "ready_for_manual_review"
    assert result["allowed"] is True
    assert result["blocked_reasons"] == []
    assert result["ready_for_real_call"] is False
    assert "execution blocked" in result["next_step"]


def test_sanitized_log_omits_sensitive_fields():
    request = _ready_request()
    request.update(
        {
            "host": "qa4-host",
            "payload": {"msisdn": "sample-line", "account": "sample-account"},
            "headers": {"bearer": "abc", "cookie": "session"},
            "response_body": {"raw": "body"},
        }
    )

    result = evaluate_real_execution_readiness(request, _ready_policy())

    log_text = str(result["sanitized_log"]).lower()
    forbidden = (
        "host",
        "ip",
        "token",
        "secret",
        "credential",
        "payload",
        "msisdn",
        "account",
        "bearer",
        "cookie",
        "response_body",
        "sample-line",
    )
    for term in forbidden:
        assert term not in log_text


def test_function_does_not_mutate_input_and_is_deterministic():
    request = _ready_request()
    policy = _ready_policy()
    original_request = copy.deepcopy(request)
    original_policy = copy.deepcopy(policy)

    first = evaluate_real_execution_readiness(request, policy)
    second = evaluate_real_execution_readiness(request, policy)

    assert request == original_request
    assert policy == original_policy
    assert first == second


def test_no_real_call_is_represented_by_readiness_flags():
    result = evaluate_real_execution_readiness(_ready_request(), _ready_policy())

    assert result["ready_for_real_call"] is False
    assert result["sanitized_log"]["ready_for_real_call"] is False
    assert "api real" not in result["next_step"].lower()
    assert "kafka real" not in result["next_step"].lower()
    assert "oracle real" not in result["next_step"].lower()


def test_blocks_retry_timeout_method_runtime_flag_and_fallback_attempts():
    cases = [
        ("retry_not_allowed", {"retry_count": 1}, _ready_policy()),
        ("invalid_timeout", {"timeout_seconds": 0}, _ready_policy()),
        ("method_not_allowed", {"method": "GET"}, _ready_policy()),
        (
            "real_execution_flag_disabled",
            {},
            build_readiness_policy(
                runtime_flags={"REAL_EXECUTION_ENABLED": False},
                allowed_api_ids=[CANDIDATE_QA4_API_ID],
                allowed_methods_by_api_id={CANDIDATE_QA4_API_ID: "POST"},
            ),
        ),
        ("fallback_execution_attempt", {"notes": "fallback execution if review fails"}, _ready_policy()),
    ]

    for expected_reason, request_updates, policy in cases:
        request = _ready_request()
        request.update(request_updates)

        result = evaluate_real_execution_readiness(request, policy)

        assert result["decision"] == "blocked"
        assert expected_reason in result["blocked_reasons"]
