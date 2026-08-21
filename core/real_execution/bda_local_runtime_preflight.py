"""Sanitized local integrity checks for the QA4 BDA resource."""

import hashlib
import hmac
from os import environ as process_environment


BDA_CHECKPOINT = "ORACLE_BDA_TECHNICAL_READ_ONLY_01"
BDA_ENVIRONMENT = "qa4"
BDA_PROFILE = "smartoffers_qa4_full_smoke"
BDA_RESOURCE_ID = "bda_db"
BDA_RUNTIME_READY = "BDA_RUNTIME_READY"
BDA_RUNTIME_BLOCKED = "BDA_RUNTIME_BLOCKED"

BDA_REQUIRED_REFS = (
    "SMARTOFFERS_QA4_BDA_SMOKE_SQL",
    "SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256",
    "SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT",
    "SMARTOFFERS_QA4_BDA_DB_DSN",
    "SMARTOFFERS_QA4_BDA_DB_USER",
    "SMARTOFFERS_QA4_BDA_DB_PASSWORD",
    "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
)


def preflight_bda_local_runtime(request, environ=None):
    """Return only sanitized BDA readiness metadata without external access."""
    environment = environ if environ is not None else process_environment
    request_data = request if isinstance(request, dict) else {}
    checked_refs = list(BDA_REQUIRED_REFS)
    missing_refs = [
        ref for ref in checked_refs if not _read_ref(environment, ref)
    ]
    allowlist_validation = _allowlist_validation(request_data)
    sql_hash_validation = _sql_hash_validation(environment)
    fingerprint_validation = _fingerprint_validation(environment)

    is_ready = (
        allowlist_validation == "MATCH"
        and not missing_refs
        and sql_hash_validation == "MATCH"
        and fingerprint_validation == "MATCH"
    )

    return {
        "status": BDA_RUNTIME_READY if is_ready else BDA_RUNTIME_BLOCKED,
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
        "allowlist_validation": allowlist_validation,
        "refs_validation": "READY" if not missing_refs else "BLOCKED",
        "sql_hash_validation": sql_hash_validation,
        "fingerprint_validation": fingerprint_validation,
        "checked_refs": checked_refs,
        "missing_refs": missing_refs,
        "connection_allowed": False,
        "sql_execution_allowed": False,
    }


def _allowlist_validation(request):
    expected = {
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
    }
    return "MATCH" if all(request.get(key) == value for key, value in expected.items()) else "DENIED"


def _sql_hash_validation(environment):
    sql = _normalize_sql(_read_ref(environment, "SMARTOFFERS_QA4_BDA_SMOKE_SQL"))
    approved_hash = _read_ref(environment, "SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256")
    if not sql or not approved_hash:
        return "DENIED"
    return "MATCH" if hmac.compare_digest(_sha256(sql), approved_hash) else "DENIED"


def _fingerprint_validation(environment):
    dsn = _normalize_destination(_read_ref(environment, "SMARTOFFERS_QA4_BDA_DB_DSN"))
    approved_fingerprint = _read_ref(
        environment, "SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT"
    )
    if not dsn or not approved_fingerprint:
        return "DENIED"
    return "MATCH" if hmac.compare_digest(_sha256(dsn), approved_fingerprint) else "DENIED"


def _read_ref(environment, name):
    return str(environment.get(name) or "").strip()


def _normalize_sql(value):
    normalized = value.strip()
    if normalized.endswith(";"):
        return normalized[:-1].rstrip()
    return normalized


def _normalize_destination(value):
    return "".join(value.split()).lower()


def _sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
