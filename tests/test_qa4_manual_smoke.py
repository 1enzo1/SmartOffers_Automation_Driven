import hashlib
import inspect

import json

import pytest

from tools.qa4_manual_smoke import CHECKPOINT, main, run_manual_smoke


class FakeCursor:
    description = [("technical",)]

    def __init__(self, row=("not-recorded",)):
        self.row = row
        self.executed = []
        self.closed = False

    def execute(self, query):
        self.executed.append(query)

    def fetchone(self):
        return self.row

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

    def cursor(self):
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


def _runtime(query="SELECT 1 FROM dual"):
    return {
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN": "fake-qa4-dsn",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER": "fake-user",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD": "fake-password",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-client-dir",
        "SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL": query,
        "SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256": _sha(query.rstrip(";")),
        "SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT": _sha("fake-qa4-dsn"),
    }


def _args(**overrides):
    args = {
        "checkpoint": CHECKPOINT,
        "environment": "qa4",
        "profile": "smartoffers_basic_smoke",
        "api_mode": "omitted",
        "attempts": 1,
        "retry": 0,
        "connect_timeout": 5,
        "read_timeout": 5,
        "total_timeout": 15,
        "approval": "EXECUTION_APPROVED",
        "operational_release": "OPERATIONAL_EXECUTION_RELEASED",
    }
    args.update(overrides)
    return args


def test_valid_checkpoint_uses_one_connection_cursor_execute_and_rollback():
    driver = FakeDriver()
    result = run_manual_smoke(_args(), environ=_runtime(), driver=driver)

    assert result["status"] == "CONNECT_AND_READ_OK"
    assert len(driver.connect_calls) == 1
    assert driver.connect_calls[0]["tcp_connect_timeout"] == 5
    assert driver.connection.call_timeout == 5000
    assert len(driver.connection.cursor_instance.executed) == 1
    assert driver.connection.rollback_calls == 1
    assert driver.connection.commit_calls == 0
    assert driver.connection.close_calls == 1
    assert "not-recorded" not in repr(result)


@pytest.mark.parametrize(
    "field,value",
    [
        ("environment", "qa3"),
        ("profile", "smartoffers_qa4_full_smoke"),
        ("checkpoint", "other"),
        ("api_mode", "enabled"),
        ("attempts", 2),
        ("retry", 1),
        ("approval", "missing"),
        ("operational_release", "missing"),
    ],
)
def test_invalid_cli_contract_blocks_before_driver(field, value):
    driver = FakeDriver()
    result = run_manual_smoke(_args(**{field: value}), environ=_runtime(), driver=driver)

    assert result["status"] == "BLOCKED"
    assert driver.connect_calls == []
    assert result["environment_allowlist"] == "DENIED"
    assert result["resource_allowlist"] == "DENIED"


def test_destination_and_query_hash_mismatches_block_before_driver():
    driver = FakeDriver()
    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT"] = "different"
    result = run_manual_smoke(_args(), environ=runtime, driver=driver)

    assert result["sanitized_error_category"] == "ALLOWLIST_MISMATCH"
    assert driver.connect_calls == []

    runtime = _runtime()
    runtime["SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256"] = "different"
    result = run_manual_smoke(_args(), environ=runtime, driver=driver)

    assert result["sanitized_error_category"] == "QUERY_HASH_MISMATCH"
    assert driver.connect_calls == []


def test_missing_runtime_ref_blocks_before_driver():
    driver = FakeDriver()
    runtime = _runtime()
    runtime.pop("SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD")

    result = run_manual_smoke(_args(), environ=runtime, driver=driver)

    assert result["sanitized_error_category"] == "CONFIG_MISSING"
    assert driver.connect_calls == []


def test_cli_missing_operational_release_emits_one_sanitized_json(capsys):
    exit_code = main(
        [
            "--checkpoint",
            CHECKPOINT,
            "--environment",
            "qa4",
            "--profile",
            "smartoffers_basic_smoke",
            "--api-mode",
            "omitted",
            "--attempts",
            "1",
            "--retry",
            "0",
            "--connect-timeout",
            "5",
            "--read-timeout",
            "5",
            "--total-timeout",
            "15",
            "--approval",
            "EXECUTION_APPROVED",
        ]
    )

    output = capsys.readouterr().out.strip().splitlines()
    assert exit_code == 1
    assert len(output) == 1
    assert json.loads(output[0])["sanitized_error_category"] == "CONFIG_MISSING"


@pytest.mark.parametrize(
    "query",
    [
        "UPDATE table_name SET value = 1",
        "SELECT 1 FROM dual FOR UPDATE",
        "SELECT 1 FROM dual; SELECT 2 FROM dual",
        "SELECT /*+ hint */ 1 FROM dual",
    ],
)
def test_non_read_only_or_multi_statement_sql_blocks_before_driver(query):
    driver = FakeDriver()
    result = run_manual_smoke(_args(), environ=_runtime(query), driver=driver)

    assert result["sanitized_error_category"] == "READ_ONLY_POLICY_VIOLATION"
    assert driver.connect_calls == []


def test_oracle_authentication_error_is_sanitized():
    error = RuntimeError("raw connection details")
    error.code = 1017
    result = run_manual_smoke(_args(), environ=_runtime(), driver=FakeDriver(error=error))

    assert result["status"] == "BLOCKED"
    assert result["sanitized_error_category"] == "AUTHENTICATION_ERROR"
    assert "raw connection details" not in repr(result)


def test_total_timeout_cancels_and_closes_the_single_connection():
    driver = FakeDriver()
    ticks = iter([0, 0, 0, 16, 16])

    result = run_manual_smoke(
        _args(),
        environ=_runtime(),
        driver=driver,
        clock=lambda: next(ticks),
    )

    assert result["sanitized_error_category"] == "TOTAL_TIMEOUT"
    assert driver.connection.cancel_calls == 1
    assert driver.connection.rollback_calls == 1
    assert driver.connection.close_calls == 1
    assert driver.connection.cursor_instance.executed == []


def test_executor_has_no_http_subprocess_or_legacy_runner_dependencies():
    source = inspect.getsource(run_manual_smoke)
    module_source = inspect.getsource(__import__("tools.qa4_manual_smoke", fromlist=["*"]))

    for forbidden in ("requests", "urllib", "httpx", "subprocess", "kafka", "jenkins"):
        assert forbidden not in source.lower()
        assert forbidden not in module_source.lower()

    for forbidden_ref in (
        "SMARTOFFERS_QA4_ACM_DB_",
        "SMARTOFFERS_QA4_BDA_DB_",
        "SMARTOFFERS_QA4_API_URL",
    ):
        assert forbidden_ref not in module_source
