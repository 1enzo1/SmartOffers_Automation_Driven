"""Closed fake-only executor for the BDA QA4 technical checkpoint."""

import argparse
import json
import re
import time

from core.real_execution.bda_local_runtime_preflight import (
    BDA_CHECKPOINT,
    BDA_ENVIRONMENT,
    BDA_PROFILE,
    BDA_REQUIRED_REFS,
    BDA_RESOURCE_ID,
    BDA_RUNTIME_READY,
    preflight_bda_local_runtime,
)


API_MODE = "omitted"
BASIC_SMOKE_OK = "BASIC_SMOKE_OK"
APPROVAL = "EXECUTION_APPROVED"
OPERATIONAL_RELEASE = "OPERATIONAL_EXECUTION_RELEASED"

_FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|TRUNCATE|CREATE|ALTER|DROP|GRANT|REVOKE|"
    r"COMMIT|ROLLBACK|EXEC|EXECUTE|BEGIN|DECLARE|CALL|DBMS_|UTL_|LOCK|FOR\s+UPDATE|INTO)\b",
    re.IGNORECASE,
)


class _Blocked(Exception):
    def __init__(self, category, stop_reason="IMMEDIATE_STOP"):
        super().__init__(category)
        self.category = category
        self.stop_reason = stop_reason


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _Blocked("CONFIG_MISSING")


class FakeCursor:
    """Minimal cursor double that never evaluates the supplied query."""

    def __init__(self, rows=None, description=None):
        self.rows = list(rows if rows is not None else [("simulated",), None])
        self.description = description if description is not None else [("technical_check",)]
        self.executed = []
        self.closed = False

    def execute(self, query):
        self.executed.append(query)

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def close(self):
        self.closed = True


class FakeConnection:
    """Minimal connection double with observable cleanup state."""

    def __init__(self, cursor=None):
        if cursor is not None and type(cursor) is not FakeCursor:
            raise TypeError("FakeCursor required")
        self.cursor_instance = cursor or FakeCursor()
        self.cursor_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0
        self.cancel_calls = 0
        self.call_timeout = None

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
    """Closed fake-only driver used by the mock executor and its tests."""

    def __init__(self, connection=None, error=None):
        if connection is not None and type(connection) is not FakeConnection:
            raise TypeError("FakeConnection required")
        self.connection = connection or FakeConnection()
        self.error = error
        self.connect_calls = []

    def connect(self, **kwargs):
        self.connect_calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.connection


def build_parser():
    parser = _ArgumentParser(add_help=False)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--api-mode", required=True)
    parser.add_argument("--attempts", required=True, type=int)
    parser.add_argument("--retry", required=True, type=int)
    parser.add_argument("--connect-timeout", required=True, type=int)
    parser.add_argument("--read-timeout", required=True, type=int)
    parser.add_argument("--total-timeout", required=True, type=int)
    parser.add_argument("--result-limit-rows", required=True, type=int)
    parser.add_argument("--result-limit-columns", required=True, type=int)
    parser.add_argument("--fallback", required=True)
    parser.add_argument("--credential-guessing", required=True)
    parser.add_argument("--alternative-password", required=True)
    parser.add_argument("--basic-smoke-status", required=True)
    parser.add_argument("--preflight-status", required=True)
    parser.add_argument("--approval", required=True)
    parser.add_argument("--operational-window-active", required=True)
    parser.add_argument("--operational-release", required=True)
    return parser


def main(argv=None, environ=None):
    try:
        args = build_parser().parse_args(argv)
        result = run_bda_mock_executor(vars(args), environ=environ)
        exit_code = 0 if result["status"] == "MOCK_EXECUTION_OK" else 1
    except _Blocked as error:
        result = _blocked_result(error.category, error.stop_reason)
        exit_code = 1

    print(json.dumps(result, sort_keys=True))
    return exit_code


def run_bda_mock_executor(arguments, environ=None, driver=None, clock=None, preflight_request=None):
    """Simulate one BDA technical read using only internal fake classes."""
    args = arguments if isinstance(arguments, dict) else {}
    runtime = environ if isinstance(environ, dict) else {}
    monotonic = clock or time.monotonic
    started = monotonic()
    connection = None
    cursor = None
    result = None

    try:
        _validate_arguments(args)
        runtime_data = _load_runtime(runtime)
        _validate_preflight(runtime, preflight_request)
        _ensure_total_timeout(started, args, monotonic)
        query = _validate_read_only_sql(runtime_data["query"])
        _ensure_total_timeout(started, args, monotonic)

        fake_driver = driver if driver is not None else FakeDriver()
        if type(fake_driver) is not FakeDriver:
            raise _Blocked("MOCK_DRIVER_REQUIRED")
        connection = fake_driver.connect(
            user=runtime_data["db_user"],
            password=runtime_data["db_password"],
            dsn=runtime_data["db_dsn"],
            timeout=args["connect_timeout"],
        )
        _ensure_total_timeout(started, args, monotonic, connection)
        connection.call_timeout = args["read_timeout"] * 1000
        cursor = connection.cursor()
        cursor.execute(query)
        _ensure_total_timeout(started, args, monotonic, connection)
        _validate_single_technical_result(cursor)
        _ensure_total_timeout(started, args, monotonic, connection)
        result = _success_result()
    except _Blocked as error:
        result = _blocked_result(error.category, error.stop_reason)
    except Exception as error:
        result = _blocked_result(_classify_fake_error(error))
    finally:
        if connection is not None:
            _close_fake_session(connection, cursor)
        if result is not None and connection is not None:
            result["connection_simulated"] = True
            result["rollback_simulated"] = connection.rollback_calls == 1
            result["resources_closed"] = (
                connection.close_calls == 1 and (cursor is None or cursor.closed)
            )

    return result


def _validate_arguments(args):
    expected = {
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
        "api_mode": API_MODE,
    }
    if any(args.get(name) != value for name, value in expected.items()):
        raise _Blocked("ALLOWLIST_DENIED")
    if args.get("attempts") != 1 or args.get("retry") != 0:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if (
        args.get("connect_timeout") != 5
        or args.get("read_timeout") != 5
        or args.get("total_timeout") != 15
        or args.get("result_limit_rows") != 1
        or args.get("result_limit_columns") != 1
    ):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if any(
        not _is_false(args.get(name))
        for name in ("fallback", "credential_guessing", "alternative_password")
    ):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if (
        args.get("basic_smoke_status") != BASIC_SMOKE_OK
        or args.get("preflight_status") != BDA_RUNTIME_READY
        or args.get("approval") != APPROVAL
        or not _is_true(args.get("operational_window_active"))
        or args.get("operational_release") != OPERATIONAL_RELEASE
    ):
        raise _Blocked("APPROVAL_MISSING")


def _load_runtime(runtime):
    missing = [name for name in BDA_REQUIRED_REFS if not str(runtime.get(name) or "").strip()]
    if missing:
        raise _Blocked("CONFIG_MISSING")
    return {
        "db_dsn": str(runtime["SMARTOFFERS_QA4_BDA_DB_DSN"]),
        "db_user": str(runtime["SMARTOFFERS_QA4_BDA_DB_USER"]),
        "db_password": str(runtime["SMARTOFFERS_QA4_BDA_DB_PASSWORD"]),
        "query": str(runtime["SMARTOFFERS_QA4_BDA_SMOKE_SQL"]),
    }


def _validate_preflight(runtime, preflight_request):
    request = preflight_request if preflight_request is not None else {
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
    }
    result = preflight_bda_local_runtime(request, runtime)
    if result["status"] == BDA_RUNTIME_READY:
        return
    if result["missing_refs"]:
        raise _Blocked("CONFIG_MISSING")
    if result["fingerprint_validation"] == "DENIED":
        raise _Blocked("FINGERPRINT_DENIED")
    if result["sql_hash_validation"] == "DENIED":
        raise _Blocked("SQL_HASH_DENIED")
    raise _Blocked("ALLOWLIST_DENIED")


def _validate_read_only_sql(query):
    normalized = query.strip()
    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip()
    if not normalized or ";" in normalized or "--" in normalized or "/*" in normalized or "*/" in normalized:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if not re.match(r"^SELECT\b", normalized, re.IGNORECASE) or _FORBIDDEN_SQL.search(normalized):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    return normalized


def _validate_single_technical_result(cursor):
    if len(getattr(cursor, "description", ()) or ()) != 1:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if cursor.fetchone() is None:
        raise _Blocked("MOCK_RESULT_EMPTY")
    if cursor.fetchone() is not None:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")


def _ensure_total_timeout(started, args, monotonic, connection=None):
    if monotonic() - started > args["total_timeout"]:
        if connection is not None:
            connection.cancel()
        raise _Blocked("TOTAL_TIMEOUT")


def _close_fake_session(connection, cursor):
    try:
        if cursor is not None:
            cursor.close()
    finally:
        try:
            connection.rollback()
        finally:
            connection.close()


def _is_false(value):
    return value is False or value == "false"


def _is_true(value):
    return value is True or value == "true"


def _classify_fake_error(error):
    return "AUTHENTICATION_ERROR" if getattr(error, "code", None) == 1017 else "MOCK_EXECUTION_ERROR"


def _success_result():
    return {
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
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


def _blocked_result(category, stop_reason="IMMEDIATE_STOP"):
    return {
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
        "status": "MOCK_EXECUTION_BLOCKED",
        "attempts_used": 0,
        "retry_count": 0,
        "connection_simulated": False,
        "real_connection_attempted": False,
        "sql_execution_simulated": False,
        "real_sql_executed": False,
        "rollback_simulated": False,
        "resources_closed": False,
        "sensitive_values_logged": False,
        "sanitized_error_category": category,
        "stop_reason": stop_reason,
    }


if __name__ == "__main__":
    raise SystemExit(main())
