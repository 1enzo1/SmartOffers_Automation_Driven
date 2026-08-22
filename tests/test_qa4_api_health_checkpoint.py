import hashlib
import inspect
from copy import deepcopy
from pathlib import Path

import pytest
import tools.qa4_api_health_smoke as api_health_smoke

from core.api_catalog.catalog import get_api_catalog
from core.api_catalog.policy import is_mock_plannable
from core.real_execution.allowlist import validate_first_qa4_allowlist
from core.real_execution.api_health_local_runtime_preflight import (
    API_CHECKPOINT,
    API_ENVIRONMENT,
    API_OPERATION_ID,
    API_PROFILE,
    API_REQUIRED_REFS,
    API_RESOURCE_ID,
    API_RUNTIME_BLOCKED,
    API_RUNTIME_READY,
    preflight_api_health_local_runtime,
)
from core.real_execution.gate_dag import normalize_checkpoint_evidence
from tools.qa4_api_health_smoke import (
    API_HEALTH_CHECKPOINT_BLOCKED,
    API_HEALTH_CHECKPOINT_FAILED,
    API_HEALTH_CHECKPOINT_OK,
    FakeHttpClient,
    FakeResponse,
    main,
    run_api_health_checkpoint,
)


class FakeConnectTimeout(Exception):
    pass


class FakeReadTimeout(Exception):
    pass


EVALUATED_AT = "2026-08-22T12:10:00+00:00"


def _sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _request(**overrides):
    request = {
        "checkpoint": API_CHECKPOINT,
        "api_operation_id": API_OPERATION_ID,
        "environment": API_ENVIRONMENT,
        "profile": API_PROFILE,
        "resource_id": API_RESOURCE_ID,
    }
    request.update(overrides)
    return request


def _runtime():
    endpoint = "https://fake-qa4-api.example"
    path = "/fake-health"
    return {
        "SMARTOFFERS_QA4_API_URL": endpoint,
        "SMARTOFFERS_QA4_API_HEALTH_PATH": path,
        "SMARTOFFERS_QA4_API_HEALTH_PATH_SHA256": _sha256(path),
        "SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT": _sha256(endpoint),
    }


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


def _db_result(**overrides):
    result = {
        "execution_id": "execution-ref",
        "timestamp": "2026-08-22T12:05:00+00:00",
        "environment": "qa4",
        "profile": "smartoffers_qa4_full_smoke",
        "attempts_used": 1,
        "retry_count": 0,
        "sensitive_values_logged": False,
        "sanitized_error_category": "NONE",
        "stop_reason": "CHECKPOINT_COMPLETED",
        "environment_allowlist": "MATCH",
        "resource_allowlist": "MATCH",
        "destination_allowlist": "MATCH",
        "query_hash_validation": "MATCH",
        "read_only_validation": "PASS",
        "result_shape_validation": "MATCH",
        "preflight_validation": "MATCH",
        "fingerprint_validation": "MATCH",
    }
    result.update(overrides)
    return result


def _valid_db_records(context=None):
    effective_context = _context() if context is None else context
    raw_results = (
        _db_result(
            checkpoint="ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01",
            resource_id="acm_custom_db",
            profile="smartoffers_basic_smoke",
            status="CONNECT_AND_READ_OK",
        ),
        _db_result(
            checkpoint="ORACLE_ACM_TECHNICAL_READ_ONLY_01",
            resource_id="acm_db",
            status="CONNECT_AND_READ_OK",
        ),
        _db_result(
            checkpoint="ORACLE_BDA_TECHNICAL_READ_ONLY_01",
            resource_id="bda_db",
            status="BDA_DB_CHECKPOINT_OK",
        ),
    )
    return [
        normalize_checkpoint_evidence(
            result, effective_context, evaluated_at=EVALUATED_AT
        )
        for result in raw_results
    ]


def _legacy_statuses():
    return {
        "acm_custom_db_checkpoint_status": "ACM_CUSTOM_DB_CHECKPOINT_OK",
        "acm_db_checkpoint_status": "ACM_DB_CHECKPOINT_OK",
        "bda_db_checkpoint_status": "BDA_DB_CHECKPOINT_OK",
        "basic_db_checkpoint_status": "BASIC_DB_CHECKPOINT_OK",
    }


def _arguments(**overrides):
    arguments = {
        **_request(),
        "method": "GET",
        "attempts": 1,
        "retry": 0,
        "redirects": False,
        "fallback": False,
        "connect_timeout": 5,
        "read_timeout": 5,
        "total_timeout": 15,
        "max_response_bytes": 1024,
        "payload_allowed": False,
        "query_parameters_allowed": False,
        "path_parameters_allowed": False,
        "customer_identifiers_allowed": False,
        "authentication_required": False,
        "db_checkpoint_gates": _valid_db_records(),
        "orchestration_context": _context(),
        "gate_evaluated_at": EVALUATED_AT,
        "operational_window_active": "true",
        "approval": "EXECUTION_APPROVED",
        "operational_release": "OPERATIONAL_EXECUTION_RELEASED",
        "preflight_status": API_RUNTIME_READY,
    }
    arguments.update(overrides)
    return arguments


def test_api_preflight_returns_ready_for_only_the_complete_matching_runtime():
    result = preflight_api_health_local_runtime(_request(), _runtime())

    assert result == {
        "status": API_RUNTIME_READY,
        "checkpoint": API_CHECKPOINT,
        "api_operation_id": API_OPERATION_ID,
        "environment": API_ENVIRONMENT,
        "profile": API_PROFILE,
        "resource_id": API_RESOURCE_ID,
        "allowlist_validation": "MATCH",
        "refs_validation": "READY",
        "path_validation": "MATCH",
        "path_hash_validation": "MATCH",
        "fingerprint_validation": "MATCH",
        "checked_refs": list(API_REQUIRED_REFS),
        "missing_refs": [],
    }


@pytest.mark.parametrize("missing_ref", API_REQUIRED_REFS)
def test_api_preflight_blocks_each_missing_ref(missing_ref):
    runtime = _runtime()
    runtime.pop(missing_ref)

    result = preflight_api_health_local_runtime(_request(), runtime)

    assert result["status"] == API_RUNTIME_BLOCKED
    assert result["refs_validation"] == "BLOCKED"
    assert result["missing_refs"] == [missing_ref]


@pytest.mark.parametrize(
    "request_update",
    (
        {"checkpoint": "WRONG"},
        {"api_operation_id": "wrong-operation"},
        {"environment": "production"},
        {"profile": "smartoffers_basic_smoke"},
        {"resource_id": "wrong-resource"},
    ),
)
def test_api_preflight_blocks_contract_mismatches(request_update):
    result = preflight_api_health_local_runtime(_request(**request_update), _runtime())

    assert result["status"] == API_RUNTIME_BLOCKED
    assert result["allowlist_validation"] == "DENIED"


def test_api_preflight_blocks_path_hash_fingerprint_and_query_divergence():
    path_hash_runtime = _runtime()
    path_hash_runtime["SMARTOFFERS_QA4_API_HEALTH_PATH_SHA256"] = "wrong"
    assert preflight_api_health_local_runtime(_request(), path_hash_runtime)["path_hash_validation"] == "DENIED"

    fingerprint_runtime = _runtime()
    fingerprint_runtime["SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT"] = "wrong"
    assert preflight_api_health_local_runtime(_request(), fingerprint_runtime)["fingerprint_validation"] == "DENIED"

    query_runtime = _runtime()
    query_runtime["SMARTOFFERS_QA4_API_HEALTH_PATH"] = "/fake-health?not=allowed"
    query_runtime["SMARTOFFERS_QA4_API_HEALTH_PATH_SHA256"] = _sha256(
        query_runtime["SMARTOFFERS_QA4_API_HEALTH_PATH"]
    )
    assert preflight_api_health_local_runtime(_request(), query_runtime)["path_validation"] == "DENIED"


def test_api_preflight_has_no_network_or_secret_output_surface():
    source = inspect.getsource(__import__("core.real_execution.api_health_local_runtime_preflight", fromlist=["*"])).lower()
    assert "socket" not in source
    assert "http.client" not in source
    assert "urllib" not in source
    assert "requests" not in source

    result = preflight_api_health_local_runtime(_request(), _runtime())
    serialized = str(result)
    for value in _runtime().values():
        assert value not in serialized


def test_health_operation_catalog_entry_remains_explicitly_blocked():
    entry = get_api_catalog(API_OPERATION_ID)

    assert entry is not None
    assert entry["method"] == "GET"
    assert entry["execution_status"] == "blocked"
    assert entry["safe_for_real_execution"] is False
    assert entry["payload_base"] == {}
    assert is_mock_plannable(API_OPERATION_ID) is False
    assert validate_first_qa4_allowlist({"api_id": API_OPERATION_ID})["valid"] is False


def test_health_checkpoint_documentation_uses_only_contract_refs_and_placeholders():
    document = (
        Path(__file__).resolve().parents[1]
        / "ai"
        / "real-execution"
        / "qa4-api-health-checkpoint-contract.md"
    )
    content = document.read_text(encoding="utf-8")

    for ref in API_REQUIRED_REFS:
        assert ref in content
    assert "<LOCAL_SECRET>" in content
    assert "OPERATIONAL_EXECUTION_RELEASED" in content
    assert "BASIC_DB_CHECKPOINT_OK" in content
    assert "BASIC_SMOKE_OK" in content
    assert "smartoffers_qa4_full_smoke" in content
    assert "OPERATIONAL_WINDOW_ACTIVE" in content
    assert "redirect" in content.lower()
    assert "http://" not in content
    assert "https://" not in content


def test_api_executor_uses_one_fake_get_and_only_sanitized_evidence():
    client = FakeHttpClient(
        FakeResponse(status_code=200, body=b"fake-body", headers={"X-Fake": "secret-header"})
    )
    result = run_api_health_checkpoint(_arguments(), environ=_runtime(), client=client)

    assert result["status"] == API_HEALTH_CHECKPOINT_OK
    assert result["sanitized_error_category"] == "NONE"
    assert result["profile"] == "smartoffers_qa4_full_smoke"
    assert result["allowlist_validation"] == "MATCH"
    assert result["preflight_validation"] == "MATCH"
    assert result["path_validation"] == "MATCH"
    assert result["path_hash_validation"] == "MATCH"
    assert result["fingerprint_validation"] == "MATCH"
    assert result["db_gate_bundle_validation"] == "MATCH"
    assert result["response_body_logged"] is False
    assert result["response_headers_logged"] is False
    assert result["sensitive_values_logged"] is False
    assert len(client.calls) == 1
    assert client.calls[0]["method"] == "GET"
    serialized = str(result)
    for value in _runtime().values():
        assert value not in serialized
    assert "fake-body" not in serialized
    assert "secret-header" not in serialized


@pytest.mark.parametrize(
    "legacy_name",
    (
        "acm_custom_db_checkpoint_status",
        "acm_db_checkpoint_status",
        "bda_db_checkpoint_status",
        "basic_db_checkpoint_status",
    ),
)
def test_api_legacy_checkpoint_statuses_are_optional_and_non_authoritative(
    legacy_name,
):
    client = FakeHttpClient(FakeResponse(status_code=200))

    result = run_api_health_checkpoint(
        _arguments(**{legacy_name: "DENIED"}), environ=_runtime(), client=client
    )

    assert result["status"] == API_HEALTH_CHECKPOINT_OK
    assert len(client.calls) == 1


def _invalid_structured_gate_cases():
    records = _valid_db_records()
    mixed_context = deepcopy(records)
    mixed_context[0]["orchestration_id"] = "historical-run"
    raw_results = deepcopy(records)
    raw_results[0] = _db_result(
        checkpoint="ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01",
        resource_id="acm_custom_db",
        profile="smartoffers_basic_smoke",
        status="CONNECT_AND_READ_OK",
    )
    return (
        [
            "ACM_CUSTOM_DB_CHECKPOINT_OK",
            "ACM_DB_CHECKPOINT_OK",
            "BDA_DB_CHECKPOINT_OK",
        ],
        ["BASIC_DB_CHECKPOINT_OK"],
        [],
        records[:2],
        [records[0], records[0], records[2]],
        raw_results,
        mixed_context,
    )


@pytest.mark.parametrize("gate_input", _invalid_structured_gate_cases())
def test_api_rejects_invalid_structured_or_legacy_gates_before_any_runtime_step(
    gate_input, monkeypatch
):
    called = []

    def load_runtime(environment):
        called.append("runtime")
        return {"endpoint": "https://fake-qa4-api.example", "path": "/fake-health"}

    def validate_preflight(args, environment):
        called.append("preflight")
        return {"fingerprint_validation": "MATCH"}

    def validate_destination(runtime):
        called.append("destination")

    def load_client():
        called.append("client")
        return FakeHttpClient(FakeResponse(status_code=200))

    monkeypatch.setattr(api_health_smoke, "_load_runtime", load_runtime)
    monkeypatch.setattr(api_health_smoke, "_validate_preflight", validate_preflight)
    monkeypatch.setattr(api_health_smoke, "_validate_destination", validate_destination)
    monkeypatch.setattr(api_health_smoke, "_load_real_http_client", load_client)

    result = run_api_health_checkpoint(
        _arguments(
            **_legacy_statuses(),
            db_checkpoint_gates=gate_input,
        ),
        environ=_runtime(),
    )

    assert result["status"] == API_HEALTH_CHECKPOINT_BLOCKED
    assert result["sanitized_error_category"] == "DB_CHECKPOINT_GATE_MISSING"
    assert called == []


def test_api_rejects_expired_structured_gates_before_client_load(monkeypatch):
    loaded = False

    def load_client():
        nonlocal loaded
        loaded = True
        return FakeHttpClient(FakeResponse(status_code=200))

    monkeypatch.setattr(api_health_smoke, "_load_real_http_client", load_client)

    result = run_api_health_checkpoint(
        _arguments(gate_evaluated_at="2026-08-22T12:15:01+00:00"),
        environ=_runtime(),
    )

    assert result["status"] == API_HEALTH_CHECKPOINT_BLOCKED
    assert result["sanitized_error_category"] == "DB_CHECKPOINT_GATE_MISSING"
    assert loaded is False


@pytest.mark.parametrize(
    "argument_update, expected_category",
    (
        ({"operational_window_active": "false"}, "OPERATIONAL_WINDOW_INACTIVE"),
        ({"approval": "DENIED"}, "APPROVAL_MISSING"),
        ({"operational_release": "DENIED"}, "APPROVAL_MISSING"),
        ({"method": "POST"}, "ALLOWLIST_DENIED"),
        ({"attempts": 2}, "READ_ONLY_POLICY_VIOLATION"),
        ({"retry": 1}, "READ_ONLY_POLICY_VIOLATION"),
        ({"connect_timeout": 4}, "READ_ONLY_POLICY_VIOLATION"),
        ({"read_timeout": 4}, "READ_ONLY_POLICY_VIOLATION"),
        ({"total_timeout": 14}, "READ_ONLY_POLICY_VIOLATION"),
        ({"fallback": True}, "READ_ONLY_POLICY_VIOLATION"),
        ({"redirects": True}, "READ_ONLY_POLICY_VIOLATION"),
        ({"payload_allowed": True}, "READ_ONLY_POLICY_VIOLATION"),
        ({"query_parameters_allowed": True}, "READ_ONLY_POLICY_VIOLATION"),
        ({"path_parameters_allowed": True}, "READ_ONLY_POLICY_VIOLATION"),
        ({"customer_identifiers_allowed": True}, "READ_ONLY_POLICY_VIOLATION"),
        ({"authentication_required": True}, "AUTHENTICATION_UNCONFIRMED"),
    ),
)
def test_api_executor_blocks_invalid_gates_and_policy_before_send(argument_update, expected_category):
    client = FakeHttpClient(FakeResponse(status_code=200))
    result = run_api_health_checkpoint(
        _arguments(**argument_update), environ=_runtime(), client=client
    )

    assert result["status"] == API_HEALTH_CHECKPOINT_BLOCKED
    assert result["sanitized_error_category"] == expected_category
    assert client.calls == []


@pytest.mark.parametrize(
    "response, expected_status, expected_category",
    (
        (FakeResponse(status_code=302), API_HEALTH_CHECKPOINT_BLOCKED, "REDIRECT_DENIED"),
        (FakeResponse(status_code=401), API_HEALTH_CHECKPOINT_FAILED, "AUTHENTICATION_ERROR"),
        (FakeResponse(status_code=503), API_HEALTH_CHECKPOINT_FAILED, "HTTP_STATUS_DENIED"),
        (FakeResponse(status_code=200, body=b"x" * 1025), API_HEALTH_CHECKPOINT_FAILED, "RESPONSE_LIMIT_EXCEEDED"),
    ),
)
def test_api_executor_stops_on_transport_or_response_contract_failure(response, expected_status, expected_category):
    client = FakeHttpClient(response)
    result = run_api_health_checkpoint(_arguments(), environ=_runtime(), client=client)

    assert result["status"] == expected_status
    assert result["sanitized_error_category"] == expected_category
    assert len(client.calls) == 1


@pytest.mark.parametrize("error, category", ((TimeoutError(), "TOTAL_TIMEOUT"), (PermissionError(), "AUTHENTICATION_ERROR")))
def test_api_executor_sanitizes_fake_transport_errors(error, category):
    client = FakeHttpClient(error=error)
    result = run_api_health_checkpoint(_arguments(), environ=_runtime(), client=client)

    assert result["status"] == API_HEALTH_CHECKPOINT_FAILED
    assert result["sanitized_error_category"] == category
    assert len(client.calls) == 1


def test_api_executor_requires_matching_preflight_and_never_imports_real_http_before_gates():
    client = FakeHttpClient(FakeResponse(status_code=200))
    result = run_api_health_checkpoint(
        _arguments(preflight_status=API_RUNTIME_BLOCKED), environ=_runtime(), client=client
    )

    assert result["status"] == API_HEALTH_CHECKPOINT_BLOCKED
    assert result["sanitized_error_category"] == "PREFLIGHT_DENIED"
    assert client.calls == []

    source = inspect.getsource(__import__("tools.qa4_api_health_smoke", fromlist=["*"])).lower()
    assert "requests" not in source
    assert "subprocess" not in source
    assert "socket" not in source


@pytest.mark.parametrize(
    "argument_update",
    (
        {"operational_window_active": "false"},
        {"approval": "DENIED"},
        {"operational_release": "DENIED"},
        {"preflight_status": API_RUNTIME_BLOCKED},
    ),
)
def test_api_executor_does_not_load_real_client_or_send_when_any_required_gate_fails(
    argument_update, monkeypatch
):
    loaded = False

    def real_client_loader():
        nonlocal loaded
        loaded = True
        return FakeHttpClient(FakeResponse(status_code=200))

    monkeypatch.setattr(api_health_smoke, "_load_real_http_client", real_client_loader)
    client = FakeHttpClient(FakeResponse(status_code=200))
    result = run_api_health_checkpoint(
        _arguments(**argument_update), environ=_runtime(), client=client
    )

    assert result["status"] == API_HEALTH_CHECKPOINT_BLOCKED
    assert loaded is False
    assert client.calls == []


def test_api_executor_rejects_basic_smoke_ok_as_a_substitute_for_structured_gates():
    args = _arguments(db_checkpoint_gates=None, basic_smoke_status="BASIC_SMOKE_OK")
    client = FakeHttpClient(FakeResponse(status_code=200))

    result = run_api_health_checkpoint(args, environ=_runtime(), client=client)

    assert result["status"] == API_HEALTH_CHECKPOINT_BLOCKED
    assert result["sanitized_error_category"] == "DB_CHECKPOINT_GATE_MISSING"
    assert client.calls == []


@pytest.mark.parametrize(
    "missing_gate, expected_category",
    (
        ("db_checkpoint_gates", "DB_CHECKPOINT_GATE_MISSING"),
        ("orchestration_context", "DB_CHECKPOINT_GATE_MISSING"),
        ("gate_evaluated_at", "DB_CHECKPOINT_GATE_MISSING"),
        ("operational_window_active", "OPERATIONAL_WINDOW_INACTIVE"),
    ),
)
def test_api_executor_blocks_each_missing_operational_gate_before_send(
    missing_gate, expected_category
):
    args = _arguments()
    args.pop(missing_gate)
    client = FakeHttpClient(FakeResponse(status_code=200))

    result = run_api_health_checkpoint(args, environ=_runtime(), client=client)

    assert result["status"] == API_HEALTH_CHECKPOINT_BLOCKED
    assert result["sanitized_error_category"] == expected_category
    assert client.calls == []


@pytest.mark.parametrize("include_legacy", (False, True))
def test_api_executor_cli_legacy_gate_strings_are_optional_and_non_authoritative(
    include_legacy, capsys
):
    arguments = [
            "--checkpoint", API_CHECKPOINT,
            "--api-operation-id", API_OPERATION_ID,
            "--environment", API_ENVIRONMENT,
            "--profile", API_PROFILE,
            "--resource-id", API_RESOURCE_ID,
            "--method", "GET",
            "--attempts", "1",
            "--retry", "0",
            "--redirects", "false",
            "--fallback", "false",
            "--connect-timeout", "5",
            "--read-timeout", "5",
            "--total-timeout", "15",
            "--max-response-bytes", "1024",
            "--payload-allowed", "false",
            "--query-parameters-allowed", "false",
            "--path-parameters-allowed", "false",
            "--customer-identifiers-allowed", "false",
            "--authentication-required", "false",
            "--operational-window-active", "true",
            "--approval", "DENIED",
            "--operational-release", "OPERATIONAL_EXECUTION_RELEASED",
            "--preflight-status", API_RUNTIME_READY,
    ]
    if include_legacy:
        arguments.extend(
            [
                "--acm-custom-db-checkpoint-status", "ACM_CUSTOM_DB_CHECKPOINT_OK",
                "--acm-db-checkpoint-status", "ACM_DB_CHECKPOINT_OK",
                "--bda-db-checkpoint-status", "BDA_DB_CHECKPOINT_OK",
                "--basic-db-checkpoint-status", "BASIC_DB_CHECKPOINT_OK",
            ]
        )

    exit_code = main(arguments)

    output = capsys.readouterr().out.splitlines()
    assert exit_code == 1
    assert len(output) == 1
    assert '"sanitized_error_category": "DB_CHECKPOINT_GATE_MISSING"' in output[0]


def test_api_executor_cli_rejects_the_legacy_basic_smoke_argument(capsys):
    exit_code = main(["--basic-smoke-status", "BASIC_SMOKE_OK"])

    output = capsys.readouterr().out.splitlines()
    assert exit_code == 1
    assert len(output) == 1
    assert '"sanitized_error_category": "CONFIG_MISSING"' in output[0]


def test_api_executor_blocks_runtime_fingerprint_mismatch_before_the_fake_transport():
    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT"] = "wrong-fingerprint"
    client = FakeHttpClient(FakeResponse(status_code=200))

    result = run_api_health_checkpoint(_arguments(), environ=runtime, client=client)

    assert result["status"] == API_HEALTH_CHECKPOINT_BLOCKED
    assert result["sanitized_error_category"] == "FINGERPRINT_DENIED"
    assert client.calls == []


@pytest.mark.parametrize(
    "error, category",
    (
        (FakeConnectTimeout(), "CONNECT_TIMEOUT"),
        (FakeReadTimeout(), "READ_TIMEOUT"),
        (TimeoutError(), "TOTAL_TIMEOUT"),
    ),
)
def test_api_executor_classifies_fake_timeout_categories_without_retry(error, category):
    client = FakeHttpClient(error=error)
    result = run_api_health_checkpoint(_arguments(), environ=_runtime(), client=client)

    assert result["status"] == API_HEALTH_CHECKPOINT_FAILED
    assert result["sanitized_error_category"] == category
    assert len(client.calls) == 1
