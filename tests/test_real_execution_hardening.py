from pathlib import Path

import core.real_execution as real_execution
from core.execution.service import AdapterRunModeError, run_adapter_scenario
from core.real_execution.allowlist import build_first_qa4_allowlist
from core.real_execution.executor import execute_first_qa4_call_manual
from core.real_execution.policy import CANDIDATE_QA4_API_ID


ROOT = Path(__file__).resolve().parents[1]
REAL_EXECUTION_DIR = ROOT / "core" / "real_execution"


class DummyManualClient:
    is_real_manual_client = True

    def __init__(self, response=None):
        self.calls = []
        self.response = response or {
            "status_code": 202,
            "ok": True,
            "elapsed_ms": 7,
            "body_recorded": False,
        }

    def send(self, sanitized_request, runtime_secrets, timeout_seconds):
        self.calls.append(
            {
                "sanitized_request": dict(sanitized_request),
                "runtime_present": bool(runtime_secrets),
                "timeout_seconds": timeout_seconds,
            }
        )
        return dict(self.response)


def _request():
    return {
        "api_id": CANDIDATE_QA4_API_ID,
        "method": "POST",
        "environment": "QA4",
        "explicit_opt_in": True,
        "timeout_seconds": 5,
        "retry_count": 0,
        "source": "hardening-test",
    }


def _runtime_refs():
    return {
        "QA4_HOST_REF": "runtime-ref:endpoint-approved-for-manual-review",
        "AUTH_REF": "runtime-ref:auth-material-approved-for-manual-review",
        "SENSITIVE_HEADERS_REF": "runtime-ref:headers-approved-for-manual-review",
        "TEST_PAYLOAD_REF": "runtime-ref:body-approved-for-manual-review",
        "CORRELATION_ID": "corr-safe-777",
    }


def _runtime_secrets():
    return {
        "endpoint": "opaque-a",
        "auth": "opaque-b",
        "headers": {"x-opaque": "opaque-c"},
        "body": b"opaque-d",
        "correlation_id": "corr-safe-777",
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
        "approver_ref": "apr-safe-777",
        "ticket_ref": "chg-safe-777",
        "approved_api_id": CANDIDATE_QA4_API_ID,
        "approved_environment": "QA4",
        "approved_at_ref": "time-safe-777",
    }


def _execute(client=None, request=None, runtime_refs=None, runtime_secrets=None, policy=None, approval=None):
    return execute_first_qa4_call_manual(
        request or _request(),
        runtime_refs or _runtime_refs(),
        runtime_secrets or _runtime_secrets(),
        policy or _policy(),
        client or DummyManualClient(),
        approval or _approval(),
    )


def test_real_client_and_manual_executor_are_not_exported_from_package():
    assert not hasattr(real_execution, "RealHttpClient")
    assert not hasattr(real_execution, "execute_first_qa4_call_manual")
    assert "RealHttpClient" not in real_execution.__all__
    assert "execute_first_qa4_call_manual" not in real_execution.__all__


def test_urllib_request_only_appears_in_isolated_real_client():
    marker = "urllib" + ".request"
    matches = []
    for path in REAL_EXECUTION_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if marker in text:
            matches.append(path.name)

    assert matches == ["real_http_client.py"]


def test_forbidden_runtime_imports_are_absent_outside_real_client_exception():
    http_import_marker = "urllib" + ".request"
    forbidden = (
        "import " + "requests",
        "from " + "requests",
        "import " + "httpx",
        "from " + "httpx",
        "import " + "subprocess",
        "from " + "subprocess",
        "os." + "environ",
        "os." + "getenv",
    )
    for path in REAL_EXECUTION_DIR.glob("*.py"):
        if path.name == "real_http_client.py":
            text = path.read_text(encoding="utf-8")
            assert http_import_marker in text
        text = path.read_text(encoding="utf-8")
        for forbidden_marker in forbidden:
            assert forbidden_marker not in text


def test_adapter_run_mode_real_still_blocks():
    try:
        run_adapter_scenario({"id": "hardening-smoke"}, mode="real")
    except AdapterRunModeError as exc:
        assert "mode real bloqueado" in str(exc)
    else:
        raise AssertionError("adapter-run mode=real must remain blocked")


def test_evidence_log_and_return_do_not_include_runtime_secrets_key_or_values():
    result = _execute()
    text = f"{result['evidence']} {result['sanitized_log']} {result['client_response']}".lower()

    assert "runtime_secrets" not in result
    assert "runtime_secrets" not in str(result).lower()
    for forbidden in (
        "opaque-a",
        "opaque-b",
        "opaque-c",
        "opaque-d",
        "x-opaque",
        "headers",
        "payload",
        "token",
        "secret",
        "credential",
        "bearer",
        "cookie",
        "msisdn",
        "account",
        "documento",
        "response_body",
    ):
        assert forbidden not in text


def test_guardrail_failures_block_before_client():
    cases = []

    no_approval = _approval()
    no_approval["approved"] = False
    cases.append(({}, _runtime_refs(), _runtime_secrets(), _policy(), no_approval, "approval_missing"))

    runtime_refs = _runtime_refs()
    runtime_refs.pop("AUTH_REF")
    cases.append(({}, runtime_refs, _runtime_secrets(), _policy(), _approval(), "missing_auth_ref"))

    runtime_secrets = _runtime_secrets()
    runtime_secrets.pop("body")
    cases.append(({}, _runtime_refs(), runtime_secrets, _policy(), _approval(), "missing_runtime_body"))

    policy = _policy()
    policy["runtime_flags"]["REAL_EXECUTION_KILL_SWITCH"] = True
    cases.append(({}, _runtime_refs(), _runtime_secrets(), policy, _approval(), "kill_switch_active"))

    request = _request()
    request["retry_count"] = 1
    cases.append((request, _runtime_refs(), _runtime_secrets(), _policy(), _approval(), "retry_not_allowed"))

    for request_override, refs, secrets, policy_data, approval, expected_reason in cases:
        client = DummyManualClient()
        result = _execute(
            client=client,
            request=request_override or _request(),
            runtime_refs=refs,
            runtime_secrets=secrets,
            policy=policy_data,
            approval=approval,
        )

        assert result["decision"] == "blocked"
        assert expected_reason in result["blocked_reasons"]
        assert client.calls == []
        assert result["real_call_executed"] is False


def test_no_automatic_path_calls_real_client():
    class AutomaticClient:
        is_real_manual_client = False

        def __init__(self):
            self.calls = []

        def send(self, sanitized_request, runtime_secrets, timeout_seconds):
            self.calls.append("called")
            return {"status_code": 200, "ok": True, "elapsed_ms": 1, "body_recorded": False}

    client = AutomaticClient()
    result = _execute(client=client)

    assert result["decision"] == "blocked"
    assert "real_manual_client_required" in result["blocked_reasons"]
    assert client.calls == []
