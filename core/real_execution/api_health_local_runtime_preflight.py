"""Sanitized local integrity checks for the QA4 SmartOffers API health checkpoint."""

import hashlib
import hmac
from os import environ as process_environment


API_CHECKPOINT = "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01"
API_OPERATION_ID = "smartoffers_api_health_readiness_01"
API_ENVIRONMENT = "qa4"
API_PROFILE = "smartoffers_qa4_full_smoke"
API_RESOURCE_ID = "smartoffers_api"
API_RUNTIME_READY = "API_RUNTIME_READY"
API_RUNTIME_BLOCKED = "API_RUNTIME_BLOCKED"

SCOPED_OFFERS_DESTINATION_ATTESTATION_READY = (
    "QA4_SCOPED_DESTINATION_ATTESTATION_READY"
)
SCOPED_OFFERS_DESTINATION_ATTESTATION_BLOCKED = (
    "QA4_SCOPED_DESTINATION_ATTESTATION_BLOCKED"
)
_SCOPED_OFFERS_REQUEST = {
    "operation": "CREATE_OFFERS_CUSTOMER",
    "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
    "environment": "QA4",
    "api_id": "post-vivo-next-habilitacao-de-cliente-ade0841563",
}

API_REQUIRED_REFS = (
    "SMARTOFFERS_QA4_API_URL",
    "SMARTOFFERS_QA4_API_HEALTH_PATH",
    "SMARTOFFERS_QA4_API_HEALTH_PATH_SHA256",
    "SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT",
)


def preflight_api_health_local_runtime(request, environ=None):
    """Validate opaque API runtime references without resolving or contacting a destination."""
    environment = environ if environ is not None else process_environment
    request_data = request if isinstance(request, dict) else {}
    checked_refs = list(API_REQUIRED_REFS)
    missing_refs = [ref for ref in checked_refs if not _read_ref(environment, ref)]
    allowlist_validation = _allowlist_validation(request_data)
    path_validation = _path_validation(environment)
    path_hash_validation = _path_hash_validation(environment)
    fingerprint_validation = _fingerprint_validation(environment)
    is_ready = (
        allowlist_validation == "MATCH"
        and not missing_refs
        and path_validation == "MATCH"
        and path_hash_validation == "MATCH"
        and fingerprint_validation == "MATCH"
    )

    return {
        "status": API_RUNTIME_READY if is_ready else API_RUNTIME_BLOCKED,
        "checkpoint": API_CHECKPOINT,
        "api_operation_id": API_OPERATION_ID,
        "environment": API_ENVIRONMENT,
        "profile": API_PROFILE,
        "resource_id": API_RESOURCE_ID,
        "allowlist_validation": allowlist_validation,
        "refs_validation": "READY" if not missing_refs else "BLOCKED",
        "path_validation": path_validation,
        "path_hash_validation": path_hash_validation,
        "fingerprint_validation": fingerprint_validation,
        "checked_refs": checked_refs,
        "missing_refs": missing_refs,
    }


def preflight_scoped_qa4_offers_destination_attestation(request, environ=None):
    """Attest only the approved Offers destination, never the generic health route."""
    environment = environ if environ is not None else process_environment
    request_data = request if isinstance(request, dict) else {}
    is_scoped_request = all(
        request_data.get(key) == value for key, value in _SCOPED_OFFERS_REQUEST.items()
    )
    # Reuse the established independent approved-destination binding.  Unlike
    # generic API health, this scoped path deliberately does not require a
    # health path or its hash.
    fingerprint_matches = _fingerprint_validation(environment) == "MATCH"
    if not is_scoped_request or not fingerprint_matches:
        return {
            "status": SCOPED_OFFERS_DESTINATION_ATTESTATION_BLOCKED,
            "attestation": {},
        }
    return {
        "status": SCOPED_OFFERS_DESTINATION_ATTESTATION_READY,
        "attestation": {
            "source": "derived_qa4_api_url",
            **_SCOPED_OFFERS_REQUEST,
            "allowlist_match": True,
            "status": "MATCH",
        },
    }


def _allowlist_validation(request):
    expected = {
        "checkpoint": API_CHECKPOINT,
        "api_operation_id": API_OPERATION_ID,
        "environment": API_ENVIRONMENT,
        "profile": API_PROFILE,
        "resource_id": API_RESOURCE_ID,
    }
    return "MATCH" if all(request.get(key) == value for key, value in expected.items()) else "DENIED"


def _path_validation(environment):
    path = _normalize_path(_read_ref(environment, "SMARTOFFERS_QA4_API_HEALTH_PATH"))
    if not path or not path.startswith("/"):
        return "DENIED"
    if any(marker in path for marker in ("?", "#", "{", "}", "<", ">")):
        return "DENIED"
    return "MATCH"


def _path_hash_validation(environment):
    path = _normalize_path(_read_ref(environment, "SMARTOFFERS_QA4_API_HEALTH_PATH"))
    approved_hash = _read_ref(environment, "SMARTOFFERS_QA4_API_HEALTH_PATH_SHA256")
    if not path or not approved_hash:
        return "DENIED"
    return "MATCH" if hmac.compare_digest(_sha256(path), approved_hash) else "DENIED"


def _fingerprint_validation(environment):
    destination = _normalize_destination(_read_ref(environment, "SMARTOFFERS_QA4_API_URL"))
    approved_fingerprint = _read_ref(
        environment, "SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT"
    )
    if not destination or not approved_fingerprint:
        return "DENIED"
    return "MATCH" if hmac.compare_digest(_sha256(destination), approved_fingerprint) else "DENIED"


def _read_ref(environment, name):
    return str(environment.get(name) or "").strip()


def _normalize_path(value):
    return value.strip()


def _normalize_destination(value):
    return "".join(value.split()).lower()


def _sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
