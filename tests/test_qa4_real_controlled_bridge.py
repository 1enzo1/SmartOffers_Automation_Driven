import json
from datetime import datetime
from pathlib import Path

import pytest

import app as app_module
from core.real_execution import qa4_real_controlled_bridge
from core.real_execution.qa4_offers_customer_adapter import OneRunAttemptLedger


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
            "runtime_flags": {"REAL_EXECUTION_ENABLED": True, "REAL_EXECUTION_KILL_SWITCH": False, "REAL_TRANSPORT_ALLOWED": True, "PRODUCTION": False, "GLOBAL_NO_AUTH_ENABLED": False},
            "first_qa4_allowlist": {
                "allowed_api_ids": [api_id],
                "items": {api_id: {"api_id": api_id, "method": "POST", "environment": "QA4", "timeout_seconds": 5, "retry_count": 0, "status": "manual_offers_customer", "operation": "CREATE_OFFERS_CUSTOMER", "scenario_id": SYNTHETIC_OFFERS_SCENARIO, "auth_required": False}},
            },
            "operation_scoped_no_auth": {"authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN", "operation": "CREATE_OFFERS_CUSTOMER", "scenario_id": SYNTHETIC_OFFERS_SCENARIO, "environment": "QA4", "auth_required": False},
            "destination_attestation": {"source": "local_runtime_config", "environment": "QA4", "allowlist_match": True, "status": "MATCH"},
        },
        "approval": {"approved": True, "risk_acceptance": True, "approver_ref": "apr-safe-001", "ticket_ref": "chg-safe-001", "approved_api_id": api_id, "approved_environment": "QA4", "approved_at_ref": "time-safe-001"},
    }


def _one_run_opt_in():
    return {
        "approved": True,
        "operation": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "environment": "QA4",
        "mode": "real-controlled",
        "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
        "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
        "max_attempts": 1,
        "retry_count": 0,
        "fallback": False,
        "production": False,
    }


def _exact_provider_context():
    return _context() | {
        "mode": "real-controlled",
        "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
        "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
    }


def _exact_control_document():
    api_id = "post-vivo-next-habilitacao-de-cliente-ade0841563"
    return {
        "owner_opt_in": _one_run_opt_in(),
        "approval": {"approved": True, "risk_acceptance": True, "approver_ref": "local-controlled-ref", "ticket_ref": "local-controlled-ref", "approved_api_id": api_id, "approved_environment": "QA4", "approved_at_ref": "local-controlled-ref"},
        "runtime_refs": {"QA4_HOST_REF": "runtime-ref:qa4-host", "SENSITIVE_HEADERS_REF": "runtime-ref:qa4-headers", "TEST_PAYLOAD_REF": "runtime-ref:qa4-body", "CORRELATION_ID": "runtime-ref:qa4-correlation"},
        "policy": {
            "runtime_flags": {"REAL_EXECUTION_ENABLED": True, "REAL_EXECUTION_KILL_SWITCH": False, "REAL_TRANSPORT_ALLOWED": True, "PRODUCTION": False, "GLOBAL_NO_AUTH_ENABLED": False},
            "operation_scoped_no_auth": {"authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN", "operation": "CREATE_OFFERS_CUSTOMER", "scenario_id": SYNTHETIC_OFFERS_SCENARIO, "environment": "QA4", "auth_required": False},
            "destination_attestation": {"source": "local_runtime_config", "environment": "QA4", "allowlist_match": True, "status": "MATCH"},
            "first_qa4_allowlist": {"allowed_api_ids": [api_id], "items": {api_id: {"api_id": api_id, "method": "POST", "environment": "QA4", "timeout_seconds": 5, "retry_count": 0, "status": "manual_offers_customer", "operation": "CREATE_OFFERS_CUSTOMER", "scenario_id": SYNTHETIC_OFFERS_SCENARIO, "auth_required": False}}},
        },
    }


def test_real_controlled_bridge_runs_standard_facade_then_blocks_before_fake_send(monkeypatch):
    facade_calls = []
    for name in (
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
        "SMARTOFFERS_QA4_ACM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_DB_USER",
        "SMARTOFFERS_QA4_ACM_DB_PASSWORD",
        "SMARTOFFERS_QA4_BDA_DB_DSN",
        "SMARTOFFERS_QA4_BDA_DB_USER",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
        "SMARTOFFERS_QA4_TEST_MSISDN",
        "SMARTOFFERS_QA4_TEST_OFFER",
    ):
        monkeypatch.delenv(name, raising=False)

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


def test_direct_bridge_blocks_unsupported_selected_scenario_before_runner_or_adapter(monkeypatch):
    for collaborator in (
        "run_standard_qa4_application_mock",
        "execute_one_synthetic_qa4_offers_customer_create",
        "execute_qa4_offers_customer_create",
    ):
        monkeypatch.setattr(
            qa4_real_controlled_bridge,
            collaborator,
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("unsupported scenario must not invoke collaborator")
            ),
        )

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(),
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        scenario_id="UNSUPPORTED_SCENARIO",
    )

    assert result["result"] == "BLOCKED"
    assert result["blockers"] == ["SCENARIO_NOT_ALLOWED"]
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
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
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
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
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
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
        environ=_offers_runtime_environment(),
        client=client,
        owner_opt_in=_one_run_opt_in(),
        ledger=OneRunAttemptLedger(),
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


def test_real_controlled_api_blocks_before_confirmation_without_real_collaborators(
    app_client_factory, monkeypatch
):
    client, _ = app_client_factory("qa4-real-controlled")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_real_controlled",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("bridge must not run before application confirmation")
        ),
        raising=False,
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

    assert response.status_code == 400
    assert response.get_json() == {"result": "BLOCKED", "reason": "APPLICATION_CONFIRMATION_REQUIRED"}
    assert "must-not-appear" not in response.get_data(as_text=True)


def test_selected_synthetic_scenario_api_binds_bridge_lazily_after_confirmation(
    app_client_factory, monkeypatch
):
    client, _ = app_client_factory("qa4-selected-scenario")
    bridge_calls = []

    def bridge(context, *, mode, evaluated_at, scenario_id, runtime_provider, **kwargs):
        bridge_calls.append((context, mode, evaluated_at, scenario_id, runtime_provider, kwargs))
        return {
            "result": "BLOCKED",
            "blockers": ["QA4_CREDENTIAL_OR_CONFIG_REQUIRED"],
            "real_call_executed": False,
            "executor_send_attempted": False,
        }

    monkeypatch.setattr(app_module, "run_atomic_qa4_bda_offer_discovery_and_offers_create", bridge)
    monkeypatch.setattr(app_module, "_atomic_static_preflight_ready", lambda *args: True)
    monkeypatch.setattr(app_module, "_trusted_local_now", lambda: datetime.fromisoformat("2026-08-25T12:00:00+00:00"))
    monkeypatch.setattr(app_module, "_governed_bda_driver", lambda: object())
    response = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "QA4",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
            "evaluated_at": EVALUATED_AT,
            "secret": "must-not-appear",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["result"] == "BLOCKED"
    assert bridge_calls[0][:4] == (
        _context()
        | {
            "environment": "qa4",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
        },
        "real-controlled",
        EVALUATED_AT,
        SYNTHETIC_OFFERS_SCENARIO,
    )
    assert callable(bridge_calls[0][4])
    assert callable(bridge_calls[0][5]["bda_driver_factory"])
    assert "must-not-appear" not in response.get_data(as_text=True)


def test_run_02_requires_its_exact_owner_authorization_before_bridge(app_client_factory, monkeypatch):
    client, _ = app_client_factory("qa4-run-02-authorization")
    monkeypatch.setattr(app_module, "_trusted_local_now", lambda: datetime.fromisoformat("2026-08-25T12:00:00+00:00"))
    payload = {
        **_context(),
        "environment": "QA4",
        "mode": "real-controlled",
        "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
        "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
        "evaluated_at": EVALUATED_AT,
        "run_id": "ALPHA_REAL_RUN_02",
    }

    denied = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={**payload, "owner_authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN"},
    )
    allowed_shape = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={**payload, "owner_authorization": "ONE_QA4_REPEATABILITY_SMOKE_RUN_02", "window_started_at": "2026-08-25T11:00:00+00:00", "window_expires_at": "2026-08-25T13:00:00+00:00"},
    )

    assert denied.status_code == 400
    assert denied.get_json() == {"result": "BLOCKED", "reason": "OWNER_AUTHORIZATION_REQUIRED"}
    assert allowed_shape.status_code in {200, 400}
    assert allowed_shape.get_json().get("reason") != "OWNER_AUTHORIZATION_REQUIRED"


def test_run_02_binds_exact_authorization_to_governed_atomic_boundary(app_client_factory, monkeypatch):
    client, _ = app_client_factory("qa4-run-02-boundary")
    calls = []
    monkeypatch.setattr(app_module, "_atomic_static_preflight_ready", lambda *args: True)
    monkeypatch.setattr(app_module, "_trusted_local_now", lambda: datetime.fromisoformat("2026-08-25T12:00:00+00:00"))
    monkeypatch.setattr(
        app_module,
        "run_atomic_qa4_bda_offer_discovery_and_offers_create",
        lambda *args, **kwargs: calls.append(kwargs) or {"result": "BLOCKED", "executor_send_attempted": False},
    )

    response = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "QA4",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
            "evaluated_at": EVALUATED_AT,
            "run_id": "ALPHA_REAL_RUN_02",
            "owner_authorization": "ONE_QA4_REPEATABILITY_SMOKE_RUN_02",
            "window_started_at": "2026-08-25T11:00:00+00:00",
            "window_expires_at": "2026-08-25T13:00:00+00:00",
        },
    )

    assert response.status_code == 200
    assert calls[0]["bda_authorization"]["owner_authorization"] == "ONE_QA4_REPEATABILITY_SMOKE_RUN_02"


def test_selected_synthetic_scenario_api_blocks_wrong_environment_or_scenario_before_bridge(
    app_client_factory, monkeypatch
):
    client, _ = app_client_factory("qa4-selected-scenario-blocked")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_real_controlled",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("bridge must not run")),
        raising=False,
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


def test_real_controlled_bridge_defers_runtime_discovery_and_client_until_standard_passes(
    monkeypatch,
):
    provider_calls = []

    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "run_standard_qa4_application_mock",
        lambda context, *, mode, evaluated_at: {"result": "BLOCKED"},
    )

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(),
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
        runtime_provider=lambda *_: provider_calls.append("called") or {},
    )

    assert result["result"] == "BLOCKED"
    assert provider_calls == []  # BDA_DISCOVERY_NOT_CALLED; REAL_HTTP_CLIENT_NOT_CREATED
    assert result["executor_send_attempted"] is False  # TRANSPORT_NOT_ATTEMPTED


def test_owner_provider_runs_offline_preflight_before_discovery_or_real_client(
    monkeypatch,
):
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery
    import core.real_execution.qa4_offers_customer_adapter as offers_adapter
    import core.real_execution.real_http_client as real_http_client

    events = []
    monkeypatch.setenv(
        "SMARTOFFERS_ALPHA_QA4_CONTROLLED_CONTRACT", json.dumps(_exact_control_document())
    )
    real_preflight = offers_adapter.prepare_one_synthetic_qa4_offers_customer_create

    def tracked_real_preflight(*args, **kwargs):
        events.append("OFFLINE_PREFLIGHT")
        return real_preflight(*args, **kwargs)

    monkeypatch.setattr(
        offers_adapter,
        "prepare_one_synthetic_qa4_offers_customer_create",
        tracked_real_preflight,
    )
    for name in (
        "SMARTOFFERS_QA4_API_URL",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
        "SMARTOFFERS_QA4_ACM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_DB_USER",
        "SMARTOFFERS_QA4_ACM_DB_PASSWORD",
        "SMARTOFFERS_QA4_BDA_DB_DSN",
        "SMARTOFFERS_QA4_BDA_DB_USER",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
        "SMARTOFFERS_QA4_DB_DSN",
        "SMARTOFFERS_QA4_DB_USER",
        "SMARTOFFERS_QA4_DB_PASSWORD",
        "SMARTOFFERS_QA4_TEST_MSISDN",
        "SMARTOFFERS_QA4_TEST_OFFER",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        bda_discovery,
        "run_qa4_bda_offer_discovery",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("BDA_DISCOVERY_NOT_CALLED_WHEN_PREFLIGHT_BLOCKS")
        ),
    )

    class NoRealHttpClient:
        def __init__(self):
            raise AssertionError("REAL_HTTP_CLIENT_NOT_CREATED_WHEN_PREFLIGHT_BLOCKS")

    monkeypatch.setattr(real_http_client, "RealHttpClient", NoRealHttpClient)

    result = app_module._qa4_owner_execution_inputs(_exact_provider_context())

    assert events == ["OFFLINE_PREFLIGHT"]
    assert result == {"ledger": offers_adapter._DEFAULT_ATTEMPT_LEDGER}


def test_owner_provider_rejects_malformed_or_widened_control_document_before_static_or_lazy_collaborators(monkeypatch):
    import core.real_execution.api_health_local_runtime_preflight as api_preflight
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery
    import core.real_execution.qa4_offers_customer_adapter as offers_adapter
    import core.real_execution.real_http_client as real_http_client

    def forbidden(*args, **kwargs):
        raise AssertionError("denied control document must not reach collaborator")

    monkeypatch.setattr(offers_adapter, "prepare_one_synthetic_qa4_offers_customer_create", forbidden)
    monkeypatch.setattr(api_preflight, "preflight_api_health_local_runtime", forbidden)
    monkeypatch.setattr(bda_discovery, "run_qa4_bda_offer_discovery", forbidden)
    monkeypatch.setattr(real_http_client, "RealHttpClient", forbidden)
    document = _exact_control_document()
    document["policy"]["runtime_flags"]["PRODUCTION"] = True
    monkeypatch.setenv("SMARTOFFERS_ALPHA_QA4_CONTROLLED_CONTRACT", json.dumps(document))

    result = app_module._qa4_owner_execution_inputs(_exact_provider_context())

    assert result == {}


@pytest.mark.parametrize("document", ["{not-json", "[]"])
def test_owner_provider_rejects_invalid_or_non_object_control_json_before_any_collaborator(
    monkeypatch, document
):
    import core.real_execution.api_health_local_runtime_preflight as api_preflight
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery
    import core.real_execution.qa4_offers_customer_adapter as offers_adapter
    import core.real_execution.real_http_client as real_http_client

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid control JSON must not reach collaborator")

    monkeypatch.setattr(offers_adapter, "prepare_one_synthetic_qa4_offers_customer_create", forbidden)
    monkeypatch.setattr(api_preflight, "preflight_api_health_local_runtime", forbidden)
    monkeypatch.setattr(bda_discovery, "run_qa4_bda_offer_discovery", forbidden)
    monkeypatch.setattr(real_http_client, "RealHttpClient", forbidden)
    monkeypatch.setenv("SMARTOFFERS_ALPHA_QA4_CONTROLLED_CONTRACT", document)

    assert app_module._qa4_owner_execution_inputs(_exact_provider_context()) == {}


def test_owner_provider_returns_discovery_readiness_without_http_or_transport_policy(monkeypatch):
    import core.real_execution.api_health_local_runtime_preflight as api_preflight
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery
    import core.real_execution.qa4_offers_customer_adapter as offers_adapter
    import core.real_execution.real_http_client as real_http_client

    events = []
    sentinel_ledger = object()

    monkeypatch.setenv(
        "SMARTOFFERS_ALPHA_QA4_CONTROLLED_CONTRACT", json.dumps(_exact_control_document())
    )
    monkeypatch.setattr(
        offers_adapter,
        "prepare_one_synthetic_qa4_offers_customer_create",
        lambda *args, **kwargs: events.append("static-offers") or {"preflight_status": "READY"},
    )
    monkeypatch.setattr(
        api_preflight,
        "preflight_scoped_qa4_offers_destination_attestation",
        lambda *args, **kwargs: events.append("destination")
        or {
            "status": api_preflight.SCOPED_OFFERS_DESTINATION_ATTESTATION_READY,
            "attestation": {
                "source": "derived_qa4_api_url",
                "environment": "QA4",
                "operation": "CREATE_OFFERS_CUSTOMER",
                "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
                "api_id": "post-vivo-next-habilitacao-de-cliente-ade0841563",
                "allowlist_match": True,
                "status": "MATCH",
            },
        },
    )
    monkeypatch.setattr(offers_adapter, "_DEFAULT_ATTEMPT_LEDGER", sentinel_ledger)
    monkeypatch.setattr(
        bda_discovery,
        "run_qa4_bda_offer_discovery",
        lambda *args, **kwargs: events.append("bda")
        or kwargs["offer_sink"]("FAKE_OFFER")
        or {"status": "QA4_BDA_OFFER_DISCOVERY_OK"},
    )

    class NoHttpClient:
        def __init__(self):
            raise AssertionError("static discovery must not create an HTTP client")

    monkeypatch.setattr(real_http_client, "RealHttpClient", NoHttpClient)
    result = app_module._qa4_owner_execution_inputs(_exact_provider_context())

    assert events == ["static-offers", "destination"]
    assert result["ledger"] is sentinel_ledger
    assert result["static_preflight"] == {
        "status": "READY",
        "test_offer_ready": False,
        "offers_attempts_used": 0,
    }
    assert not {"client", "runtime_secrets", "policy", "owner_opt_in", "approval"}.intersection(result)
    assert isinstance(result["environ"], dict)
    assert callable(result["runtime_factory"])
    assert "SMARTOFFERS_QA4_API_URL" not in str(result)


def test_real_controlled_bridge_reuses_provider_ledger_across_authorized_runs(monkeypatch):
    class Ledger:
        def __init__(self):
            self.scopes = set()

        def consume(self, scope):
            if scope in self.scopes:
                return False
            self.scopes.add(scope)
            return True

    ledger = Ledger()
    adapter_ledgers = []
    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "run_standard_qa4_application_mock",
        lambda context, *, mode, evaluated_at: {"result": "PASS"},
    )

    def adapter(context, **kwargs):
        adapter_ledgers.append(kwargs["ledger"])
        consumed = kwargs["ledger"].consume("ONE_QA4_OFFERS_CUSTOMER_CREATE_RUN")
        return {
            "result": "BLOCKED",
            "blockers": [] if consumed else ["ONE_QA4_OFFERS_CUSTOMER_CREATE_RUN_BUDGET_EXHAUSTED"],
            "send_attempted": False,
            "real_call_executed": False,
            "evidence": {"ATTEMPTS_USED": "0/1"},
        }

    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "execute_one_synthetic_qa4_offers_customer_create",
        adapter,
    )
    provider = lambda *_: {"ledger": ledger}

    first = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(), mode="real-controlled", evaluated_at=EVALUATED_AT,
        scenario_id=SYNTHETIC_OFFERS_SCENARIO, runtime_provider=provider,
    )
    second = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(), mode="real-controlled", evaluated_at=EVALUATED_AT,
        scenario_id=SYNTHETIC_OFFERS_SCENARIO, runtime_provider=provider,
    )

    assert adapter_ledgers == [ledger, ledger]
    assert first["executor_send_attempted"] is False
    assert second["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_RUN_BUDGET_EXHAUSTED"]
    assert second["evidence"]["ATTEMPTS_USED"] == "0/1"


def test_owner_provider_uses_scoped_attestation_then_lazy_bda_without_transport_composition(
    monkeypatch,
):
    import hashlib
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery
    import core.real_execution.qa4_offers_customer_adapter as offers_adapter
    import core.real_execution.real_http_client as real_http_client

    events = []
    environment = _offers_runtime_environment()
    environment.pop("SMARTOFFERS_QA4_TEST_OFFER")
    environment["SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT"] = hashlib.sha256(
        environment["SMARTOFFERS_QA4_API_URL"].encode("utf-8")
    ).hexdigest()
    monkeypatch.setenv("SMARTOFFERS_ALPHA_QA4_CONTROLLED_CONTRACT", json.dumps(_exact_control_document()))
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        offers_adapter,
        "prepare_one_synthetic_qa4_offers_customer_create",
        lambda *args, **kwargs: events.append("static")
        or {"preflight_status": "READY"},
    )
    monkeypatch.setattr(
        bda_discovery,
        "run_qa4_bda_offer_discovery",
        lambda *args, **kwargs: events.append("bda")
        or kwargs["offer_sink"]("DISCOVERED_OFFER")
        or {"status": "QA4_BDA_OFFER_DISCOVERY_OK"},
    )

    class NoHttpClient:
        def __init__(self):
            raise AssertionError("static discovery must not create an HTTP client")

    monkeypatch.setattr(real_http_client, "RealHttpClient", NoHttpClient)
    result = app_module._qa4_owner_execution_inputs(_exact_provider_context())

    assert events == ["static"]
    assert result["static_preflight"] == {
        "status": "READY", "test_offer_ready": False, "offers_attempts_used": 0,
    }
    assert "client" not in result
    assert "policy" not in result
    assert "DISCOVERED_OFFER" not in str(result)
    assert "qa4.example.invalid" not in str(result)


def test_owner_provider_blocks_invalid_bda_offer_without_constructing_boundary_client(monkeypatch):
    import hashlib
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery
    import core.real_execution.qa4_offers_customer_adapter as offers_adapter
    import core.real_execution.real_http_client as real_http_client

    environment = _offers_runtime_environment()
    environment.pop("SMARTOFFERS_QA4_TEST_OFFER")
    environment["SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT"] = hashlib.sha256(
        environment["SMARTOFFERS_QA4_API_URL"].encode("utf-8")
    ).hexdigest()
    monkeypatch.setenv("SMARTOFFERS_ALPHA_QA4_CONTROLLED_CONTRACT", json.dumps(_exact_control_document()))
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        offers_adapter,
        "prepare_one_synthetic_qa4_offers_customer_create",
        lambda *args, **kwargs: {"preflight_status": "READY"},
    )
    monkeypatch.setattr(
        bda_discovery,
        "run_qa4_bda_offer_discovery",
        lambda *args, **kwargs: {"status": "QA4_BDA_OFFER_DISCOVERY_OK"},
    )
    monkeypatch.setattr(
        real_http_client,
        "RealHttpClient",
        lambda: (_ for _ in ()).throw(AssertionError("boundary must not be constructed")),
    )

    result = app_module._qa4_owner_execution_inputs(_exact_provider_context())
    assert result["ledger"] is offers_adapter._DEFAULT_ATTEMPT_LEDGER
    assert isinstance(result["environ"], dict)
    assert callable(result["runtime_factory"])
    assert result["static_preflight"] == {
        "status": "READY", "test_offer_ready": False, "offers_attempts_used": 0,
    }


def test_atomic_discovery_hands_offer_to_real_controlled_run_without_persistence(monkeypatch):
    """The discovered offer crosses only the same-process call stack."""
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery

    events = []
    environment = _offers_runtime_environment()
    environment.pop("SMARTOFFERS_QA4_TEST_OFFER")
    client = _TransportMarkedManualClient(201)
    inputs = _executor_inputs()
    inputs["client"] = client
    inputs["owner_opt_in"] = _one_run_opt_in()
    inputs["ledger"] = OneRunAttemptLedger()

    monkeypatch.setattr(
        bda_discovery,
        "run_qa4_bda_offer_discovery",
        lambda **kwargs: events.append(("discovery", kwargs["driver"]))
        or kwargs["offer_sink"]("DISCOVERED_OFFER")
        or {"status": "QA4_BDA_OFFER_DISCOVERY_OK", "found_valid_offer": True},
    )
    monkeypatch.setattr(
        qa4_real_controlled_bridge,
        "run_standard_qa4_application_mock",
        lambda *args, **kwargs: events.append(("standard", None)) or {"result": "PASS"},
    )

    result = qa4_real_controlled_bridge.run_atomic_qa4_bda_offer_discovery_and_offers_create(
        _context(),
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
        bda_environ=environment,
        bda_driver=object(),
        bda_authorization={
            "owner_authorization": "ONE_ATOMIC_QA4_BDA_DISCOVERY_AND_OFFERS_CREATE_RUN",
            "operation": "QA4_BDA_OFFER_DISCOVERY",
            "bda_operation": "OFFER_DISCOVERY",
            "read_only_discovery_authorized": True,
            "authorization_verified": True,
            "destination_attestation_ready": True,
            "offers_operation": "CREATE_OFFERS_CUSTOMER",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "access_mode": "READ_ONLY",
            "attempts_used": 0,
        },
        runtime_provider=lambda *_: events.append(("provider", None)) or {
            "environ": environment,
            "runtime_factory": lambda: {
                **inputs,
                "client_factory": lambda: client,
            },
        },
    )

    assert [event[0] for event in events] == ["discovery", "standard", "provider"]
    assert len(client.calls) == 1
    assert result["result"] == "PASS"
    assert result["bda_discovery"]["status"] == "QA4_BDA_OFFER_DISCOVERY_OK"
    assert "DISCOVERED_OFFER" not in repr(result)
    assert "SMARTOFFERS_QA4_TEST_OFFER" not in repr(result)


def test_atomic_run_id_authorization_mismatch_blocks_before_driver_or_discovery(monkeypatch):
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery

    monkeypatch.setattr(
        bda_discovery,
        "run_qa4_bda_offer_discovery",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("discovery must not run")),
    )
    result = qa4_real_controlled_bridge.run_atomic_qa4_bda_offer_discovery_and_offers_create(
        _context() | {"run_id": "ALPHA_REAL_RUN_02"},
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
        bda_environ={},
        bda_driver_factory=lambda: (_ for _ in ()).throw(AssertionError("driver factory must not run")),
        bda_authorization={"owner_authorization": "ONE_ATOMIC_QA4_BDA_DISCOVERY_AND_OFFERS_CREATE_RUN"},
    )

    assert result["result"] == "BLOCKED"
    assert result["bda_discovery"]["status"] == "QA4_BDA_OFFER_DISCOVERY_BLOCKED"


def test_real_controlled_api_uses_atomic_handoff_and_never_constructs_http_on_bda_block(
    app_client_factory, monkeypatch
):
    client, _ = app_client_factory("atomic-app-entry")
    atomic_calls = []
    monkeypatch.setattr(
        app_module,
        "_governed_bda_driver",
        lambda: object(),
        raising=False,
    )
    monkeypatch.setattr(
        app_module,
        "_qa4_controlled_contract_from_environ",
        lambda: _exact_control_document(),
    )
    monkeypatch.setattr(
        app_module,
        "_atomic_static_preflight_ready",
        lambda context, contract: True,
        raising=False,
    )
    monkeypatch.setattr(
        app_module,
        "run_atomic_qa4_bda_offer_discovery_and_offers_create",
        lambda *args, **kwargs: atomic_calls.append(kwargs)
        or {"result": "BLOCKED", "real_call_executed": False},
        raising=False,
    )
    monkeypatch.setattr(app_module, "_trusted_local_now", lambda: datetime.fromisoformat("2026-08-25T12:00:00+00:00"))

    response = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "QA4",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
            "evaluated_at": EVALUATED_AT,
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {"result": "BLOCKED", "real_call_executed": False}
    assert len(atomic_calls) == 1
    assert callable(atomic_calls[0]["bda_driver_factory"])
    assert callable(atomic_calls[0]["runtime_provider"])


def test_atomic_bda_failure_never_reaches_runtime_provider_or_http_client(monkeypatch):
    import core.real_execution.qa4_bda_offer_discovery as bda_discovery

    provider_calls = []
    monkeypatch.setattr(
        bda_discovery,
        "run_qa4_bda_offer_discovery",
        lambda **kwargs: {"status": "QA4_BDA_OFFER_DISCOVERY_BLOCKED"},
    )

    result = qa4_real_controlled_bridge.run_atomic_qa4_bda_offer_discovery_and_offers_create(
        _context(),
        mode="real-controlled",
        evaluated_at=EVALUATED_AT,
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
        bda_environ={},
        bda_driver=object(),
        bda_authorization={
            "owner_authorization": "ONE_ATOMIC_QA4_BDA_DISCOVERY_AND_OFFERS_CREATE_RUN",
            "operation": "QA4_BDA_OFFER_DISCOVERY",
        },
        runtime_provider=lambda *_: provider_calls.append("constructed") or {},
    )

    assert result["result"] == "BLOCKED"
    assert provider_calls == []


def test_owner_provider_defers_real_http_client_to_runtime_factory(monkeypatch):
    import hashlib
    import core.real_execution.real_http_client as real_http_client

    environment = _offers_runtime_environment()
    environment["SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT"] = hashlib.sha256(
        environment["SMARTOFFERS_QA4_API_URL"].encode("utf-8")
    ).hexdigest()
    monkeypatch.setenv(
        "SMARTOFFERS_ALPHA_QA4_CONTROLLED_CONTRACT", json.dumps(_exact_control_document())
    )
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    constructed = []
    monkeypatch.setattr(
        real_http_client,
        "RealHttpClient",
        lambda: constructed.append("client") or object(),
    )

    inputs = app_module._qa4_owner_execution_inputs(_exact_provider_context())

    assert constructed == []
    assert callable(inputs["runtime_factory"])
    runtime = inputs["runtime_factory"]()
    assert constructed == []
    assert callable(runtime["client_factory"])
    runtime["client_factory"]()
    assert constructed == ["client"]


def test_atomic_route_reuses_app_bda_ledger_and_blocks_second_before_driver_factory(
    app_client_factory, monkeypatch
):
    from core.real_execution.qa4_bda_offer_discovery import BdaDiscoveryAttemptLedger

    client, _ = app_client_factory("atomic-repeat-ledger")
    shared_ledger = BdaDiscoveryAttemptLedger()
    ledgers = []
    driver_factory_calls = []
    monkeypatch.setattr(app_module, "_DEFAULT_BDA_DISCOVERY_LEDGER", shared_ledger)
    monkeypatch.setattr(app_module, "_atomic_static_preflight_ready", lambda *args: True)
    monkeypatch.setattr(app_module, "_trusted_local_now", lambda: datetime.fromisoformat("2026-08-25T12:00:00+00:00"))
    monkeypatch.setattr(
        app_module, "_governed_bda_driver", lambda: driver_factory_calls.append("driver") or object()
    )

    def atomic(*args, **kwargs):
        ledger = kwargs["bda_ledger"]
        ledgers.append(ledger)
        if not ledger.consume("QA4_BDA_OFFER_DISCOVERY"):
            return {"result": "BLOCKED", "driver_started": False}
        kwargs["bda_driver_factory"]()
        return {"result": "BLOCKED", "driver_started": True}

    monkeypatch.setattr(app_module, "run_atomic_qa4_bda_offer_discovery_and_offers_create", atomic)
    request_data = {
        **_context(),
        "environment": "QA4",
        "mode": "real-controlled",
        "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
        "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
        "evaluated_at": EVALUATED_AT,
    }

    first = client.post("/api/qa4/standard/real-controlled-run", json=request_data)
    second = client.post("/api/qa4/standard/real-controlled-run", json=request_data)

    assert first.get_json() == {"result": "BLOCKED", "driver_started": True}
    assert second.get_json() == {"result": "BLOCKED", "driver_started": False}
    assert ledgers == [shared_ledger, shared_ledger]
    assert driver_factory_calls == ["driver"]


@pytest.mark.parametrize(
    ("now", "window_started_at", "window_expires_at", "expected_reason"),
    [
        ("2026-08-25T12:06:00+00:00", "2026-08-25T11:55:00+00:00", "2026-08-25T12:05:00+00:00", "WINDOW_EXPIRED"),
        ("2026-08-25T11:54:00+00:00", "2026-08-25T11:55:00+00:00", "2026-08-25T12:05:00+00:00", "WINDOW_NOT_STARTED"),
        ("2026-08-25T12:00:00+00:00", "2026-08-25T11:55:00", "2026-08-25T12:05:00", "WINDOW_INVALID"),
    ],
)
def test_atomic_route_blocks_inactive_window_before_atomic_bridge(
    app_client_factory, monkeypatch, now, window_started_at, window_expires_at, expected_reason
):
    client, _ = app_client_factory("atomic-window-gate")
    bridge_calls = []
    monkeypatch.setattr(app_module, "_atomic_static_preflight_ready", lambda *args: True)
    monkeypatch.setattr(app_module, "_trusted_local_now", lambda: datetime.fromisoformat(now))
    monkeypatch.setattr(
        app_module,
        "run_atomic_qa4_bda_offer_discovery_and_offers_create",
        lambda *args, **kwargs: bridge_calls.append(kwargs) or {"result": "PASS"},
    )

    response = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "QA4",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
            "window_started_at": window_started_at,
            "window_expires_at": window_expires_at,
            "evaluated_at": EVALUATED_AT,
        },
    )

    assert response.get_json() == {"result": "BLOCKED", "reason": expected_reason}
    assert bridge_calls == []
