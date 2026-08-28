import json
from datetime import datetime, timedelta

from core.real_execution.qa4_offers_customer_adapter import (
    OneRunAttemptLedger,
    execute_one_synthetic_qa4_offers_customer_create,
    execute_qa4_offers_customer_create,
    prepare_one_synthetic_qa4_offers_customer_create,
    prepare_qa4_offers_customer_create,
)
from core.real_execution.real_http_client import RealHttpClient
import core.real_execution.real_http_client as real_http_client


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


def test_synthetic_static_preflight_can_defer_offer_until_authorized_bda_discovery():
    environment = _runtime_env()
    environment.pop("SMARTOFFERS_QA4_TEST_OFFER")

    result = prepare_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=environment,
        approval=_approval(),
        defer_offer_validation=True,
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["preflight_status"] == "READY"
    assert result["test_data"] == {"available": False, "source": "synthetic"}


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


class ContractInspectingTransportClient(TransportMarkedLocalClient):
    def __init__(self, status_code, expected_event_time):
        super().__init__(status_code)
        self.expected_event_time = expected_event_time
        self.body_contract_ok = False

    def send(self, sanitized_request, runtime_secrets, timeout_seconds):
        payload = json.loads(runtime_secrets["body"].decode("utf-8"))
        attributes = payload["attributes"]
        account = attributes["447500851"]
        self.body_contract_ok = (
            payload["operation"] == "processEvent"
            and payload["eventTime"] == self.expected_event_time
            and attributes["1667261676"].startswith("119")
            and account == attributes["1667261676"][3:]
            and attributes["1597489127"] == f"NEXT_{account}"
        )
        return super().send(sanitized_request, runtime_secrets, timeout_seconds)


class LocalUrlopenResponse:
    status = 201

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def getcode(self):
        return self.status

    def read(self, size):
        assert size == 0
        return b""


class LocalUrlopenRequest:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


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
        "runtime_flags": {
            "REAL_EXECUTION_ENABLED": True,
            "REAL_EXECUTION_KILL_SWITCH": False,
            "REAL_TRANSPORT_ALLOWED": True,
            "PRODUCTION": False,
            "GLOBAL_NO_AUTH_ENABLED": False,
        },
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


def _no_auth_policy():
    policy = _policy()
    item = next(iter(policy["first_qa4_allowlist"]["items"].values()))
    item.update(
        {
            "operation": "CREATE_OFFERS_CUSTOMER",
            "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
            "auth_required": False,
        }
    )
    policy["operation_scoped_no_auth"] = {
        "authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "operation": "CREATE_OFFERS_CUSTOMER",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "environment": "QA4",
        "auth_required": False,
    }
    policy["destination_attestation"] = {
        "source": "local_runtime_config",
        "environment": "QA4",
        "allowlist_match": True,
        "status": "MATCH",
    }
    return policy


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
        "operation": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "environment": "QA4",
        "mode": "real-controlled",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
        "max_attempts": 1,
        "retry_count": 0,
        "fallback": False,
        "production": False,
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
    fixed_now = datetime.now().strftime("%d-%m-%Y 12:00:00")

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


def test_one_synthetic_execute_uses_one_candidate_with_today_and_sanitized_evidence():
    runtime_env = _runtime_env()
    runtime_env.pop("SMARTOFFERS_QA4_TEST_MSISDN")
    today = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    generator_calls = []
    client = ContractInspectingTransportClient(201, today)

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=runtime_env,
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_no_auth_policy(),
        client=client,
        approval=_approval(),
        owner_opt_in=_one_offers_customer_create_opt_in(),
        ledger=OneRunAttemptLedger(),
        current_time=lambda: today,
        random_int=lambda lower, upper: generator_calls.append((lower, upper)) or lower,
    )

    assert result["result"] == "PASS"
    assert generator_calls == [(20_000_000, 99_999_999)]
    assert len(client.calls) == 1
    assert client.body_contract_ok is True
    rendered = str(result)
    assert "119" not in rendered
    assert "NEXT_" not in rendered
    assert runtime_env["SMARTOFFERS_QA4_TEST_OFFER"] not in rendered


def test_one_synthetic_execute_blocks_malformed_or_historical_date_without_send():
    runtime_env = _runtime_env()
    runtime_env.pop("SMARTOFFERS_QA4_TEST_MSISDN")
    client = TransportMarkedLocalClient(201)
    historical = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y %H:%M:%S")

    for clock_value in ("invalid-date", historical):
        result = execute_one_synthetic_qa4_offers_customer_create(
            _context(),
            environ=runtime_env,
            runtime_refs=_runtime_refs(),
            runtime_secrets=_runtime_secrets(),
            policy=_no_auth_policy(),
            client=client,
            approval=_approval(),
            owner_opt_in=_one_offers_customer_create_opt_in(),
            ledger=OneRunAttemptLedger(),
            current_time=lambda value=clock_value: value,
        )

        assert result["result"] == "BLOCKED"
        assert "INVALID_EVENT_TIME" in result["blockers"]

    assert client.calls == []


def test_actual_real_http_client_without_bounded_opt_in_blocks_before_urlopen(monkeypatch):
    runtime_env = _runtime_env()
    runtime_env.pop("SMARTOFFERS_QA4_TEST_MSISDN")
    urlopen_calls = []
    monkeypatch.setattr(
        real_http_client.urllib.request,
        "urlopen",
        lambda *args, **kwargs: urlopen_calls.append((args, kwargs)),
    )

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=runtime_env,
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
            policy=_no_auth_policy(),
        client=RealHttpClient(),
        approval=_approval(),
        ledger=OneRunAttemptLedger(),
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "BLOCKED"
    assert result["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN_OPT_IN_REQUIRED"]
    assert urlopen_calls == []


def test_actual_real_http_client_has_explicit_transport_marker():
    assert getattr(RealHttpClient(), "is_real_transport_client", False) is True


def test_actual_real_http_client_with_one_run_opt_in_sends_once_then_exhausts_budget(monkeypatch):
    runtime_env = _runtime_env()
    runtime_env.pop("SMARTOFFERS_QA4_TEST_MSISDN")
    urlopen_calls = []
    monkeypatch.setattr(
        real_http_client.urllib.request,
        "urlopen",
        lambda *args, **kwargs: urlopen_calls.append((args, kwargs)) or LocalUrlopenResponse(),
    )
    monkeypatch.setattr(real_http_client.urllib.request, "Request", LocalUrlopenRequest)
    ledger = OneRunAttemptLedger()
    inputs = {
        "environ": runtime_env,
        "runtime_refs": _runtime_refs(),
        "runtime_secrets": _runtime_secrets(),
        "policy": _no_auth_policy(),
        "client": RealHttpClient(),
        "approval": _approval(),
        "owner_opt_in": _one_offers_customer_create_opt_in(),
        "ledger": ledger,
        "current_time": lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    }

    first = execute_one_synthetic_qa4_offers_customer_create(_context(), **inputs)
    second = execute_one_synthetic_qa4_offers_customer_create(_context(), **inputs)

    assert first["result"] == "PASS"
    assert second["result"] == "BLOCKED"
    assert second["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN_BUDGET_EXHAUSTED"]
    assert len(urlopen_calls) == 1


def test_exact_allowlisted_synthetic_qa4_create_can_send_without_authorization_header(monkeypatch):
    runtime_env = _runtime_env()
    runtime_env.pop("SMARTOFFERS_QA4_TEST_MSISDN")
    captured_requests = []
    monkeypatch.setattr(
        real_http_client.urllib.request,
        "urlopen",
        lambda request, **kwargs: captured_requests.append(request) or LocalUrlopenResponse(),
    )
    monkeypatch.setattr(real_http_client.urllib.request, "Request", LocalUrlopenRequest)
    runtime_refs = _runtime_refs()
    runtime_refs.pop("AUTH_REF")
    runtime_secrets = _runtime_secrets()
    runtime_secrets.pop("auth")

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=runtime_env,
        runtime_refs=runtime_refs,
        runtime_secrets=runtime_secrets,
        policy=_no_auth_policy(),
        client=RealHttpClient(),
        approval=_approval(),
        owner_opt_in=_one_offers_customer_create_opt_in(),
        ledger=OneRunAttemptLedger(),
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "PASS"
    assert len(captured_requests) == 1
    assert "Authorization" not in captured_requests[0].kwargs["headers"]


def test_no_auth_exception_fails_closed_for_another_scenario_before_send():
    client = TransportMarkedLocalClient(201)
    policy = _no_auth_policy()
    item = next(iter(policy["first_qa4_allowlist"]["items"].values()))
    item["scenario_id"] = "OTHER_SCENARIO"
    runtime_refs = _runtime_refs()
    runtime_refs.pop("AUTH_REF")
    runtime_secrets = _runtime_secrets()
    runtime_secrets.pop("auth")

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=runtime_refs,
        runtime_secrets=runtime_secrets,
        policy=policy,
        client=client,
        approval=_approval(),
        owner_opt_in=_one_offers_customer_create_opt_in(),
        ledger=OneRunAttemptLedger(),
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "BLOCKED"
    assert client.calls == []


def test_policy_and_owner_opt_in_authorizations_must_match_before_client_factory():
    policy = _no_auth_policy()
    policy["operation_scoped_no_auth"]["authorization"] = "ONE_QA4_REPEATABILITY_SMOKE_RUN_02"
    factory_calls = []

    result = execute_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=policy,
        approval=_approval(),
        owner_opt_in=_one_offers_customer_create_opt_in(),
        ledger=OneRunAttemptLedger(),
        client_factory=lambda: factory_calls.append("constructed") or TransportMarkedLocalClient(201),
        synthetic_customer={"msisdn": "11999999999"},
        offer="LOCAL_TEST_OFFER",
    )

    assert result["result"] == "BLOCKED"
    assert "OPERATION_SCOPED_NO_AUTH_REQUIRED" in result["blockers"]
    assert factory_calls == []


def test_no_auth_flag_without_exact_operation_scope_remains_auth_required():
    client = TransportMarkedLocalClient(201)
    policy = _policy()
    item = next(iter(policy["first_qa4_allowlist"]["items"].values()))
    item["auth_required"] = False
    runtime_refs = _runtime_refs()
    runtime_refs.pop("AUTH_REF")
    runtime_secrets = _runtime_secrets()
    runtime_secrets.pop("auth")

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=runtime_refs,
        runtime_secrets=runtime_secrets,
        policy=policy,
        client=client,
        approval=_approval(),
        owner_opt_in=_one_offers_customer_create_opt_in(),
        ledger=OneRunAttemptLedger(),
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "BLOCKED"
    assert "OPERATION_SCOPED_NO_AUTH_REQUIRED" in result["blockers"]
    assert client.calls == []


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

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_no_auth_policy(),
        client=client,
        approval=_approval(),
        owner_opt_in=_one_offers_customer_create_opt_in(),
        ledger=OneRunAttemptLedger(),
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "PASS"
    assert len(client.calls) == 1
    assert client.calls[0]["request"]["api_id"] == "post-vivo-next-habilitacao-de-cliente-ade0841563"


def test_transport_marked_client_is_blocked_without_owner_opt_in_before_send():
    client = TransportMarkedLocalClient(201)

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_no_auth_policy(),
        client=client,
        approval=_approval(),
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "BLOCKED"
    assert result["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN_OPT_IN_REQUIRED"]
    assert client.calls == []


def test_transport_marked_client_is_blocked_when_owner_opt_in_scope_does_not_match():
    client = TransportMarkedLocalClient(201)
    opt_in = _one_offers_customer_create_opt_in() | {"operation": "OTHER_OPERATION"}

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs(),
        runtime_secrets=_runtime_secrets(),
        policy=_no_auth_policy(),
        client=client,
        approval=_approval(),
        owner_opt_in=opt_in,
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "BLOCKED"
    assert result["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN_OPT_IN_REQUIRED"]
    assert client.calls == []


def test_transport_attempt_ledger_blocks_second_send_after_first_failure():
    client = TransportMarkedLocalClient(503)
    ledger = OneRunAttemptLedger()
    inputs = {
        "environ": _runtime_env(),
        "runtime_refs": _runtime_refs(),
        "runtime_secrets": _runtime_secrets(),
        "policy": _no_auth_policy(),
        "client": client,
        "approval": _approval(),
        "owner_opt_in": _one_offers_customer_create_opt_in(),
        "ledger": ledger,
    }

    inputs["current_time"] = lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    first = execute_one_synthetic_qa4_offers_customer_create(_context(), **inputs)
    second = execute_one_synthetic_qa4_offers_customer_create(_context(), **inputs)

    assert first["result"] == "FAIL"
    assert second["result"] == "BLOCKED"
    assert second["blockers"] == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN_BUDGET_EXHAUSTED"]
    assert second["evidence"]["decision"] == "blocked"
    assert len(client.calls) == 1


def test_real_transport_contract_defaults_to_denied_without_explicit_transport_flag():
    client = TransportMarkedLocalClient(201)
    policy = _no_auth_policy()
    policy["runtime_flags"].pop("REAL_TRANSPORT_ALLOWED")
    policy["runtime_flags"]["PRODUCTION"] = False
    policy["runtime_flags"]["GLOBAL_NO_AUTH_ENABLED"] = False
    policy["destination_attestation"] = {
        "source": "local_runtime_config",
        "environment": "QA4",
        "allowlist_match": True,
        "status": "MATCH",
    }
    opt_in = _one_offers_customer_create_opt_in() | {
        "authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
    }

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=_runtime_refs() | {"AUTH_REF": None},
        runtime_secrets=_runtime_secrets() | {"auth": None},
        policy=policy,
        client=client,
        approval=_approval(),
        owner_opt_in=opt_in,
        ledger=OneRunAttemptLedger(),
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "BLOCKED"
    assert result["blockers"] == ["REAL_TRANSPORT_ALLOWED_REQUIRED"]
    assert client.calls == []


def test_real_transport_contract_requires_exact_scoped_no_auth_destination_and_confirmation():
    client = TransportMarkedLocalClient(201)
    policy = _no_auth_policy()
    policy["runtime_flags"].update(
        {
            "REAL_TRANSPORT_ALLOWED": True,
            "PRODUCTION": False,
            "GLOBAL_NO_AUTH_ENABLED": False,
        }
    )
    policy["destination_attestation"] = {
        "source": "local_runtime_config",
        "environment": "QA4",
        "allowlist_match": True,
        "status": "MATCH",
    }
    runtime_refs = _runtime_refs()
    runtime_refs.pop("AUTH_REF")
    runtime_secrets = _runtime_secrets()
    runtime_secrets.pop("auth")
    opt_in = _one_offers_customer_create_opt_in() | {
        "authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
    }

    result = execute_one_synthetic_qa4_offers_customer_create(
        _context(),
        environ=_runtime_env(),
        runtime_refs=runtime_refs,
        runtime_secrets=runtime_secrets,
        policy=policy,
        client=client,
        approval=_approval(),
        owner_opt_in=opt_in,
        ledger=OneRunAttemptLedger(),
        current_time=lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

    assert result["result"] == "PASS"
    assert len(client.calls) == 1
    assert "local_runtime_config" not in str(result)


def test_real_transport_contract_never_consumes_budget_before_all_gates_and_keeps_it_after_send_error():
    class Ledger:
        def __init__(self):
            self.consumed = []

        def consume(self, scope):
            self.consumed.append(scope)
            return len(self.consumed) == 1

    class FailingClient(TransportMarkedLocalClient):
        def send(self, *args, **kwargs):
            self.calls.append({"boundary": "entered"})
            raise TimeoutError("local fake timeout")

    ledger = Ledger()
    policy = _no_auth_policy()
    policy["runtime_flags"].update(
        {
            "REAL_TRANSPORT_ALLOWED": True,
            "PRODUCTION": False,
            "GLOBAL_NO_AUTH_ENABLED": False,
        }
    )
    policy["destination_attestation"] = {"status": "MISMATCH"}
    opt_in = _one_offers_customer_create_opt_in() | {
        "authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "application_confirmation": "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER",
    }
    client = FailingClient(201)
    inputs = {
        "environ": _runtime_env(),
        "runtime_refs": _runtime_refs() | {"AUTH_REF": None},
        "runtime_secrets": _runtime_secrets() | {"auth": None},
        "policy": policy,
        "client": client,
        "approval": _approval(),
        "owner_opt_in": opt_in,
        "ledger": ledger,
        "current_time": lambda: datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    }

    blocked = execute_one_synthetic_qa4_offers_customer_create(_context(), **inputs)
    assert blocked["result"] == "BLOCKED"
    assert ledger.consumed == []
    assert client.calls == []

    policy["destination_attestation"] = {
        "source": "local_runtime_config",
        "environment": "QA4",
        "allowlist_match": True,
        "status": "MATCH",
    }
    failed = execute_one_synthetic_qa4_offers_customer_create(_context(), **inputs)
    assert failed["result"] == "FAIL"
    assert ledger.consumed == ["ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN"]
    assert client.calls == [{"boundary": "entered"}]
