"""Bounded, read-only QA4 BDA discovery of a historical Offers product code."""

import hashlib
import time
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from core.real_execution.bda_local_runtime_preflight import (
    BDA_CHECKPOINT,
    BDA_ENVIRONMENT,
    BDA_PROFILE,
    BDA_RESOURCE_ID,
    BDA_RUNTIME_READY,
    preflight_bda_local_runtime,
)


OPERATION = "QA4_BDA_OFFER_DISCOVERY"
_QUERY = (
    "SELECT STEP_ID AS PRODUCT_CODE "
    "FROM BOP_CFG_STEP_DOWN_MAP "
    "WHERE PROMO_CODE IN (856, 869, 888) "
    "AND STEP_ID IS NOT NULL "
    "AND ROWNUM <= 1"
)
_TIMEOUT_SECONDS = 5
_TOTAL_TIMEOUT_SECONDS = 15


class BdaDiscoveryAttemptLedger:
    """Single-use, process-local budget isolated from the Offers request ledger."""

    def __init__(self):
        self._lock = Lock()
        self._consumed = False

    def consume(self, scope):
        with self._lock:
            if scope != OPERATION or self._consumed:
                return False
            self._consumed = True
            return True


class _Blocked(Exception):
    def __init__(self, category, status="QA4_BDA_OFFER_DISCOVERY_BLOCKED"):
        super().__init__(category)
        self.category = category
        self.status = status


def run_qa4_bda_offer_discovery(
    *, environ, driver=None, driver_factory=None, offer_sink=None, authorization=None, clock=None, attempt_ledger=None
):
    """Run the single static BDA SELECT and expose the code only to a local sink."""

    environment = environ if isinstance(environ, dict) else {}
    monotonic = clock or time.monotonic
    started = monotonic()
    connection = None
    cursor = None

    try:
        _validate_runtime(environment, authorization)
        _ensure_total_timeout(started, monotonic)
        runtime = _load_runtime(environment)
        if driver is None and not callable(driver_factory):
            raise _Blocked("EXPLICIT_ORACLE_DRIVER_REQUIRED")
        if attempt_ledger is not None and not _consume_discovery_budget(attempt_ledger):
            raise _Blocked("BDA_DISCOVERY_BUDGET_EXHAUSTED")
        oracle_driver = driver if driver is not None else driver_factory()
        if oracle_driver is None:
            raise _Blocked("EXPLICIT_ORACLE_DRIVER_REQUIRED")
        oracle_driver.init_oracle_client(lib_dir=runtime["oracle_client_lib_dir"])
        connection = oracle_driver.connect(
            user=runtime["db_user"],
            password=runtime["db_password"],
            dsn=runtime["db_dsn"],
            tcp_connect_timeout=_TIMEOUT_SECONDS,
        )
        connection.call_timeout = _TIMEOUT_SECONDS * 1000
        _ensure_total_timeout(started, monotonic, connection)
        cursor = connection.cursor()
        cursor.execute(_QUERY)
        _ensure_total_timeout(started, monotonic, connection)
        offer_code = _read_single_product_code(cursor)
        _ensure_total_timeout(started, monotonic, connection)
        if offer_code is None:
            return _result(
                "QA4_BDA_OFFER_DISCOVERY_NO_MATCH",
                found_valid_offer=False,
                error_category="NO_MATCH",
                elapsed_ms=_elapsed_ms(started, monotonic),
            )
        if callable(offer_sink):
            offer_sink(offer_code)
        return _result(
            "QA4_BDA_OFFER_DISCOVERY_OK",
            found_valid_offer=True,
            error_category="NONE",
            elapsed_ms=_elapsed_ms(started, monotonic),
        )
    except _Blocked as error:
        return _result(
            error.status,
            found_valid_offer=False,
            error_category=error.category,
            elapsed_ms=_elapsed_ms(started, monotonic),
        )
    except Exception as error:
        return _result(
            "QA4_BDA_OFFER_DISCOVERY_FAILED",
            found_valid_offer=False,
            error_category=_classify_oracle_error(error),
            elapsed_ms=_elapsed_ms(started, monotonic),
        )
    finally:
        _close_read_only_session(connection, cursor)


def _validate_runtime(environment, authorization):
    authorization_data = authorization if isinstance(authorization, dict) else {}
    request = {
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
        "operation": authorization_data.get("operation"),
        "bda_operation": authorization_data.get("bda_operation"),
        "read_only_discovery_authorized": authorization_data.get(
            "read_only_discovery_authorized"
        ),
        "authorization_verified": authorization_data.get("authorization_verified"),
        "destination_attestation_ready": authorization_data.get(
            "destination_attestation_ready"
        ),
        "offers_operation": authorization_data.get("offers_operation"),
        "scenario_id": authorization_data.get("scenario_id"),
        "access_mode": authorization_data.get("access_mode"),
        "attempts_used": authorization_data.get("attempts_used"),
        "query_hash": hashlib.sha256(_QUERY.encode("utf-8")).hexdigest(),
    }
    preflight = preflight_bda_local_runtime(request, environment)
    if preflight["offer_discovery_query_hash_validation"] != "MATCH":
        raise _Blocked("QUERY_HASH_MISMATCH")
    if preflight["status"] != BDA_RUNTIME_READY:
        if preflight["missing_refs"]:
            raise _Blocked("CONFIG_MISSING")
        if preflight["fingerprint_validation"] != "MATCH":
            raise _Blocked("FINGERPRINT_DENIED")
        if preflight["sql_hash_validation"] != "MATCH":
            raise _Blocked("QUERY_HASH_MISMATCH")
        raise _Blocked("ALLOWLIST_MISMATCH")
    if not (
        preflight["connection_allowed"] is True
        and preflight["sql_execution_allowed"] is True
    ):
        raise _Blocked("READ_ONLY_DISCOVERY_AUTHORIZATION_REQUIRED")


def _load_runtime(environment):
    required = (
        "SMARTOFFERS_QA4_BDA_DB_DSN",
        "SMARTOFFERS_QA4_BDA_DB_USER",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    )
    if any(not str(environment.get(name) or "").strip() for name in required):
        raise _Blocked("CONFIG_MISSING")
    return {
        "db_dsn": str(environment["SMARTOFFERS_QA4_BDA_DB_DSN"]),
        "db_user": str(environment["SMARTOFFERS_QA4_BDA_DB_USER"]),
        "db_password": str(environment["SMARTOFFERS_QA4_BDA_DB_PASSWORD"]),
        "oracle_client_lib_dir": str(environment["SMARTOFFERS_ORACLE_CLIENT_LIB_DIR"]),
    }


def _consume_discovery_budget(ledger):
    return hasattr(ledger, "consume") and ledger.consume(OPERATION) is True


def _read_single_product_code(cursor):
    if len(getattr(cursor, "description", ()) or ()) != 1:
        raise _Blocked("RESULT_SHAPE_DENIED", status="QA4_BDA_OFFER_DISCOVERY_FAILED")
    row = cursor.fetchone()
    if row is None or len(row) != 1:
        raise _Blocked("RESULT_SHAPE_DENIED", status="QA4_BDA_OFFER_DISCOVERY_FAILED")
    if cursor.fetchone() is not None:
        raise _Blocked("RESULT_SHAPE_DENIED", status="QA4_BDA_OFFER_DISCOVERY_FAILED")
    value = str(row[0] or "").strip()
    return value or None


def _ensure_total_timeout(started, monotonic, connection=None):
    if monotonic() - started > _TOTAL_TIMEOUT_SECONDS:
        if connection is not None and hasattr(connection, "cancel"):
            connection.cancel()
        raise _Blocked("TOTAL_TIMEOUT", status="QA4_BDA_OFFER_DISCOVERY_FAILED")


def _close_read_only_session(connection, cursor):
    try:
        if cursor is not None:
            cursor.close()
    finally:
        if connection is not None:
            try:
                connection.rollback()
            finally:
                connection.close()


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


def _result(status, *, found_valid_offer, error_category, elapsed_ms):
    return {
        "execution_id": uuid4().hex,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "operation": OPERATION,
        "environment": "qa4",
        "resource_id": "bda_db",
        "status": status,
        "found_valid_offer": found_valid_offer,
        "select_only": True,
        "row_limited": True,
        "attempts_used": 1,
        "offers_attempts_used": 0,
        "offers_attempts_available": 1,
        "retry_count": 0,
        "fallback": False,
        "connect_timeout_seconds": _TIMEOUT_SECONDS,
        "read_timeout_seconds": _TIMEOUT_SECONDS,
        "total_timeout_seconds": _TOTAL_TIMEOUT_SECONDS,
        "elapsed_ms": elapsed_ms,
        "sanitized_error_category": error_category,
        "sensitive_values_logged": False,
    }
