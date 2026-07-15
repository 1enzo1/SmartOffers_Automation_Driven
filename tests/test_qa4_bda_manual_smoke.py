import hashlib
import inspect
import json

import pytest

from tools.qa4_bda_manual_smoke import (
    CHECKPOINT,
    main,
    run_bda_manual_smoke,
)


class FakeCursor:
    def __init__(self, rows=None, description=None, error=None):
        self.rows = list(rows if rows is not None else [("not-recorded",), None])
        self.description = description if description is not None else [("technical",)]
        self.error = error
        self.executed = []
        self.closed = False

    def execute(self, query):
        self.executed.append(query)
        if self.error:
            raise self.error

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
    dsn = "fake-bda-dsn"
    return {
        "SMARTOFFERS_QA4_BDA_DB_DSN": dsn,
        "SMARTOFFERS_QA4_BDA_DB_USER": "fake-bda-user",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD": "fake-bda-password",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-client-dir",
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL": query,
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256": _sha(query.rstrip(";")),
        "SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT": _sha(dsn),
    }


def _args(**overrides):
    args = {
        "checkpoint": CHECKPOINT,
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
        "basic_db_checkpoint_status": "BASIC_DB_CHECKPOINT_OK",
        "preflight_status": "BDA_RUNTIME_READY",
        "approval": "EXECUTION_APPROVED",
        "operational_window_active": True,
        "operational_release": "OPERATIONAL_EXECUTION_RELEASED",
    }
    args.update(overrides)
    return args


def test_bda_contract_uses_one_connection_cursor_execute_and_defensive_rollback():
    driver = FakeDriver()

    result = run_bda_manual_smoke(_args(), environ=_runtime(), driver=driver)

    assert result["status"] == "BDA_DB_CHECKPOINT_OK"
    assert result["sanitized_error_category"] == "NONE"
    assert result["stop_reason"] == "CHECKPOINT_COMPLETED"
    assert len(driver.init_calls) == 1
    assert len(driver.connect_calls) == 1
    assert driver.connection.cursor_calls == 1
    assert len(driver.connection.cursor_instance.executed) == 1
    assert driver.connection.call_timeout == 5000
    assert driver.connection.rollback_calls == 1
    assert driver.connection.commit_calls == 0
    assert driver.connection.close_calls == 1
    assert result["fingerprint_validation"] == "MATCH"
    assert "not-recorded" not in repr(result)


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
        ("basic_db_checkpoint_status", "missing"),
        ("preflight_status", "BDA_RUNTIME_BLOCKED"),
        ("approval", "missing"),
        ("operational_window_active", False),
        ("operational_release", "missing"),
    ],
)
def test_bda_contract_and_all_gates_block_before_driver(field, value):
    driver = FakeDriver()

    result = run_bda_manual_smoke(_args(**{field: value}), environ=_runtime(), driver=driver)

    assert result["status"] == "BDA_DB_CHECKPOINT_BLOCKED"
    assert driver.init_calls == []
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "missing_ref",
    [
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL",
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256",
        "SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT",
        "SMARTOFFERS_QA4_BDA_DB_DSN",
        "SMARTOFFERS_QA4_BDA_DB_USER",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    ],
)
def test_each_missing_bda_ref_blocks_before_driver(missing_ref):
    runtime = _runtime()
    runtime.pop(missing_ref)
    driver = FakeDriver()

    result = run_bda_manual_smoke(_args(), environ=runtime, driver=driver)

    assert result["sanitized_error_category"] == "CONFIG_MISSING"
    assert driver.init_calls == []
    assert driver.connect_calls == []


def test_hash_fingerprint_allowlist_and_foreign_refs_block_before_driver():
    driver = FakeDriver()
    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256"] = "different-fake-hash"
    result = run_bda_manual_smoke(_args(), environ=runtime, driver=driver)
    assert result["sanitized_error_category"] == "QUERY_HASH_MISMATCH"

    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT"] = "different-fake-fingerprint"
    result = run_bda_manual_smoke(_args(), environ=runtime, driver=driver)
    assert result["sanitized_error_category"] == "FINGERPRINT_DENIED"
    assert result["fingerprint_validation"] == "DENIED"

    result = run_bda_manual_smoke(
        _args(), environ=_runtime(), driver=driver, preflight_request={}
    )
    assert result["sanitized_error_category"] == "ALLOWLIST_MISMATCH"

    for prefix in (
        "SMARTOFFERS_QA4_ACM_",
        "SMARTOFFERS_QA4_ACM_CUSTOM_",
        "SMARTOFFERS_QA4_",
    ):
        suffix = "DB_DSN" if prefix == "SMARTOFFERS_QA4_" else "DB_DSN"
        foreign_only = {
            f"{prefix}{suffix}": "fake-foreign-dsn",
            f"{prefix}{suffix.replace('DSN', 'USER')}": "fake-foreign-user",
            f"{prefix}{suffix.replace('DSN', 'PASSWORD')}": "fake-foreign-password",
            "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-client-dir",
        }
        result = run_bda_manual_smoke(_args(), environ=foreign_only, driver=driver)
        assert result["sanitized_error_category"] == "CONFIG_MISSING"

    assert driver.init_calls == []
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "query",
    [
        "UPDATE fake_table SET fake_value = 1",
        "SELECT fake_value FROM fake_table FOR UPDATE",
        "SELECT 1 FROM fake_dual; SELECT 2 FROM fake_dual",
        "SELECT /* fake */ 1 FROM fake_dual",
        "SELECT fake_value INTO fake_target FROM fake_dual",
    ],
)
def test_non_read_only_sql_blocks_before_driver(query):
    driver = FakeDriver()

    result = run_bda_manual_smoke(_args(), environ=_runtime(query), driver=driver)

    assert result["sanitized_error_category"] == "READ_ONLY_POLICY_VIOLATION"
    assert driver.init_calls == []
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "cursor,category",
    [
        (FakeCursor(description=[]), "READ_ONLY_POLICY_VIOLATION"),
        (FakeCursor(description=[("one",), ("two",)]), "READ_ONLY_POLICY_VIOLATION"),
        (FakeCursor(rows=[("first",), ("second",), None]), "READ_ONLY_POLICY_VIOLATION"),
        (FakeCursor(rows=[None]), "ORACLE_CLIENT_ERROR"),
    ],
)
def test_non_single_results_block_and_close_read_only_session(cursor, category):
    connection = FakeConnection(cursor=cursor)
    driver = FakeDriver(connection=connection)

    result = run_bda_manual_smoke(_args(), environ=_runtime(), driver=driver)

    assert result["status"] == "BDA_DB_CHECKPOINT_FAILED"
    assert result["sanitized_error_category"] == category
    assert len(driver.connect_calls) == 1
    assert connection.rollback_calls == 1
    assert connection.close_calls == 1
    assert cursor.closed is True


def test_total_timeout_cancels_and_closes_resources():
    connection = FakeConnection()
    driver = FakeDriver(connection=connection)
    ticks = iter([0, 0, 0, 16, 16])

    result = run_bda_manual_smoke(
        _args(), environ=_runtime(), driver=driver, clock=lambda: next(ticks)
    )

    assert result["sanitized_error_category"] == "TOTAL_TIMEOUT"
    assert connection.cancel_calls == 1
    assert connection.rollback_calls == 1
    assert connection.close_calls == 1


@pytest.mark.parametrize(
    "code,category",
    [(1017, "AUTHENTICATION_ERROR"), (12170, "CONNECT_TIMEOUT"), (12535, "CONNECT_TIMEOUT")],
)
def test_oracle_errors_are_sanitized(code, category):
    error = RuntimeError("raw fake connection detail")
    error.code = code

    result = run_bda_manual_smoke(_args(), environ=_runtime(), driver=FakeDriver(error=error))

    assert result["status"] == "BDA_DB_CHECKPOINT_FAILED"
    assert result["sanitized_error_category"] == category
    assert "raw fake connection detail" not in repr(result)


def test_read_timeout_is_sanitized_and_closes_resources():
    error = RuntimeError("raw fake read detail")
    error.code = 1013
    cursor = FakeCursor(error=error)
    connection = FakeConnection(cursor=cursor)

    result = run_bda_manual_smoke(
        _args(), environ=_runtime(), driver=FakeDriver(connection=connection)
    )

    assert result["status"] == "BDA_DB_CHECKPOINT_FAILED"
    assert result["sanitized_error_category"] == "READ_TIMEOUT"
    assert connection.rollback_calls == 1
    assert connection.close_calls == 1
    assert "raw fake read detail" not in repr(result)


def test_blocked_gate_never_loads_dynamic_driver(monkeypatch):
    module = __import__("tools.qa4_bda_manual_smoke", fromlist=["*"])

    def fail_if_called():
        raise AssertionError("dynamic driver must not load")

    monkeypatch.setattr(module, "_load_oracle_driver", fail_if_called)
    result = run_bda_manual_smoke(
        _args(operational_release="missing"), environ=_runtime()
    )

    assert result["status"] == "BDA_DB_CHECKPOINT_BLOCKED"
    assert result["sanitized_error_category"] == "APPROVAL_MISSING"


def test_execute_error_is_sanitized_and_resources_are_closed():
    cursor = FakeCursor(error=RuntimeError("raw fake SQL detail"))
    connection = FakeConnection(cursor=cursor)

    result = run_bda_manual_smoke(
        _args(), environ=_runtime(), driver=FakeDriver(connection=connection)
    )

    assert result["status"] == "BDA_DB_CHECKPOINT_FAILED"
    assert result["sanitized_error_category"] == "UNCLASSIFIED_ORACLE_ERROR"
    assert "raw fake SQL detail" not in repr(result)
    assert connection.rollback_calls == 1
    assert connection.close_calls == 1


def test_executor_has_no_network_legacy_or_foreign_runtime_dependencies():
    module = __import__("tools.qa4_bda_manual_smoke", fromlist=["*"])
    source = inspect.getsource(module)

    for forbidden in (
        "requests", "urllib", "httpx", "subprocess", "kafka", "jenkins",
        "SMARTOFFERS_QA4_ACM_", "SMARTOFFERS_QA4_ACM_CUSTOM_", "SMARTOFFERS_QA4_DB_",
    ):
        assert forbidden not in source


def test_cli_emits_one_sanitized_json_without_loading_runtime_or_driver(capsys):
    exit_code = main(
        [
            "--checkpoint", CHECKPOINT,
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
            "--basic-db-checkpoint-status", "BASIC_DB_CHECKPOINT_OK",
            "--preflight-status", "BDA_RUNTIME_READY",
            "--approval", "EXECUTION_APPROVED",
            "--operational-window-active", "true",
            "--operational-release", "OPERATIONAL_EXECUTION_RELEASED",
        ]
    )

    output = capsys.readouterr().out.strip().splitlines()
    assert exit_code == 1
    assert len(output) == 1
    payload = json.loads(output[0])
    assert payload["status"] == "BDA_DB_CHECKPOINT_BLOCKED"
    assert payload["sanitized_error_category"] == "CONFIG_MISSING"
