from core.real_execution.qa4_offers_customer_adapter import (
    OneRunAttemptLedger,
    execute_qa4_offers_customer_create,
    prepare_one_synthetic_qa4_offers_customer_create,
    prepare_qa4_offers_customer_create,
)


def _context():
    return {
        "environment": "qa4",
        "workflow_profile": "smartoffers_qa4_full_smoke",
        "event_time": "2026-08-25 12:00:00",
    }


def _runtime_env():
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


class LocalManualClient:
    is_real_manual_client = True

    def __init__(self, status_code):
        self.status_code = status_code
        self.calls = []

    def send(self, sanitized_request, runtime_secrets, timeout_seconds):
        self.calls.append(
            {
                "request": dict(sanitized_request),
                "timeout": timeout_seconds,
                "body_is_bytes": isinstance(runtime_secrets.get("body"), bytes),
            }
        )
        return {
            "status_code": self.status_code,
            "ok": 200 <= self.status_code < 300,
            "elapsed_ms": 1,
            "body_recorded": False,
        }


class TransportMarkedLocalClient(LocalManualClient):
    """In-memory stand-in for the isolated real client; it never opens a socket."""

    is_real_transport_client = True


def _runtime_refs():
    return {
        "QA4_HOST_REF": "runtime-ref:qa4-host",
        "AUTH_REF": "runtime-ref:qa4-auth",
        "SENSITIVE_HEADERS_REF": "runtime-ref:qa4-headers",
        "TEST_PAYLOAD_REF": "runtime-ref:qa4-body",
        "CORRELATION_ID": "corr-safe-001",
    }


def _runtime_secrets():
    return {
        "endpoint": "in-memory-endpoint",
        "auth": "in-memory-auth",
        "headers": {"content-type": "application/json"},
        "body": b"unused",
        "correlation_id": "corr-safe-001",
        "timeout_seconds": 5,
    }


def _policy():
    api_id = "post-vivo-next-habilitacao-de-cliente-ade0841563"
    return {
        "runtime_flags": {"REAL_EXECUTION_ENABLED": True, "REAL_EXECUTION_KILL_SWITCH": False},
        "first_qa4_allowlist": {
            "allowed_api_ids": [api_id],
            "items": {
                api_id: {
                    "api_id": api_id,
                    "method": "POST",
                    "environment": "QA4",
                    "timeout_seconds": 5,
                    "retry_count": 0,
                    "status": "manual_offers_customer",
                }
            },
        },
    }


def _approval():
    return {
        "approved": True,
        "risk_acceptance": True,
        "approver_ref": "apr-safe-001",
        "ticket_ref": "chg-safe-001",
        "approved_api_id": "post-vivo-next-habilitacao-de-cliente-ade0841563",
        "approved_environment": "QA4",
        "approved_at_ref": "time-safe-001",
    }


def _one_offers_customer_create_opt_in():
    return {
        "approved": True,
        "operation": "ONE_QA4_OFFERS_CUSTOMER_CREATE_RUN",
        "environment": "QA4",
        "max_attempts": 1,
        "retry_count": 0,
        "fallback": False,
    }


def test_preflight_reuses_legacy_payload_builder_but_keeps_catalogued_real_operation_blocked():
    runtime_env = _runtime_env()

    result = prepare_qa4_offers_customer_create(_context(), environ=runtime_env)

    assert result["decision"] == "BLOCKED"
    assert result["operation"] == "CREATE_OFFERS_CUSTOMER"
    assert result["blockers"] == ["REAL_QA4_OPERATION_NOT_CONFIRMED"]
    assert result["preflight_status"] == "READY"
    assert result["request_contract"] == {
        "api_id": "post-vivo-next-habilitacao-de-cliente-ade0841563",
        "method": "POST",
        "path": "/ws/integration/online/process",
        "legacy_operation": "processEvent",
        "legacy_builder_applied": True,
    }
    assert result["attempt_policy"] == {
        "max_attempts": 1,
        "retry_count": 0,
        "fallback": False,
    }
    assert result["transport_permitted"] is False
    assert result["send_attempted"] is False
    rendered = str(result)
    for value in runtime_env.values():
        assert value not in rendered


def test_preflight_reads_runtime_test_refs_when_no_environment_is_injected(monkeypatch):
    for key, value in _runtime_env().items():
        monkeypatch.setenv(key, value)

    result = prepare_qa4_offers_customer_create(_context())

    assert result["decision"] == "BLOCKED"
    assert result["preflight_status"] == "READY"
    assert result["test_data"] == {"available": True}


def test_preflight_blocks_when_synthetic_customer_reference_is_absent():
    runtime_env = _runtime_env()
    runtime_env.pop("SMARTOFFERS_QA4_TEST_MSISDN")

    result = prepare_qa4_offers_customer_create(_context(), environ=runtime_env)

    assert result["decision"] == "BLOCKED"
    assert result["blockers"] == [
        "QA4_TEST_DATA_REQUIRED",
        "REAL_QA4_OPERATION_NOT_CONFIRMED",
    ]
    assert result["request_contract"]["legacy_builder_applied"] is False
    assert result["send_attempted"] is False


def test_one_synthetic_preflight_generates_one_candidate_uses_today_and_keeps_values_out_of_evidence():
    runtime_env = _runtime_env()
    runtime_env.pop("SMARTOFFERS_QA4_TEST_MSISDN")
    fixed_now = "25-08-2026 12:00:00"

    result = prepare_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=runtime_env,
        current_time=lambda: fixed_now,
        random_int=lambda lower, upper: lower,
    )

    assert result["decision"] == "BLOCKED"
    assert result["preflight_status"] == "READY"
    assert result["test_data"] == {"available": True, "source": "synthetic"}
    assert result["request_contract"]["legacy_builder_applied"] is True
    assert result["attempt_policy"] == {"max_attempts": 1, "retry_count": 0, "fallback": False}
    assert result["send_attempted"] is False
    rendered = str(result)
    assert "119" not in rendered
    assert "NEXT_" not in rendered
    assert fixed_now not in rendered


def test_preflight_blocks_non_qa4_context_before_any_payload_is_built():
    result = prepare_qa4_offers_customer_create(
        _context() | {"environment": "qa3"}, environ=_runtime_env()
    )

    assert result["decision"] == "BLOCKED"
    assert result["blockers"] == [
        "ENVIRONMENT_NOT_QA4",
        "REAL_QA4_OPERATION_NOT_CONFIRMED",
    ]
    assert result["request_contract"]["legacy_builder_applied"] is False


def test_exact_offers_executor_maps_authorized_local_2xx_to_pass_without_evidence_leak():
    client = LocalManualClient(202)

    result = execute_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_policy(),
        client=client,
        approval=_approval(),
    )

    assert result["result"] == "PASS"
    assert result["request_contract"]["api_id"] == "post-vivo-next-habilitacao-de-cliente-ade0841563"
    assert len(client.calls) == 1
    assert client.calls[0]["request"]["api_id"] == "post-vivo-next-habilitacao-de-cliente-ade0841563"
    assert client.calls[0]["timeout"] == 5
    assert client.calls[0]["body_is_bytes"] is True
    assert result["real_call_executed"] is True
    assert "5511999999999" not in str(result)
    assert "QA4_SYNTHETIC_OFFER" not in str(result)


def test_exact_offers_executor_maps_one_local_non_2xx_response_to_fail_without_retry():
    client = LocalManualClient(503)

    result = execute_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_policy(),
        client=client,
        approval=_approval(),
    )

    assert result["result"] == "FAIL"
    assert len(client.calls) == 1
    assert result["attempt_policy"] == {"max_attempts": 1, "retry_count": 0, "fallback": False}


def test_exact_offers_executor_default_remains_blocked_before_any_client_send():
    client = LocalManualClient(202)

    result = execute_qa4_offers_customer_create(_context(), client=client)

    assert result["result"] == "BLOCKED"
    assert client.calls == []
    assert result["real_call_executed"] is False


def test_transport_marked_client_requires_bounded_owner_opt_in_before_one_local_send():
    client = TransportMarkedLocalClient(201)

    result = execute_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_policy(),
        client=client,
        approval=_approval(),
        owner_opt_in=_one_offers_customer_create_opt_in(),
        ledger=OneRunAttemptLedger(),
    )

    assert result["result"] == "PASS"
    assert len(client.calls) == 1
    assert client.calls[0]["request"]["api_id"] == "post-vivo-next-habilitacao-de-cliente-ade0841563"


def test_transport_marked_client_is_blocked_without_owner_opt_in_before_send():
    client = TransportMarkedLocalClient(201)

    result = execute_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_policy(),
        client=client,
        approval=_approval(),
    )

    assert result["result"] == "BLOCKED"
    assert result["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_RUN_OPT_IN_REQUIRED"]
    assert client.calls == []


def test_transport_marked_client_is_blocked_when_owner_opt_in_scope_does_not_match():
    client = TransportMarkedLocalClient(201)
    opt_in = _one_offers_customer_create_opt_in() | {"operation": "OTHER_OPERATION"}

    result = execute_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_policy(),
        client=client,
        approval=_approval(),
        owner_opt_in=opt_in,
    )

    assert result["result"] == "BLOCKED"
    assert result["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_RUN_OPT_IN_REQUIRED"]
    assert client.calls == []


def test_transport_attempt_ledger_blocks_second_send_after_first_failure():
    client = TransportMarkedLocalClient(503)
    ledger = OneRunAttemptLedger()
    inputs = {
        "environ": _runtime_env(),
        "runtime_refs": _runtime_refs(),
        "runtime_secrets": _runtime_secrets(),
        "policy": _policy(),
        "client": client,
        "approval": _approval(),
        "owner_opt_in": _one_offers_customer_create_opt_in(),
        "ledger": ledger,
    }

    first = execute_qa4_offers_customer_create(_context(), **inputs)
    second = execute_qa4_offers_customer_create(_context(), **inputs)

    assert first["result"] == "FAIL"
    assert second["result"] == "BLOCKED"
    assert second["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_RUN_BUDGET_EXHAUSTED"]
    assert second["evidence"] == {"attempt_budget": "EXHAUSTED"}
    assert len(client.calls) == 1
