import hashlib
import inspect
import json

import pytest

from tools.qa4_bda_mock_executor import (
    BDA_CHECKPOINT,
    FakeConnection,
    FakeCursor,
    FakeDriver,
    main,
    run_bda_mock_executor,
)


def _sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _runtime(query="SELECT fake_technical_check FROM fake_dual"):
    dsn = "fake-bda-dsn"
    return {
        "SMARTOFFERS_QA4_BDA_DB_DSN": dsn,
        "SMARTOFFERS_QA4_BDA_DB_USER": "fake-bda-user",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD": "fake-bda-password",
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL": query,
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256": _sha256(query.rstrip(";")),
        "SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT": _sha256(dsn),
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-oracle-client-dir",
    }


def _args(**overrides):
    args = {
        "checkpoint": BDA_CHECKPOINT,
        "environment": "qa4",
        "profile": "smartoffers_qa4_full_smoke",
        "resource_id": "bda_db",
        "api_mode": "omitted",
        "attempts": 1,
        "retry": 0,
        "connect_timeout": 5,
        "read_timeout": 5,
        "total_timeout": 15,
        "result_limit_rows": 1,
        "result_limit_columns": 1,
        "fallback": False,
        "credential_guessing": False,
        "alternative_password": False,
        "basic_smoke_status": "BASIC_SMOKE_OK",
        "preflight_status": "BDA_RUNTIME_READY",
        "approval": "EXECUTION_APPROVED",
        "operational_window_active": True,
        "operational_release": "OPERATIONAL_EXECUTION_RELEASED",
    }
    args.update(overrides)
    return args


def test_bda_mock_executor_returns_sanitized_success_after_one_simulation():
    driver = FakeDriver()

    result = run_bda_mock_executor(_args(), environ=_runtime(), driver=driver)

    assert result == {
        "checkpoint": BDA_CHECKPOINT,
        "environment": "qa4",
        "profile": "smartoffers_qa4_full_smoke",
        "resource_id": "bda_db",
        "status": "MOCK_EXECUTION_OK",
        "attempts_used": 1,
        "retry_count": 0,
        "connection_simulated": True,
        "real_connection_attempted": False,
        "sql_execution_simulated": True,
        "real_sql_executed": False,
        "rollback_simulated": True,
        "resources_closed": True,
        "sensitive_values_logged": False,
    }
    assert len(driver.connect_calls) == 1
    assert driver.connection.cursor_calls == 1
    assert len(driver.connection.cursor_instance.executed) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("checkpoint", "ORACLE_ACM_TECHNICAL_READ_ONLY_01"),
        ("environment", "qa3"),
        ("profile", "smartoffers_basic_smoke"),
        ("resource_id", "acm_db"),
        ("api_mode", "enabled"),
        ("attempts", 2),
        ("retry", 1),
        ("connect_timeout", 6),
        ("read_timeout", 6),
        ("total_timeout", 16),
        ("result_limit_rows", 2),
        ("result_limit_columns", 2),
        ("fallback", True),
        ("credential_guessing", True),
        ("alternative_password", True),
        ("basic_smoke_status", "missing"),
        ("preflight_status", "BDA_RUNTIME_BLOCKED"),
        ("approval", "missing"),
        ("operational_window_active", False),
        ("operational_release", "missing"),
    ],
)
def test_bda_mock_executor_blocks_all_contract_and_gate_variants(field, value):
    driver = FakeDriver()

    result = run_bda_mock_executor(_args(**{field: value}), environ=_runtime(), driver=driver)

    assert result["status"] == "MOCK_EXECUTION_BLOCKED"
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "missing_ref",
    [
        "SMARTOFFERS_QA4_BDA_DB_DSN",
        "SMARTOFFERS_QA4_BDA_DB_USER",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD",
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL",
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256",
        "SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    ],
)
def test_bda_mock_executor_blocks_each_missing_bda_ref(missing_ref):
    runtime = _runtime()
    runtime.pop(missing_ref)
    driver = FakeDriver()

    result = run_bda_mock_executor(_args(), environ=runtime, driver=driver)

    assert result["sanitized_error_category"] == "CONFIG_MISSING"
    assert driver.connect_calls == []


@pytest.mark.parametrize("foreign_prefix", ["SMARTOFFERS_QA4_ACM_", "SMARTOFFERS_QA4_ACM_CUSTOM_"])
def test_bda_mock_executor_rejects_acm_and_acm_custom_runtime(foreign_prefix):
    runtime = {
        f"{foreign_prefix}DB_DSN": "fake-foreign-dsn",
        f"{foreign_prefix}DB_USER": "fake-foreign-user",
        f"{foreign_prefix}DB_PASSWORD": "fake-foreign-password",
        f"{foreign_prefix}SMOKE_SQL": "SELECT fake_value FROM fake_dual",
        f"{foreign_prefix}SMOKE_SQL_SHA256": "fake-foreign-hash",
        f"{foreign_prefix}DESTINATION_FINGERPRINT": "fake-foreign-fingerprint",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-oracle-client-dir",
    }
    driver = FakeDriver()

    result = run_bda_mock_executor(_args(), environ=runtime, driver=driver)

    assert result["sanitized_error_category"] == "CONFIG_MISSING"
    assert driver.connect_calls == []


def test_bda_mock_executor_blocks_hash_fingerprint_and_allowlist_denials():
    driver = FakeDriver()
    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256"] = "different-fake-hash"
    assert run_bda_mock_executor(_args(), environ=runtime, driver=driver)["sanitized_error_category"] == "SQL_HASH_DENIED"

    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT"] = "different-fake-fingerprint"
    assert run_bda_mock_executor(_args(), environ=runtime, driver=driver)["sanitized_error_category"] == "FINGERPRINT_DENIED"

    assert run_bda_mock_executor(
        _args(), environ=_runtime(), driver=driver, preflight_request={}
    )["sanitized_error_category"] == "ALLOWLIST_DENIED"


@pytest.mark.parametrize(
    "query",
    [
        "UPDATE fake_table SET fake_value = 1",
        "SELECT fake_value FROM fake_table FOR UPDATE",
        "SELECT 1 FROM fake_dual; SELECT 2 FROM fake_dual",
        "SELECT /* fake */ 1 FROM fake_dual",
    ],
)
def test_bda_mock_executor_blocks_non_read_only_sql(query):
    driver = FakeDriver()

    result = run_bda_mock_executor(_args(), environ=_runtime(query), driver=driver)

    assert result["sanitized_error_category"] == "READ_ONLY_POLICY_VIOLATION"
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "cursor",
    [
        FakeCursor(description=[]),
        FakeCursor(description=[("one",), ("two",)]),
        FakeCursor(rows=[("first",), ("second",), None]),
        FakeCursor(rows=[None]),
    ],
)
def test_bda_mock_executor_blocks_non_single_results_and_closes_resources(cursor):
    connection = FakeConnection(cursor=cursor)
    driver = FakeDriver(connection=connection)

    result = run_bda_mock_executor(_args(), environ=_runtime(), driver=driver)

    assert result["status"] == "MOCK_EXECUTION_BLOCKED"
    assert len(driver.connect_calls) == 1
    assert connection.rollback_calls == 1
    assert connection.close_calls == 1
    assert cursor.closed is True


def test_bda_mock_executor_timeout_stops_and_closes_resources():
    connection = FakeConnection()
    driver = FakeDriver(connection=connection)
    ticks = iter([0, 0, 0, 0, 16])

    result = run_bda_mock_executor(
        _args(),
        environ=_runtime(),
        driver=driver,
        clock=lambda: next(ticks),
    )

    assert result["sanitized_error_category"] == "TOTAL_TIMEOUT"
    assert connection.cancel_calls == 1
    assert connection.rollback_calls == 1
    assert connection.close_calls == 1


def test_bda_mock_executor_sanitizes_fake_errors_and_allows_only_fake_driver():
    error = RuntimeError("raw fake credential detail")
    error.code = 1017
    result = run_bda_mock_executor(
        _args(), environ=_runtime(), driver=FakeDriver(error=error)
    )
    assert result["sanitized_error_category"] == "AUTHENTICATION_ERROR"
    assert "raw fake credential detail" not in repr(result)

    result = run_bda_mock_executor(_args(), environ=_runtime(), driver=object())
    assert result["sanitized_error_category"] == "MOCK_DRIVER_REQUIRED"


def test_bda_mock_executor_source_has_no_real_or_legacy_dependencies_or_acm_refs():
    module = __import__("tools.qa4_bda_mock_executor", fromlist=["*"])
    source = inspect.getsource(module).lower()

    for forbidden in (
        "oracledb",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "local_secrets",
        "smartoffers_qa4_acm",
    ):
        assert forbidden not in source


def test_bda_mock_cli_emits_one_sanitized_json_without_runtime_loading(capsys):
    exit_code = main(
        [
            "--checkpoint", BDA_CHECKPOINT,
            "--environment", "qa4",
            "--profile", "smartoffers_qa4_full_smoke",
            "--resource-id", "bda_db",
            "--api-mode", "omitted",
            "--attempts", "1",
            "--retry", "0",
            "--connect-timeout", "5",
            "--read-timeout", "5",
            "--total-timeout", "15",
            "--result-limit-rows", "1",
            "--result-limit-columns", "1",
            "--fallback", "false",
            "--credential-guessing", "false",
            "--alternative-password", "false",
            "--basic-smoke-status", "BASIC_SMOKE_OK",
            "--preflight-status", "BDA_RUNTIME_READY",
            "--approval", "EXECUTION_APPROVED",
            "--operational-window-active", "true",
            "--operational-release", "OPERATIONAL_EXECUTION_RELEASED",
        ]
    )

    output = capsys.readouterr().out.strip().splitlines()
    assert exit_code == 1
    assert len(output) == 1
    assert json.loads(output[0])["sanitized_error_category"] == "CONFIG_MISSING"
