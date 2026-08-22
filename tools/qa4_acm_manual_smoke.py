"""Single-checkpoint QA4 ACM smoke executor with explicit local gates."""

import argparse
import importlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone

from core.real_execution.acm_local_runtime_preflight import (
    ACM_CHECKPOINT,
    ACM_ENVIRONMENT,
    ACM_PROFILE,
    ACM_RESOURCE_ID,
    ACM_RUNTIME_READY,
    preflight_acm_local_runtime,
)


CHECKPOINT = ACM_CHECKPOINT
ENVIRONMENT = ACM_ENVIRONMENT
PROFILE = ACM_PROFILE
RESOURCE_ID = ACM_RESOURCE_ID
APPROVAL = "EXECUTION_APPROVED"
OPERATIONAL_RELEASE = "OPERATIONAL_EXECUTION_RELEASED"
API_MODE = "omitted"

_REQUIRED_RUNTIME_REFS = (
    "SMARTOFFERS_QA4_ACM_SMOKE_SQL",
    "SMARTOFFERS_QA4_ACM_SMOKE_SQL_SHA256",
    "SMARTOFFERS_QA4_ACM_DESTINATION_FINGERPRINT",
    "SMARTOFFERS_QA4_ACM_DB_DSN",
    "SMARTOFFERS_QA4_ACM_DB_USER",
    "SMARTOFFERS_QA4_ACM_DB_PASSWORD",
    "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
)
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
        fingerprint_validation="DENIED",
    ):
        super().__init__(category)
        self.category = category
        self.stop_reason = stop_reason
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
    parser.add_argument("--basic-smoke-status")
    parser.add_argument("--approval", required=True)
    parser.add_argument("--operational-release", required=True)
    parser.add_argument("--preflight-status", required=True)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        result = run_acm_manual_smoke(vars(args))
        exit_code = 0 if result["status"] == "CONNECT_AND_READ_OK" else 1
    except _Blocked as error:
        result = _result(
            status="BLOCKED",
            error_category=error.category,
            stop_reason=error.stop_reason,
            elapsed_ms=0,
        )
        exit_code = 1

    print(json.dumps(result, sort_keys=True))
    return exit_code


def run_acm_manual_smoke(arguments, environ=None, driver=None, clock=None):
    """Run one ACM checkpoint only after all local gates validate."""
    args = arguments if isinstance(arguments, dict) else {}
    environment = environ if environ is not None else os.environ
    monotonic = clock or time.monotonic
    started = monotonic()
    connection = None
    cursor = None
    fingerprint_validation = "DENIED"

    try:
        _validate_arguments(args)
        runtime = _load_runtime(environment)
        preflight = _validate_preflight(environment)
        fingerprint_validation = preflight["fingerprint_validation"]
        _ensure_total_timeout(started, args, monotonic)
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
            status="CONNECT_AND_READ_OK",
            error_category="NONE",
            stop_reason="CHECKPOINT_COMPLETED",
            elapsed_ms=_elapsed_ms(started, monotonic),
            allowlist="MATCH",
            environment_allowlist="MATCH",
            resource_allowlist="MATCH",
            query_hash_validation="MATCH",
            read_only_validation="PASS",
            preflight_validation="MATCH",
            fingerprint_validation=fingerprint_validation,
            result_shape_validation="MATCH",
        )
    except _Blocked as error:
        error_fingerprint_validation = (
            error.fingerprint_validation
            if error.fingerprint_validation == "MATCH"
            else fingerprint_validation
        )
        return _result(
            status="BLOCKED",
            error_category=error.category,
            stop_reason=error.stop_reason,
            elapsed_ms=_elapsed_ms(started, monotonic),
            fingerprint_validation=error_fingerprint_validation,
        )
    except Exception as error:
        return _result(
            status="BLOCKED",
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
        "approval": APPROVAL,
        "operational_release": OPERATIONAL_RELEASE,
        "preflight_status": ACM_RUNTIME_READY,
    }
    for name, value in expected.items():
        if args.get(name) != value:
            if name in {
                "approval",
                "operational_release",
                "preflight_status",
            }:
                raise _Blocked("APPROVAL_MISSING")
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


def _validate_preflight(environment):
    result = preflight_acm_local_runtime(
        {
            "checkpoint": CHECKPOINT,
            "environment": ENVIRONMENT,
            "profile": PROFILE,
            "resource_id": RESOURCE_ID,
        },
        environment,
    )
    if result["status"] == ACM_RUNTIME_READY:
        return result
    if result["missing_refs"]:
        raise _Blocked(
            "CONFIG_MISSING",
            fingerprint_validation=result["fingerprint_validation"],
        )
    if result["fingerprint_validation"] == "DENIED":
        raise _Blocked("FINGERPRINT_DENIED", fingerprint_validation="DENIED")
    if result["sql_hash_validation"] == "DENIED":
        raise _Blocked(
            "QUERY_HASH_MISMATCH",
            fingerprint_validation=result["fingerprint_validation"],
        )
    raise _Blocked(
        "ALLOWLIST_MISMATCH",
        fingerprint_validation=result["fingerprint_validation"],
    )


def _load_runtime(environment):
    missing = [name for name in _REQUIRED_RUNTIME_REFS if not str(environment.get(name) or "").strip()]
    if missing:
        raise _Blocked("CONFIG_MISSING")
    return {
        "db_dsn": str(environment["SMARTOFFERS_QA4_ACM_DB_DSN"]),
        "db_user": str(environment["SMARTOFFERS_QA4_ACM_DB_USER"]),
        "db_password": str(environment["SMARTOFFERS_QA4_ACM_DB_PASSWORD"]),
        "oracle_client_lib_dir": str(environment["SMARTOFFERS_ORACLE_CLIENT_LIB_DIR"]),
        "query": str(environment["SMARTOFFERS_QA4_ACM_SMOKE_SQL"]),
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
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if cursor.fetchone() is None:
        raise _Blocked("ORACLE_CLIENT_ERROR")
    if cursor.fetchone() is not None:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")


def _ensure_total_timeout(started, args, monotonic, connection=None):
    if monotonic() - started > args["total_timeout"]:
        if connection is not None and hasattr(connection, "cancel"):
            connection.cancel()
        raise _Blocked("TOTAL_TIMEOUT")


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


def _load_oracle_driver():
    return importlib.import_module("oracledb")


def _elapsed_ms(started, monotonic):
    return max(0, int((monotonic() - started) * 1000))


def _classify_oracle_error(error):
    code = getattr(error, "code", None)
    if code == 1017:
        return "AUTHENTICATION_ERROR"
    if code in (12170, 12535):
        return "CONNECT_TIMEOUT"
    return "UNCLASSIFIED_ORACLE_ERROR"


def _result(
    status,
    error_category,
    stop_reason,
    elapsed_ms,
    allowlist="DENIED",
    environment_allowlist="DENIED",
    resource_allowlist="DENIED",
    query_hash_validation="DENIED",
    read_only_validation="DENIED",
    preflight_validation="DENIED",
    fingerprint_validation="DENIED",
    result_shape_validation="DENIED",
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
        "destination_allowlist": allowlist,
        "query_hash_validation": query_hash_validation,
        "read_only_validation": read_only_validation,
        "preflight_validation": preflight_validation,
        "fingerprint_validation": fingerprint_validation,
        "result_shape_validation": result_shape_validation,
        "api_checkpoint": "OMITTED",
        "sanitized_error_category": error_category,
        "stop_reason": stop_reason,
        "sensitive_values_logged": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
