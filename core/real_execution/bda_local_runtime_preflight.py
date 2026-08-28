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
QA4_BDA_OFFER_DISCOVERY = "QA4_BDA_OFFER_DISCOVERY"
OFFER_DISCOVERY_OPERATION = "OFFER_DISCOVERY"
OFFERS_CUSTOMER_OPERATION = "CREATE_OFFERS_CUSTOMER"
SYNTHETIC_OFFERS_SCENARIO = "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4"
QA4_BDA_OFFER_DISCOVERY_QUERY_SHA256 = (
    "7aa86655f68c0473884169f25fbeb77362a7355273a0cb03ef6493473c9bd7bc"
)

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
    offer_discovery_query_hash_validation = _offer_discovery_query_hash_validation(
        request_data
    )
    fingerprint_validation = _fingerprint_validation(environment)

    is_ready = (
        allowlist_validation == "MATCH"
        and not missing_refs
        and sql_hash_validation == "MATCH"
        and fingerprint_validation == "MATCH"
    )
    offer_discovery_allowed = (
        is_ready
        and offer_discovery_query_hash_validation == "MATCH"
        and _offer_discovery_is_authorized(request_data)
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
        "offer_discovery_query_hash_validation": offer_discovery_query_hash_validation,
        "fingerprint_validation": fingerprint_validation,
        "checked_refs": checked_refs,
        "missing_refs": missing_refs,
        "connection_allowed": offer_discovery_allowed,
        "sql_execution_allowed": offer_discovery_allowed,
    }


def _allowlist_validation(request):
    expected = {
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
    }
    return "MATCH" if all(request.get(key) == value for key, value in expected.items()) else "DENIED"


def _offer_discovery_is_authorized(request):
    return (
        request.get("operation") == QA4_BDA_OFFER_DISCOVERY
        and request.get("bda_operation") == OFFER_DISCOVERY_OPERATION
        and request.get("read_only_discovery_authorized") is True
        and request.get("authorization_verified") is True
        and request.get("destination_attestation_ready") is True
        and request.get("offers_operation") == OFFERS_CUSTOMER_OPERATION
        and request.get("scenario_id") == SYNTHETIC_OFFERS_SCENARIO
        and request.get("access_mode") == "READ_ONLY"
        and request.get("attempts_used") == 0
    )


def _offer_discovery_query_hash_validation(request):
    actual_hash = str(request.get("query_hash") or "").strip()
    if not actual_hash:
        return "DENIED"
    return (
        "MATCH"
        if hmac.compare_digest(actual_hash, QA4_BDA_OFFER_DISCOVERY_QUERY_SHA256)
        else "DENIED"
    )


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
