import copy

from core.execution.service import AdapterRunModeError, run_adapter_scenario
from core.real_execution import (
    FakeHttpClient,
    build_first_qa4_allowlist,
    build_readiness_policy,
    prepare_first_qa4_call,
)
from core.real_execution.policy import CANDIDATE_QA4_API_ID


def _safe_runtime():
    return {
        "QA4_HOST_REF": "runtime-ref:endpoint-approved-for-manual-review",
        "AUTH_REF": "runtime-ref:auth-material-approved-for-manual-review",
        "SENSITIVE_HEADERS_REF": "runtime-ref:headers-approved-for-manual-review",
        "TEST_PAYLOAD_REF": "runtime-ref:body-approved-for-manual-review",
        "CORRELATION_ID": "corr-safe-001",
    }


def _request():
    return {
        "api_id": CANDIDATE_QA4_API_ID,
        "method": "POST",
        "environment": "QA4",
        "explicit_opt_in": True,
        "timeout_seconds": 5,
        "retry_count": 0,
        "source": "test",
    }


def _policy():
    return {
        "runtime_flags": {
            "REAL_EXECUTION_ENABLED": True,
            "REAL_EXECUTION_KILL_SWITCH": False,
        },
        "first_qa4_allowlist": build_first_qa4_allowlist(),
    }


def test_api_outside_allowlist_blocks_before_client():
    request = _request()
    request["api_id"] = "post-not-allowlisted"
    client = FakeHttpClient()

    result = prepare_first_qa4_call(request, _safe_runtime(), _policy(), client)

    assert result["decision"] == "blocked"
    assert "api_not_in_first_qa4_allowlist" in result["blocked_reasons"]
    assert client.sent_requests == []
    assert result["real_call_executed"] is False


def test_method_mismatch_blocks_before_client():
    request = _request()
    request["method"] = "GET"
    client = FakeHttpClient()

    result = prepare_first_qa4_call(request, _safe_runtime(), _policy(), client)

    assert result["decision"] == "blocked"
    assert "method_not_allowlisted" in result["blocked_reasons"]
    assert client.sent_requests == []


def test_kill_switch_blocks_before_client():
    policy = _policy()
    policy["runtime_flags"]["REAL_EXECUTION_KILL_SWITCH"] = True
    client = FakeHttpClient()

    result = prepare_first_qa4_call(_request(), _safe_runtime(), policy, client)

    assert result["decision"] == "blocked"
    assert "kill_switch_active" in result["blocked_reasons"]
    assert client.sent_requests == []


def test_readiness_blocked_prevents_client():
    policy = _policy()
    policy["runtime_flags"]["REAL_EXECUTION_ENABLED"] = False
    client = FakeHttpClient()

    result = prepare_first_qa4_call(_request(), _safe_runtime(), policy, client)

    assert result["decision"] == "blocked"
    assert "readiness_blocked" in result["blocked_reasons"]
    assert "real_execution_flag_disabled" in result["blocked_reasons"]
    assert client.sent_requests == []


def test_risk_classifier_blocked_prevents_client():
    request = _request()
    request["risk_input"] = {"mode": "real"}
    client = FakeHttpClient()

    result = prepare_first_qa4_call(request, _safe_runtime(), _policy(), client)

    assert result["decision"] == "blocked"
    assert "risk_classifier_blocked" in result["blocked_reasons"]
    assert client.sent_requests == []


def test_fake_client_receives_only_sanitized_request():
    client = FakeHttpClient()

    result = prepare_first_qa4_call(_request(), _safe_runtime(), _policy(), client)

    assert result["decision"] == "prepared_with_fake_client"
    assert result["allowed"] is True
    assert result["real_call_executed"] is False
    assert len(client.sent_requests) == 1
    sent = client.sent_requests[0]
    assert sent == result["sanitized_request"]
    assert sent["api_id"] == CANDIDATE_QA4_API_ID
    assert sent["runtime_ready"] is True
    assert sent["endpoint_reference"] is True
    assert sent["auth_reference"] is True
    assert sent["headers_reference"] is True
    assert sent["body_reference"] is True


def test_logs_do_not_expose_sensitive_terms_or_values():
    result = prepare_first_qa4_call(_request(), _safe_runtime(), _policy(), FakeHttpClient())

    log_text = str(result["sanitized_log"]).lower()
    request_text = str(result["sanitized_request"]).lower()
    forbidden = (
        "host",
        "ip",
        "token",
        "secret",
        "credential",
        "payload",
        "msisdn",
        "account",
        "documento",
        "document",
        "bearer",
        "cookie",
        "response_body",
        "runtime-ref",
    )
    for term in forbidden:
        assert term not in log_text
        assert term not in request_text


def test_non_fake_client_is_rejected_without_calling_send():
    class NonFakeClient:
        is_fake_client = False

        def __init__(self):
            self.called = False

        def send(self, sanitized_request):
            self.called = True
            return {"simulated": False}

    client = NonFakeClient()

    result = prepare_first_qa4_call(_request(), _safe_runtime(), _policy(), client)

    assert result["decision"] == "blocked"
    assert "fake_client_required" in result["blocked_reasons"]
    assert client.called is False


def test_no_network_is_represented_by_fake_response():
    result = prepare_first_qa4_call(_request(), _safe_runtime(), _policy(), FakeHttpClient())

    assert result["client_response"] == {
        "client": "fake",
        "status_code": 202,
        "simulated": True,
    }
    assert result["real_call_executed"] is False


def test_request_runtime_and_policy_are_not_mutated_and_result_is_deterministic():
    request = _request()
    runtime = _safe_runtime()
    policy = _policy()
    original_request = copy.deepcopy(request)
    original_runtime = copy.deepcopy(runtime)
    original_policy = copy.deepcopy(policy)

    first = prepare_first_qa4_call(request, runtime, policy, FakeHttpClient())
    second = prepare_first_qa4_call(request, runtime, policy, FakeHttpClient())

    assert request == original_request
    assert runtime == original_runtime
    assert policy == original_policy
    assert first == second


def test_adapter_run_mode_real_remains_blocked():
    try:
        run_adapter_scenario({"id": "runtime-contract-smoke"}, mode="real")
    except AdapterRunModeError as exc:
        assert "mode real bloqueado" in str(exc)
    else:
        raise AssertionError("mode=real should remain blocked in adapter-run")
