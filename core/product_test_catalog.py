"""Small user-facing catalog for the safe, product-facing QA4 test flow.

The catalog deliberately separates a locally executable mock from a contract
that can be reviewed locally but has no governed real binding yet.  It is not
an execution allowlist.
"""

from core.api_catalog import get_api_catalog_entry as _get_catalog_entry

PRODUCT_TESTS = (
    {
        "id": "create-customer-basic",
        "name": "Create Customer",
        "description": "Prepares a synthetic QA4 customer through the safe local test flow.",
        "risk_level": "low",
        "environments": ["QA4"],
        "data_requirement": "Automatic synthetic data",
        "execution_mode": "mock",
        "execution_mode_notice": "Local simulation — no QA4 request",
        "validation_strategy": "Local deterministic validation",
        "availability": "READY",
        "execution_available": True,
        "capability_status": "CAPABILITY_EXISTS",
        "evidence_status": "LOCAL_MOCK_SUMMARY",
        "local_mock_working": True,
        "real_contract_ready": False,
        "read_only_validation_ready": False,
        "real_execution_requires_owner_authorization": True,
        "missing_capabilities": [
            "Exact governed create binding",
            "Approved read-only customer or line lookup",
        ],
        "future_read_only_validation_prerequisite": (
            "Approved operation/scenario-scoped customer or line read-only lookup "
            "identity, hash, destination, and result shape."
        ),
    },
    {
        "id": "recharge-basic",
        "name": "Recharge",
        "description": "Reviews the existing recharge contract and creates a safe local plan; no QA4 recharge is sent.",
        "risk_level": "medium",
        "environments": ["QA4"],
        "data_requirement": "Synthetic customer",
        "execution_mode": "static-plan",
        "validation_strategy": "Static contract and mock-plan validation",
        "availability": "CONTRACT_READY",
        "execution_available": False,
        "capability_status": "PARTIAL_CAPABILITY_EXISTS",
        "operation_mapping": "processEvent",
        "api_mapping": "post-evento-de-recarga-6954ef3458",
        "missing_capabilities": ["Governed real binding", "Read-only result validation"],
    },
    {
        "id": "activate-offer-basic",
        "name": "Activate Offer",
        "description": "Reviews the existing offer-change contract and creates a safe local plan; no offer is activated.",
        "risk_level": "medium",
        "environments": ["QA4"],
        "data_requirement": "Synthetic customer and governed offer discovery",
        "execution_mode": "static-plan",
        "validation_strategy": "Static contract and mock-plan validation",
        "availability": "CONTRACT_READY",
        "execution_available": False,
        "capability_status": "LEGACY_CAPABILITY_EXISTS",
        "operation_mapping": "processEvent",
        "api_mapping": "post-o-vivo-next-troca-de-oferta-fedbfb981e",
        "missing_capabilities": ["Governed real binding", "Offer lookup for this operation", "Read-only result validation"],
    },
)


def list_product_tests():
    return [dict(item) for item in PRODUCT_TESTS]


def get_product_test(test_id):
    return next((dict(item) for item in PRODUCT_TESTS if item["id"] == test_id), None)


def validate_contract_plan(test):
    """Validate a catalog-backed local plan without creating a request or binding.

    The selected API catalog is a tracked, sanitized source.  We expose only a
    small, safe preview and reject stale metadata before a caller can treat the
    entry as ready for any kind of execution.
    """
    if test.get("availability") != "CONTRACT_READY":
        return None

    api_mapping = test.get("api_mapping")
    expected_operation = test.get("operation_mapping")
    entry = _get_catalog_entry(api_mapping) if api_mapping else None
    payload = entry.get("payload_base") if isinstance(entry, dict) else None
    operation = payload.get("operation") if isinstance(payload, dict) else None

    if not entry or not expected_operation or operation != expected_operation:
        return {"valid": False, "reason": "CONTRACT_MAPPING_INVALID"}
    if entry.get("method") != "POST" or entry.get("supported_environments") != ["QA4"]:
        return {"valid": False, "reason": "CONTRACT_MAPPING_INVALID"}
    if entry.get("execution_status") != "blocked" or entry.get("safe_for_real_execution") is not False:
        return {"valid": False, "reason": "CONTRACT_POLICY_INVALID"}

    return {
        "valid": True,
        "preview": {
            "api_mapping": api_mapping,
            "operation": operation,
            "method": entry["method"],
            "environment": "QA4",
            "mode": "STATIC_MOCK_PLAN",
        },
    }
