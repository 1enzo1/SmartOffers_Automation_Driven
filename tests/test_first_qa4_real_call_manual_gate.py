import copy

from core.execution.service import AdapterRunModeError, run_adapter_scenario
from core.real_execution.allowlist import build_first_qa4_allowlist
from core.real_execution.executor import execute_first_qa4_call_manual
from core.real_execution.policy import CANDIDATE_QA4_API_ID


_DEFAULT = object()


class DummyManualClient:
    is_real_manual_client = True

    def __init__(self, response=None, error=None):
        self.calls = []
        self.response = response or {
            "status_code": 202,
            "ok": True,
            "elapsed_ms": 12,
            "body_recorded": False,
        }
        self.error = error

    def send(self, sanitized_request, runtime_secrets, timeout_seconds):
        self.calls.append(
            {
                "sanitized_request": dict(sanitized_request),
                "timeout_seconds": timeout_seconds,
                "runtime_seen": bool(runtime_secrets),
            }
        )
        if self.error:
            raise self.error
        return dict(self.response)


class NonManualClient:
    is_real_manual_client = False

    def __init__(self):
        self.calls = []

    def send(self, sanitized_request, runtime_secrets, timeout_seconds):
        self.calls.append({"called": True})
        return {}


def _request():
    return {
        "api_id": CANDIDATE_QA4_API_ID,
        "method": "POST",
        "environment": "QA4",
        "explicit_opt_in": True,
        "timeout_seconds": 5,
        "retry_count": 0,
        "source": "manual-test",
    }


def _runtime_refs():
    return {
        "QA4_HOST_REF": "runtime-ref:endpoint-approved-for-manual-review",
        "AUTH_REF": "runtime-ref:auth-material-approved-for-manual-review",
        "SENSITIVE_HEADERS_REF": "runtime-ref:headers-approved-for-manual-review",
        "TEST_PAYLOAD_REF": "runtime-ref:body-approved-for-manual-review",
        "CORRELATION_ID": "corr-safe-001",
    }


def _runtime_secrets():
    return {
        "endpoint": "redacted-endpoint-in-memory",
        "auth": "redacted-auth-in-memory",
        "headers": {"x-redacted": "redacted"},
        "body": b"redacted-body-in-memory",
        "correlation_id": "corr-safe-001",
        "timeout_seconds": 5,
    }


def _policy():
    return {
        "runtime_flags": {
            "REAL_EXECUTION_ENABLED": True,
            "REAL_EXECUTION_KILL_SWITCH": False,
        },
        "first_qa4_allowlist": build_first_qa4_allowlist(),
    }


def _approval():
    return {
        "approved": True,
        "risk_acceptance": True,
        "approver_ref": "apr-safe-001",
        "ticket_ref": "chg-safe-001",
        "approved_api_id": CANDIDATE_QA4_API_ID,
        "approved_environment": "QA4",
        "approved_at_ref": "time-safe-001",
    }


def _execute(
    request=None,
    runtime_refs=None,
    runtime_secrets=None,
    policy=None,
    client=None,
    approval=_DEFAULT,
):
    return execute_first_qa4_call_manual(
        request or _request(),
        runtime_refs or _runtime_refs(),
        runtime_secrets or _runtime_secrets(),
        policy or _policy(),
        client or DummyManualClient(),
        _approval() if approval is _DEFAULT else approval,
    )


def test_missing_approval_blocks_before_client():
    client = DummyManualClient()

    result = _execute(client=client, approval=None)

    assert result["decision"] == "blocked"
    assert "approval_missing" in result["blocked_reasons"]
    assert client.calls == []
    assert result["real_call_executed"] is False


def test_incomplete_approval_blocks_before_client():
    approval = _approval()
    approval.pop("ticket_ref")
    client = DummyManualClient()

    result = _execute(client=client, approval=approval)

    assert result["decision"] == "blocked"
    assert "missing_ticket_ref" in result["blocked_reasons"]
    assert client.calls == []


def test_kill_switch_blocks_before_client():
    policy = _policy()
    policy["runtime_flags"]["REAL_EXECUTION_KILL_SWITCH"] = True
    client = DummyManualClient()

    result = _execute(policy=policy, client=client)

    assert result["decision"] == "blocked"
    assert "kill_switch_active" in result["blocked_reasons"]
    assert client.calls == []


def test_readiness_blocked_prevents_client():
    policy = _policy()
    policy["runtime_flags"]["REAL_EXECUTION_ENABLED"] = False
    client = DummyManualClient()

    result = _execute(policy=policy, client=client)

    assert result["decision"] == "blocked"
    assert "readiness_not_ready_for_manual_review" in result["blocked_reasons"]
    assert "real_execution_flag_disabled" in result["blocked_reasons"]
    assert client.calls == []


def test_risk_classifier_blocked_prevents_client():
    request = _request()
    request["risk_status"] = "blocked"
    client = DummyManualClient()

    result = _execute(request=request, client=client)

    assert result["decision"] == "blocked"
    assert "risk_classifier_blocked" in result["blocked_reasons"]
    assert client.calls == []


def test_timeout_mismatch_blocks_before_client():
    request = _request()
    request["timeout_seconds"] = 4
    client = DummyManualClient()

    result = _execute(request=request, client=client)

    assert result["decision"] == "blocked"
    assert "timeout_not_allowlisted" in result["blocked_reasons"]
    assert client.calls == []


def test_retry_nonzero_blocks_before_client():
    request = _request()
    request["retry_count"] = 1
    client = DummyManualClient()

    result = _execute(request=request, client=client)

    assert result["decision"] == "blocked"
    assert "retry_not_allowed" in result["blocked_reasons"]
    assert client.calls == []


def test_runtime_secrets_incomplete_blocks_before_client():
    runtime_secrets = _runtime_secrets()
    runtime_secrets.pop("body")
    client = DummyManualClient()

    result = _execute(runtime_secrets=runtime_secrets, client=client)

    assert result["decision"] == "blocked"
    assert "missing_runtime_body" in result["blocked_reasons"]
    assert client.calls == []


def test_runtime_refs_incomplete_blocks_before_client():
    runtime_refs = _runtime_refs()
    runtime_refs.pop("AUTH_REF")
    client = DummyManualClient()

    result = _execute(runtime_refs=runtime_refs, client=client)

    assert result["decision"] == "blocked"
    assert "missing_auth_ref" in result["blocked_reasons"]
    assert client.calls == []


def test_non_manual_client_blocks_before_send():
    client = NonManualClient()

    result = _execute(client=client)

    assert result["decision"] == "blocked"
    assert "real_manual_client_required" in result["blocked_reasons"]
    assert client.calls == []


def test_dummy_manual_client_called_only_with_valid_approval_and_returns_executed():
    client = DummyManualClient()

    result = _execute(client=client)

    assert result["decision"] == "manual_call_completed"
    assert result["allowed"] is True
    assert result["real_call_executed"] is True
    assert len(client.calls) == 1
    assert client.calls[0]["timeout_seconds"] == 5
    assert result["evidence"]["status_code"] == 202
    assert result["evidence"]["body_recorded"] is False


def test_error_before_send_keeps_real_call_executed_false():
    client = DummyManualClient()
    request = _request()
    request["api_id"] = "not-allowlisted"

    result = _execute(request=request, client=client)

    assert result["decision"] == "blocked"
    assert result["real_call_executed"] is False
    assert client.calls == []


def test_error_after_send_does_not_leak_raw_data():
    client = DummyManualClient(error=RuntimeError("raw response included forbidden data"))

    result = _execute(client=client)

    assert len(client.calls) == 1
    assert result["decision"] == "client_error_after_send"
    assert result["real_call_executed"] is False
    assert result["evidence"]["error"] == "RuntimeError"
    assert "raw response" not in str(result).lower()
    assert "forbidden data" not in str(result).lower()


def test_evidence_and_logs_do_not_contain_sensitive_terms():
    result = _execute()
    text = f"{result['evidence']} {result['sanitized_log']}".lower()
    forbidden = (
        "host",
        "ip",
        "token",
        "secret",
        "credential",
        "bearer",
        "cookie",
        "headers",
        "payload",
        "msisdn",
        "account",
        "documento",
        "response_body",
        "redacted",
    )

    for term in forbidden:
        assert term not in text


def test_inputs_are_not_mutated():
    request = _request()
    runtime_refs = _runtime_refs()
    runtime_secrets = _runtime_secrets()
    policy = _policy()
    approval = _approval()
    originals = [
        copy.deepcopy(request),
        copy.deepcopy(runtime_refs),
        copy.deepcopy(runtime_secrets),
        copy.deepcopy(policy),
        copy.deepcopy(approval),
    ]

    _execute(
        request=request,
        runtime_refs=runtime_refs,
        runtime_secrets=runtime_secrets,
        policy=policy,
        approval=approval,
    )

    assert [request, runtime_refs, runtime_secrets, policy, approval] == originals


def test_adapter_run_mode_real_remains_blocked():
    try:
        run_adapter_scenario({"id": "manual-real-gate-smoke"}, mode="real")
    except AdapterRunModeError as exc:
        assert "mode real bloqueado" in str(exc)
    else:
        raise AssertionError("mode=real should remain blocked in adapter-run")
