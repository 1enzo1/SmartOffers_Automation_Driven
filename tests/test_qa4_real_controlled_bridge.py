from pathlib import Path

import app as app_module
from core.real_execution import qa4_real_controlled_bridge


EVALUATED_AT = "2026-08-25T12:00:00+00:00"
SYNTHETIC_OFFERS_SCENARIO = "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4"


def _context():
    return {
        "environment": "qa4",
        "workflow_profile": "smartoffers_qa4_full_smoke",
        "orchestration_id": "alpha-bridge-ref",
        "operational_window_ref": "qa4-window-ref",
        "window_started_at": "2026-08-25T11:55:00+00:00",
        "window_expires_at": "2026-08-25T12:05:00+00:00",
    }


class _ManualClient:
    is_real_manual_client = True

    def __init__(self, status_code):
        self.status_code = status_code
        self.calls = []

    def send(self, sanitized_request, runtime_secrets, timeout_seconds):
        self.calls.append((dict(sanitized_request), timeout_seconds))
        return {
            "status_code": self.status_code,
            "ok": 200 <= self.status_code < 300,
            "elapsed_ms": 1,
            "body_recorded": False,
        }


class _TransportMarkedManualClient(_ManualClient):
    is_real_transport_client = True


def _offers_runtime_environment():
    return {
        "SMARTOFFERS_QA4_API_URL": "https://qa4.example.invalid/smartoffers",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN": "safe-acm-custom-dsn",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER": "safe-acm-custom-user",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD": "safe-acm-custom-password",
        "SMARTOFFERS_QA4_ACM_DB_DSN": "safe-acm-dsn",
        "SMARTOFFERS_QA4_ACM_DB_USER": "safe-acm-user",
        "SMARTOFFERS_QA4_ACM_DB_PASSWORD": "safe-acm-password",
        "SMARTOFFERS_QA4_BDA_DB_DSN": "safe-bda-dsn",
        "SMARTOFFERS_QA4_BDA_DB_USER": "safe-bda-user",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD": "safe-bda-password",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "safe-oracle-client-dir",
        "SMARTOFFERS_QA4_TEST_MSISDN": "5511999999999",
        "SMARTOFFERS_QA4_TEST_OFFER": "QA4_SYNTHETIC_OFFER",
    }


def _executor_inputs():
    api_id = "post-vivo-next-habilitacao-de-cliente-ade0841563"
    return {
        "runtime_refs": {
            "QA4_HOST_REF": "runtime-ref:qa4-host",
            "AUTH_REF": "runtime-ref:qa4-auth",
            "SENSITIVE_HEADERS_REF": "runtime-ref:qa4-headers",
            "TEST_PAYLOAD_REF": "runtime-ref:qa4-body",
            "CORRELATION_ID": "corr-safe-001",
        },
        "runtime_secrets": {
            "endpoint": "in-memory-endpoint",
            "auth": "in-memory-auth",
            "headers": {"content-type": "application/json"},
            "body": b"unused",
            "correlation_id": "corr-safe-001",
            "timeout_seconds": 5,
        },
        "policy": {
            "runtime_flags": {"REAL_EXECUTION_ENABLED": True, "REAL_EXECUTION_KILL_SWITCH": False},
            "first_qa4_allowlist": {
                "allowed_api_ids": [api_id],
                "items": {api_id: {"api_id": api_id, "method": "POST", "environment": "QA4", "timeout_seconds": 5, "retry_count": 0, "status": "manual_offers_customer"}},
            },
        },
        "approval": {"approved": True, "risk_acceptance": True, "approver_ref": "apr-safe-001", "ticket_ref": "chg-safe-001", "approved_api_id": api_id, "approved_environment": "QA4", "approved_at_ref": "time-safe-001"},
    }


def _one_run_opt_in():
    return {
        "approved": True,
        "operation": "ONE_QA4_OFFERS_CUSTOMER_CREATE_RUN",
        "environment": "QA4",
        "max_attempts": 1,
        "retry_count": 0,
        "fallback": False,
    }


def test_real_controlled_bridge_runs_standard_facade_then_blocks_before_fake_send(monkeypatch):
    facade_calls = []

    def facade(context, *, mode, evaluated_at):
        facade_calls.append((context, mode, evaluated_at))
        return {"result": "PASS", "full": {"status": "FULL_SMOKE_OK"}}

    monkeypatch.setattr(qa4_real_controlled_bridge, "run_standard_qa4_application_mock", facade)

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(), mode="real-controlled", evaluated_at=EVALUATED_AT
    )

    assert facade_calls == [(_context(), "mock", EVALUATED_AT)]
    assert result["result"] == "BLOCKED"
    assert result["standard_report"]["result"] == "PASS"
    assert result["real_call_executed"] is False
    assert result["fake_client_send_calls"] == 0
    assert result["blockers"] == [
        "REAL_QA4_OPERATION_NOT_CONFIRMED",
        "QA4_TEST_DATA_REQUIRED",
        "QA4_CREDENTIAL_OR_CONFIG_REQUIRED",
    ]
    assert "secret" not in str(result).lower()
    assert "payload" not in str(result).lower()


def test_real_controlled_bridge_uses_local_offers_adapter_before_zero_transport(monkeypatch):
    adapter_calls = []

    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "run_standard_qa4_application_mock",
        lambda context, *, mode, evaluated_at: {"result": "PASS"},
    )

    def adapter(context, **kwargs):
        adapter_calls.append(context)
        return {
            "decision": "READY",
            "operation": "CREATE_OFFERS_CUSTOMER",
            "attempt_policy": {"max_attempts": 1, "retry_count": 0, "fallback": False},
            "transport_permitted": False,
            "send_attempted": False,
        }

    monkeypatch.setattr(qa4_real_controlled_bridge, "execute_qa4_offers_customer_create", adapter)

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(), mode="real-controlled", evaluated_at=EVALUATED_AT
    )

    assert adapter_calls == [_context() | {"event_time": EVALUATED_AT}]
    assert result["result"] == "BLOCKED"
    assert result["offers_adapter"]["operation"] == "CREATE_OFFERS_CUSTOMER"
    assert result["offers_adapter"]["attempt_policy"]["max_attempts"] == 1
    assert result["offers_adapter"]["attempt_policy"]["retry_count"] == 0
    assert result["offers_adapter"]["attempt_policy"]["fallback"] is False
    assert result["real_call_executed"] is False
    assert result["fake_client_send_calls"] == 0


def test_selected_synthetic_scenario_routes_standard_pass_to_one_synthetic_adapter(monkeypatch):
    adapter_calls = []
    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "run_standard_qa4_application_mock",
        lambda context, *, mode, evaluated_at: {"result": "PASS"},
    )

    def synthetic_adapter(context, **kwargs):
        adapter_calls.append((context, kwargs))
        return {
            "result": "PASS",
            "operation": "CREATE_OFFERS_CUSTOMER",
            "evidence": {"synthetic": True},
            "send_attempted": False,
            "real_call_executed": False,
        }

    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "execute_one_synthetic_qa4_offers_customer_create",
        synthetic_adapter,
    )

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(),
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
    )

    assert result["result"] == "PASS"
    assert adapter_calls == [
        (
            _context(),
            {
                "environ": None,
                "runtime_refs": None,
                "runtime_secrets": None,
                "policy": None,
                "client": None,
                "approval": None,
                "owner_opt_in": None,
                "ledger": None,
            },
        )
    ]
    assert result["evidence"] == {"synthetic": True}
    assert result["real_call_executed"] is False
    assert result["executor_send_attempted"] is False


def test_real_controlled_bridge_passes_evaluated_timestamp_to_offers_adapter():
    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(), mode="real-controlled", evaluated_at=EVALUATED_AT
    )

    assert "INVALID_EVENT_TIME" not in result["offers_adapter"]["blockers"]


def test_real_controlled_bridge_routes_exact_offers_request_to_injected_executor_client(monkeypatch):
    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "run_standard_qa4_application_mock",
        lambda context, *, mode, evaluated_at: {"result": "PASS"},
    )
    client = _ManualClient(202)

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(),
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        environ=_offers_runtime_environment(),
        client=client,
        **_executor_inputs(),
    )

    assert result["result"] == "PASS"
    assert result["guard_decision"] == "manual_call_completed"
    assert result["evidence"]["status_code"] == 202
    assert result["real_call_executed"] is True
    assert len(client.calls) == 1
    assert client.calls[0][0]["api_id"] == "post-vivo-next-habilitacao-de-cliente-ade0841563"
    assert client.calls[0][1] == 5


def test_real_controlled_bridge_surfaces_exact_offers_failure_without_retry(monkeypatch):
    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "run_standard_qa4_application_mock",
        lambda context, *, mode, evaluated_at: {"result": "PASS"},
    )
    client = _ManualClient(503)

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(),
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        environ=_offers_runtime_environment(),
        client=client,
        **_executor_inputs(),
    )

    assert result["result"] == "FAIL"
    assert result["guard_decision"] == "manual_call_completed"
    assert result["evidence"]["status_code"] == 503
    assert len(client.calls) == 1
    assert result["offers_adapter"]["attempt_policy"] == {"max_attempts": 1, "retry_count": 0, "fallback": False}


def test_real_controlled_bridge_forwards_bounded_one_run_opt_in_to_transport_gate(monkeypatch):
    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "run_standard_qa4_application_mock",
        lambda context, *, mode, evaluated_at: {"result": "PASS"},
    )
    client = _TransportMarkedManualClient(202)

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(),
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        environ=_offers_runtime_environment(),
        client=client,
        owner_opt_in=_one_run_opt_in(),
        **_executor_inputs(),
    )

    assert result["result"] == "PASS"
    assert len(client.calls) == 1


def test_real_controlled_bridge_has_no_transport_imports():
    source = Path("core/real_execution/qa4_real_controlled_bridge.py").read_text()

    for forbidden in (
        "import requests",
        "from requests",
        "import urllib",
        "import socket",
        "RealHttpClient",
    ):
        assert forbidden not in source


def test_real_controlled_api_entry_returns_sanitized_blocked_bridge(app_client_factory, monkeypatch):
    client, _ = app_client_factory("qa4-real-controlled")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_real_controlled",
        lambda context, *, mode, evaluated_at, scenario_id: {
            "result": "BLOCKED",
            "standard_report": {"result": "PASS"},
            "blockers": ["REAL_QA4_OPERATION_NOT_CONFIRMED"],
            "real_call_executed": False,
            "fake_client_send_calls": 0,
        },
    )

    response = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "QA4",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "evaluated_at": EVALUATED_AT,
            "secret": "must-not-appear",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["result"] == "BLOCKED"
    assert "must-not-appear" not in response.get_data(as_text=True)


def test_selected_synthetic_scenario_api_routes_only_qa4_to_real_controlled_bridge(
    app_client_factory, monkeypatch
):
    client, _ = app_client_factory("qa4-selected-scenario")
    bridge_calls = []

    def bridge(context, *, mode, evaluated_at, scenario_id):
        bridge_calls.append((context, mode, evaluated_at, scenario_id))
        return {
            "result": "BLOCKED",
            "blockers": ["AUTH_CONTRACT_UNREADY"],
            "real_call_executed": False,
            "executor_send_attempted": False,
        }

    monkeypatch.setattr(app_module, "run_standard_qa4_real_controlled", bridge)
    response = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "QA4",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "evaluated_at": EVALUATED_AT,
            "secret": "must-not-appear",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["result"] == "BLOCKED"
    assert bridge_calls == [
        (
            _context() | {"environment": "qa4"},
            "real-controlled",
            EVALUATED_AT,
            SYNTHETIC_OFFERS_SCENARIO,
        )
    ]
    assert "must-not-appear" not in response.get_data(as_text=True)


def test_selected_synthetic_scenario_api_blocks_wrong_environment_or_scenario_before_bridge(
    app_client_factory, monkeypatch
):
    client, _ = app_client_factory("qa4-selected-scenario-blocked")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_real_controlled",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("bridge must not run")),
    )

    production = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "PRODUCTION",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "evaluated_at": EVALUATED_AT,
        },
    )
    wrong_scenario = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "QA4",
            "mode": "real-controlled",
            "scenario_id": "UNSUPPORTED_SCENARIO",
            "evaluated_at": EVALUATED_AT,
        },
    )

    assert production.get_json() == {"result": "BLOCKED", "reason": "ENVIRONMENT_NOT_ALLOWED"}
    assert wrong_scenario.get_json() == {"result": "BLOCKED", "reason": "SCENARIO_NOT_ALLOWED"}
