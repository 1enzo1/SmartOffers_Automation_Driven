"""Single-checkpoint BDA QA4 read-only executor with explicit gates."""

import argparse
import importlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone

from core.real_execution.bda_local_runtime_preflight import (
    BDA_CHECKPOINT,
    BDA_ENVIRONMENT,
    BDA_PROFILE,
    BDA_REQUIRED_REFS,
    BDA_RESOURCE_ID,
    BDA_RUNTIME_READY,
    preflight_bda_local_runtime,
)


CHECKPOINT = BDA_CHECKPOINT
ENVIRONMENT = BDA_ENVIRONMENT
PROFILE = BDA_PROFILE
RESOURCE_ID = BDA_RESOURCE_ID
API_MODE = "omitted"
APPROVAL = "EXECUTION_APPROVED"
OPERATIONAL_RELEASE = "OPERATIONAL_EXECUTION_RELEASED"

_FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|TRUNCATE|CREATE|ALTER|DROP|GRANT|REVOKE|"
    r"COMMIT|ROLLBACK|EXEC|EXECUTE|BEGIN|DECLARE|CALL|DBMS_|UTL_|LOCK|FOR\s+UPDATE|INTO)\b",
    re.IGNORECASE,
)


class _Blocked(Exception):
    def __init__(
        self,
        category,
        stop_reason="IMMEDIATE_STOP",
        status="BDA_DB_CHECKPOINT_BLOCKED",
        fingerprint_validation="DENIED",
    ):
        super().__init__(category)
        self.category = category
        self.stop_reason = stop_reason
        self.status = status
        self.fingerprint_validation = fingerprint_validation


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _Blocked("CONFIG_MISSING")


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
    parser.add_argument("--basic-db-checkpoint-status")
    parser.add_argument("--preflight-status", required=True)
    parser.add_argument("--approval", required=True)
    parser.add_argument("--operational-window-active", required=True)
    parser.add_argument("--operational-release", required=True)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        result = run_bda_manual_smoke(vars(args))
        exit_code = 0 if result["status"] == "BDA_DB_CHECKPOINT_OK" else 1
    except _Blocked as error:
        result = _result(
            status=error.status,
            error_category=error.category,
            stop_reason=error.stop_reason,
            elapsed_ms=0,
            fingerprint_validation=error.fingerprint_validation,
        )
        exit_code = 1

    print(json.dumps(result, sort_keys=True))
    return exit_code


def run_bda_manual_smoke(arguments, environ=None, driver=None, clock=None, preflight_request=None):
    """Execute one BDA technical read only after all controls validate."""
    args = arguments if isinstance(arguments, dict) else {}
    environment = environ if environ is not None else os.environ
    monotonic = clock or time.monotonic
    started = monotonic()
    connection = None
    cursor = None
    fingerprint_validation = "DENIED"

    try:
        _validate_arguments(args)
        preflight = _validate_preflight(environment, preflight_request)
        fingerprint_validation = preflight["fingerprint_validation"]
        _ensure_total_timeout(started, args, monotonic)
        runtime = _load_runtime(environment)
        query = _validate_read_only_sql(runtime["query"])
        _ensure_total_timeout(started, args, monotonic)

        oracle_driver = driver or _load_oracle_driver()
        oracle_driver.init_oracle_client(lib_dir=runtime["oracle_client_lib_dir"])
        connection = oracle_driver.connect(
            user=runtime["db_user"],
            password=runtime["db_password"],
            dsn=runtime["db_dsn"],
            tcp_connect_timeout=args["connect_timeout"],
        )
        _ensure_total_timeout(started, args, monotonic, connection)
        connection.call_timeout = args["read_timeout"] * 1000
        cursor = connection.cursor()
        cursor.execute(query)
        _ensure_total_timeout(started, args, monotonic, connection)
        _validate_single_technical_result(cursor)
        _ensure_total_timeout(started, args, monotonic, connection)

        return _result(
            status="BDA_DB_CHECKPOINT_OK",
            error_category="NONE",
            stop_reason="CHECKPOINT_COMPLETED",
            elapsed_ms=_elapsed_ms(started, monotonic),
            environment_allowlist="MATCH",
            resource_allowlist="MATCH",
            destination_allowlist="MATCH",
            query_hash_validation="MATCH",
            read_only_validation="PASS",
            result_shape_validation="MATCH",
            preflight_validation="MATCH",
            fingerprint_validation=fingerprint_validation,
        )
    except _Blocked as error:
        error_fingerprint_validation = (
            error.fingerprint_validation
            if error.fingerprint_validation == "MATCH"
            else fingerprint_validation
        )
        return _result(
            status=error.status,
            error_category=error.category,
            stop_reason=error.stop_reason,
            elapsed_ms=_elapsed_ms(started, monotonic),
            fingerprint_validation=error_fingerprint_validation,
        )
    except Exception as error:
        return _result(
            status="BDA_DB_CHECKPOINT_FAILED",
            error_category=_classify_oracle_error(error),
            stop_reason="IMMEDIATE_STOP",
            elapsed_ms=_elapsed_ms(started, monotonic),
            fingerprint_validation=fingerprint_validation,
        )
    finally:
        if connection is not None:
            _close_read_only_session(connection, cursor)


def _validate_arguments(args):
    expected = {
        "checkpoint": CHECKPOINT,
        "environment": ENVIRONMENT,
        "profile": PROFILE,
        "resource_id": RESOURCE_ID,
        "api_mode": API_MODE,
    }
    if any(args.get(name) != value for name, value in expected.items()):
        raise _Blocked("ALLOWLIST_MISMATCH")
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
        args.get("preflight_status") != BDA_RUNTIME_READY
        or args.get("approval") != APPROVAL
        or not _is_true(args.get("operational_window_active"))
        or args.get("operational_release") != OPERATIONAL_RELEASE
    ):
        raise _Blocked("APPROVAL_MISSING")


def _validate_preflight(environment, preflight_request):
    request = preflight_request if preflight_request is not None else {
        "checkpoint": CHECKPOINT,
        "environment": ENVIRONMENT,
        "profile": PROFILE,
        "resource_id": RESOURCE_ID,
    }
    result = preflight_bda_local_runtime(request, environment)
    if result["status"] == BDA_RUNTIME_READY:
        return result
    if result["missing_refs"]:
        raise _Blocked(
            "CONFIG_MISSING", fingerprint_validation=result["fingerprint_validation"]
        )
    if result["fingerprint_validation"] == "DENIED":
        raise _Blocked("FINGERPRINT_DENIED", fingerprint_validation="DENIED")
    if result["sql_hash_validation"] == "DENIED":
        raise _Blocked(
            "QUERY_HASH_MISMATCH", fingerprint_validation=result["fingerprint_validation"]
        )
    raise _Blocked(
        "ALLOWLIST_MISMATCH", fingerprint_validation=result["fingerprint_validation"]
    )


def _load_runtime(environment):
    missing = [name for name in BDA_REQUIRED_REFS if not str(environment.get(name) or "").strip()]
    if missing:
        raise _Blocked("CONFIG_MISSING")
    return {
        "db_dsn": str(environment["SMARTOFFERS_QA4_BDA_DB_DSN"]),
        "db_user": str(environment["SMARTOFFERS_QA4_BDA_DB_USER"]),
        "db_password": str(environment["SMARTOFFERS_QA4_BDA_DB_PASSWORD"]),
        "oracle_client_lib_dir": str(environment["SMARTOFFERS_ORACLE_CLIENT_LIB_DIR"]),
        "query": str(environment["SMARTOFFERS_QA4_BDA_SMOKE_SQL"]),
    }


def _validate_read_only_sql(query):
    normalized = query.strip()
    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip()
    if not normalized or ";" in normalized or "--" in normalized or "/*" in normalized or "*/" in normalized:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if not re.match(r"^SELECT\b", normalized, re.IGNORECASE):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if _FORBIDDEN_SQL.search(normalized):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    return normalized


def _validate_single_technical_result(cursor):
    if len(getattr(cursor, "description", ()) or ()) != 1:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION", status="BDA_DB_CHECKPOINT_FAILED")
    if cursor.fetchone() is None:
        raise _Blocked("ORACLE_CLIENT_ERROR", status="BDA_DB_CHECKPOINT_FAILED")
    if cursor.fetchone() is not None:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION", status="BDA_DB_CHECKPOINT_FAILED")


def _ensure_total_timeout(started, args, monotonic, connection=None):
    if monotonic() - started > args["total_timeout"]:
        if connection is not None and hasattr(connection, "cancel"):
            connection.cancel()
        status = "BDA_DB_CHECKPOINT_FAILED" if connection is not None else "BDA_DB_CHECKPOINT_BLOCKED"
        raise _Blocked("TOTAL_TIMEOUT", status=status)


def _close_read_only_session(connection, cursor):
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


def _load_oracle_driver():
    return importlib.import_module("oracledb")


def _classify_oracle_error(error):
    code = getattr(error, "code", None)
    if code == 1017:
        return "AUTHENTICATION_ERROR"
    if code in (12170, 12535):
        return "CONNECT_TIMEOUT"
    if code == 1013:
        return "READ_TIMEOUT"
    return "UNCLASSIFIED_ORACLE_ERROR"


def _elapsed_ms(started, monotonic):
    return max(0, int((monotonic() - started) * 1000))


def _result(
    status,
    error_category,
    stop_reason,
    elapsed_ms,
    environment_allowlist="DENIED",
    resource_allowlist="DENIED",
    destination_allowlist="DENIED",
    query_hash_validation="DENIED",
    read_only_validation="DENIED",
    result_shape_validation="DENIED",
    preflight_validation="DENIED",
    fingerprint_validation="DENIED",
):
    return {
        "execution_id": uuid.uuid4().hex,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "environment": ENVIRONMENT,
        "profile": PROFILE,
        "checkpoint": CHECKPOINT,
        "resource_id": RESOURCE_ID,
        "status": status,
        "attempts_used": 1,
        "retry_count": 0,
        "connect_timeout_seconds": 5,
        "read_timeout_seconds": 5,
        "total_timeout_seconds": 15,
        "result_limit_rows": 1,
        "result_limit_columns": 1,
        "elapsed_ms": elapsed_ms,
        "environment_allowlist": environment_allowlist,
        "resource_allowlist": resource_allowlist,
        "destination_allowlist": destination_allowlist,
        "query_hash_validation": query_hash_validation,
        "read_only_validation": read_only_validation,
        "result_shape_validation": result_shape_validation,
        "preflight_validation": preflight_validation,
        "fingerprint_validation": fingerprint_validation,
        "api_checkpoint": "OMITTED",
        "sanitized_error_category": error_category,
        "stop_reason": stop_reason,
        "sensitive_values_logged": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
