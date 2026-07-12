"""Single-checkpoint QA4 ACM_CUSTOM smoke executor.

This module performs no work on import. It is intended for a separately
released manual operation and is tested only with injected fake drivers.
"""

import argparse
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone


CHECKPOINT = "ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01"
ENVIRONMENT = "qa4"
PROFILE = "smartoffers_basic_smoke"
RESOURCE_ID = "acm_custom_db"
APPROVAL = "EXECUTION_APPROVED"
OPERATIONAL_RELEASE = "OPERATIONAL_EXECUTION_RELEASED"
API_MODE = "omitted"

_REQUIRED_RUNTIME_REFS = (
    "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
    "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
    "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
    "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    "SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL",
    "SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256",
    "SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT",
)
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


def build_parser():
    parser = _ArgumentParser(add_help=False)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--api-mode", required=True)
    parser.add_argument("--attempts", required=True, type=int)
    parser.add_argument("--retry", required=True, type=int)
    parser.add_argument("--connect-timeout", required=True, type=int)
    parser.add_argument("--read-timeout", required=True, type=int)
    parser.add_argument("--total-timeout", required=True, type=int)
    parser.add_argument("--approval", required=True)
    parser.add_argument("--operational-release", required=True)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        result = run_manual_smoke(vars(args))
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


def run_manual_smoke(arguments, environ=None, driver=None, clock=None):
    """Run exactly one approved read-only checkpoint with an injected driver."""
    args = arguments if isinstance(arguments, dict) else {}
    environment = environ if environ is not None else os.environ
    monotonic = clock or time.monotonic
    started = monotonic()
    connection = None
    cursor = None

    try:
        _validate_arguments(args)
        runtime = _load_runtime(environment)
        _ensure_total_timeout(started, args, monotonic)
        _validate_destination(runtime)
        query = _validate_query(runtime)
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
        if len(getattr(cursor, "description", ()) or ()) != 1:
            raise _Blocked("READ_ONLY_POLICY_VIOLATION")
        if cursor.fetchone() is None:
            raise _Blocked("ORACLE_CLIENT_ERROR")
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
        )
    except _Blocked as error:
        return _result(
            status="BLOCKED",
            error_category=error.category,
            stop_reason=error.stop_reason,
            elapsed_ms=_elapsed_ms(started, monotonic),
        )
    except Exception as error:
        return _result(
            status="BLOCKED",
            error_category=_classify_oracle_error(error),
            stop_reason="IMMEDIATE_STOP",
            elapsed_ms=_elapsed_ms(started, monotonic),
        )
    finally:
        if connection is not None:
            _close_read_only_session(connection, cursor)


def _validate_arguments(args):
    expected = {
        "checkpoint": CHECKPOINT,
        "environment": ENVIRONMENT,
        "profile": PROFILE,
        "api_mode": API_MODE,
        "approval": APPROVAL,
        "operational_release": OPERATIONAL_RELEASE,
    }
    for name, value in expected.items():
        if args.get(name) != value:
            if name in ("approval", "operational_release"):
                raise _Blocked("APPROVAL_MISSING")
            raise _Blocked("ALLOWLIST_MISMATCH")
    if args.get("attempts") != 1:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if args.get("retry") != 0:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if (
        args.get("connect_timeout") != 5
        or args.get("read_timeout") != 5
        or args.get("total_timeout") != 15
    ):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")


def _load_runtime(environment):
    missing = [name for name in _REQUIRED_RUNTIME_REFS if not str(environment.get(name) or "").strip()]
    if missing:
        raise _Blocked("CONFIG_MISSING")
    return {
        "db_dsn": str(environment["SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN"]),
        "db_user": str(environment["SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER"]),
        "db_password": str(environment["SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD"]),
        "oracle_client_lib_dir": str(environment["SMARTOFFERS_ORACLE_CLIENT_LIB_DIR"]),
        "query": str(environment["SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL"]),
        "query_hash": str(environment["SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256"]),
        "destination_fingerprint": str(
            environment["SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT"]
        ),
    }


def _validate_destination(runtime):
    fingerprint = _sha256(_normalize_destination(runtime["db_dsn"]))
    if not hmac.compare_digest(fingerprint, runtime["destination_fingerprint"]):
        raise _Blocked("ALLOWLIST_MISMATCH")


def _validate_query(runtime):
    query = runtime["query"].strip()
    if query.endswith(";"):
        query = query[:-1].rstrip()
    if not query or ";" in query or "--" in query or "/*" in query or "*/" in query:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if not re.match(r"^SELECT\b", query, re.IGNORECASE):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if _FORBIDDEN_SQL.search(query):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if not hmac.compare_digest(_sha256(query), runtime["query_hash"]):
        raise _Blocked("QUERY_HASH_MISMATCH")
    return query


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


def _load_oracle_driver():
    import importlib

    return importlib.import_module("oracledb")


def _normalize_destination(value):
    return "".join(value.split()).lower()


def _sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
        "elapsed_ms": elapsed_ms,
        "environment_allowlist": environment_allowlist,
        "resource_allowlist": resource_allowlist,
        "destination_allowlist": allowlist,
        "query_hash_validation": query_hash_validation,
        "read_only_validation": read_only_validation,
        "api_checkpoint": "OMITTED",
        "sanitized_error_category": error_category,
        "stop_reason": stop_reason,
    }


if __name__ == "__main__":
    raise SystemExit(main())
