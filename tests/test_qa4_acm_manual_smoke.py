import hashlib
import inspect
import json

import pytest

from tools.qa4_acm_manual_smoke import (
    CHECKPOINT,
    build_parser,
    main,
    run_acm_manual_smoke,
)


class FakeCursor:
    def __init__(self, rows=None, description=None):
        self.rows = list(rows if rows is not None else [("not-recorded",), None])
        self.description = description if description is not None else [("technical",)]
        self.executed = []
        self.closed = False

    def execute(self, query):
        self.executed.append(query)

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor=None):
        self.cursor_instance = cursor or FakeCursor()
        self.call_timeout = None
        self.rollback_calls = 0
        self.commit_calls = 0
        self.close_calls = 0
        self.cancel_calls = 0
        self.cursor_calls = 0

    def cursor(self):
        self.cursor_calls += 1
        return self.cursor_instance

    def rollback(self):
        self.rollback_calls += 1

    def close(self):
        self.close_calls += 1

    def cancel(self):
        self.cancel_calls += 1


class FakeDriver:
    def __init__(self, connection=None, error=None):
        self.connection = connection or FakeConnection()
        self.error = error
        self.init_calls = []
        self.connect_calls = []

    def init_oracle_client(self, lib_dir):
        self.init_calls.append(lib_dir)

    def connect(self, **kwargs):
        self.connect_calls.append(kwargs)
        if self.error:
            raise self.error
        return self.connection


def _sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _runtime(query="SELECT fake_technical_check FROM fake_dual"):
    dsn = "fake-acm-dsn"
    return {
        "SMARTOFFERS_QA4_ACM_DB_DSN": dsn,
        "SMARTOFFERS_QA4_ACM_DB_USER": "fake-acm-user",
        "SMARTOFFERS_QA4_ACM_DB_PASSWORD": "fake-acm-password",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-client-dir",
        "SMARTOFFERS_QA4_ACM_SMOKE_SQL": query,
        "SMARTOFFERS_QA4_ACM_SMOKE_SQL_SHA256": _sha(query.rstrip(";")),
        "SMARTOFFERS_QA4_ACM_DESTINATION_FINGERPRINT": _sha(dsn),
    }


def _args(**overrides):
    args = {
        "checkpoint": CHECKPOINT,
        "environment": "qa4",
        "profile": "smartoffers_qa4_full_smoke",
        "resource_id": "acm_db",
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
        "approval": "EXECUTION_APPROVED",
        "operational_release": "OPERATIONAL_EXECUTION_RELEASED",
        "preflight_status": "ACM_RUNTIME_READY",
    }
    args.update(overrides)
    return args


def test_acm_contract_uses_one_connection_cursor_execute_and_defensive_rollback():
    driver = FakeDriver()

    result = run_acm_manual_smoke(_args(), environ=_runtime(), driver=driver)

    assert result["status"] == "CONNECT_AND_READ_OK"
    assert len(driver.connect_calls) == 1
    assert driver.connection.cursor_calls == 1
    assert len(driver.connection.cursor_instance.executed) == 1
    assert driver.connection.call_timeout == 5000
    assert driver.connection.rollback_calls == 1
    assert driver.connection.commit_calls == 0
    assert driver.connection.close_calls == 1
    assert result["fingerprint_validation"] == "MATCH"
    assert result["result_shape_validation"] == "MATCH"
    assert result["sensitive_values_logged"] is False
    assert "not-recorded" not in repr(result)


@pytest.mark.parametrize("legacy_value", (None, "DENIED", "BASIC_SMOKE_OK"))
def test_acm_legacy_basic_smoke_value_is_non_authoritative(legacy_value):
    args = _args()
    if legacy_value is not None:
        args["basic_smoke_status"] = legacy_value

    result = run_acm_manual_smoke(args, environ=_runtime(), driver=FakeDriver())

    assert result["status"] == "CONNECT_AND_READ_OK"


def test_acm_parser_keeps_legacy_basic_smoke_option_optional():
    parsed = build_parser().parse_args(
        [
            "--checkpoint", CHECKPOINT,
            "--environment", "qa4",
            "--profile", "smartoffers_qa4_full_smoke",
            "--resource-id", "acm_db",
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
            "--approval", "EXECUTION_APPROVED",
            "--operational-release", "OPERATIONAL_EXECUTION_RELEASED",
            "--preflight-status", "ACM_RUNTIME_READY",
        ]
    )

    assert parsed.basic_smoke_status is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("checkpoint", "ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01"),
        ("environment", "qa3"),
        ("profile", "smartoffers_basic_smoke"),
        ("resource_id", "acm_custom_db"),
        ("api_mode", "enabled"),
        ("attempts", 2),
        ("retry", 1),
        ("connect_timeout", 6),
        ("result_limit_rows", 2),
        ("result_limit_columns", 2),
        ("fallback", True),
        ("credential_guessing", True),
        ("alternative_password", True),
        ("approval", "missing"),
        ("operational_release", "missing"),
        ("preflight_status", "ACM_RUNTIME_BLOCKED"),
    ],
)
def test_acm_contract_and_all_gates_block_before_driver(field, value):
    driver = FakeDriver()

    result = run_acm_manual_smoke(_args(**{field: value}), environ=_runtime(), driver=driver)

    assert result["status"] == "BLOCKED"
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "missing_ref",
    [
        "SMARTOFFERS_QA4_ACM_SMOKE_SQL",
        "SMARTOFFERS_QA4_ACM_SMOKE_SQL_SHA256",
        "SMARTOFFERS_QA4_ACM_DESTINATION_FINGERPRINT",
        "SMARTOFFERS_QA4_ACM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_DB_USER",
        "SMARTOFFERS_QA4_ACM_DB_PASSWORD",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    ],
)
def test_each_missing_acm_ref_blocks_before_driver(missing_ref):
    runtime = _runtime()
    runtime.pop(missing_ref)
    driver = FakeDriver()

    result = run_acm_manual_smoke(_args(), environ=runtime, driver=driver)

    assert result["sanitized_error_category"] == "CONFIG_MISSING"
    assert driver.connect_calls == []


def test_hash_fingerprint_and_acm_custom_refs_block_before_driver():
    driver = FakeDriver()
    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_ACM_SMOKE_SQL_SHA256"] = "different-fake-hash"
    result = run_acm_manual_smoke(_args(), environ=runtime, driver=driver)
    assert result["sanitized_error_category"] == "QUERY_HASH_MISMATCH"
    assert driver.connect_calls == []

    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_ACM_DESTINATION_FINGERPRINT"] = "different-fake-fingerprint"
    result = run_acm_manual_smoke(_args(), environ=runtime, driver=driver)
    assert result["sanitized_error_category"] == "FINGERPRINT_DENIED"
    assert result["fingerprint_validation"] == "DENIED"
    assert driver.connect_calls == []

    custom_only = {
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN": "fake-custom-dsn",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER": "fake-custom-user",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD": "fake-custom-password",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-client-dir",
    }
    result = run_acm_manual_smoke(_args(), environ=custom_only, driver=driver)
    assert result["sanitized_error_category"] == "CONFIG_MISSING"
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "query",
    [
        "UPDATE fake_table SET fake_value = 1",
        "SELECT fake_value FROM fake_table FOR UPDATE",
        "SELECT 1 FROM fake_dual; SELECT 2 FROM fake_dual",
        "SELECT /* fake */ 1 FROM fake_dual",
    ],
)
def test_non_read_only_sql_blocks_before_driver(query):
    driver = FakeDriver()

    result = run_acm_manual_smoke(_args(), environ=_runtime(query), driver=driver)

    assert result["sanitized_error_category"] == "READ_ONLY_POLICY_VIOLATION"
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "cursor",
    [
        FakeCursor(description=[]),
        FakeCursor(description=[("one",), ("two",)]),
        FakeCursor(rows=[("first",), ("second",), None]),
    ],
)
def test_non_single_result_blocks_and_closes_read_only_session(cursor):
    connection = FakeConnection(cursor=cursor)
    driver = FakeDriver(connection=connection)

    result = run_acm_manual_smoke(_args(), environ=_runtime(), driver=driver)

    assert result["sanitized_error_category"] == "READ_ONLY_POLICY_VIOLATION"
    assert len(driver.connect_calls) == 1
    assert connection.rollback_calls == 1
    assert connection.close_calls == 1


def test_zero_rows_blocks_and_closes_read_only_session():
    connection = FakeConnection(cursor=FakeCursor(rows=[None]))
    driver = FakeDriver(connection=connection)

    result = run_acm_manual_smoke(_args(), environ=_runtime(), driver=driver)

    assert result["status"] == "BLOCKED"
    assert result["sanitized_error_category"] == "ORACLE_CLIENT_ERROR"
    assert len(driver.connect_calls) == 1
    assert connection.rollback_calls == 1
    assert connection.close_calls == 1


def test_timeout_authentication_and_unexpected_error_are_sanitized():
    timeout_connection = FakeConnection()
    timeout_driver = FakeDriver(connection=timeout_connection)
    ticks = iter([0, 0, 0, 16, 16])
    result = run_acm_manual_smoke(
        _args(), environ=_runtime(), driver=timeout_driver, clock=lambda: next(ticks)
    )
    assert result["sanitized_error_category"] == "TOTAL_TIMEOUT"
    assert timeout_connection.cancel_calls == 1
    assert timeout_connection.rollback_calls == 1

    error = RuntimeError("raw fake connection detail")
    error.code = 1017
    result = run_acm_manual_smoke(_args(), environ=_runtime(), driver=FakeDriver(error=error))
    assert result["sanitized_error_category"] == "AUTHENTICATION_ERROR"
    assert "raw fake connection detail" not in repr(result)


def test_executor_has_no_network_or_legacy_runner_dependencies_or_custom_refs():
    module = __import__("tools.qa4_acm_manual_smoke", fromlist=["*"])
    source = inspect.getsource(module)

    for forbidden in ("requests", "urllib", "httpx", "subprocess", "kafka", "jenkins"):
        assert forbidden not in source.lower()
    assert "SMARTOFFERS_QA4_ACM_CUSTOM" not in source


def test_missing_preflight_gate_emits_one_sanitized_json_without_loading_driver(capsys):
    exit_code = main(
        [
            "--checkpoint", CHECKPOINT,
            "--environment", "qa4",
            "--profile", "smartoffers_qa4_full_smoke",
            "--resource-id", "acm_db",
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
            "--approval", "EXECUTION_APPROVED",
            "--operational-release", "OPERATIONAL_EXECUTION_RELEASED",
        ]
    )

    output = capsys.readouterr().out.strip().splitlines()
    assert exit_code == 1
    assert len(output) == 1
    assert json.loads(output[0])["sanitized_error_category"] == "CONFIG_MISSING"
