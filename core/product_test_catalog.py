"""Small user-facing catalog for the safe, product-facing QA4 test flow.

The catalog deliberately separates a locally executable mock from a contract
that can be reviewed locally but has no governed real binding yet.  It is not
an execution allowlist.
"""

from core.api_catalog import get_api_catalog_entry as _get_catalog_entry

PRODUCT_TESTS = (
    {
        "id": "create-customer-basic",
        "name": "Create Customer with Offer",
        "description": "Prepares a synthetic customer-with-offer through the safe local test flow.",
        "risk_level": "low",
        "environments": ["QA4"],
        "data_requirement": "Automatic synthetic data",
        "execution_mode": "mock",
        "execution_mode_notice": "Local simulation - no QA4 request",
        "validation_strategy": "Local deterministic validation",
        "availability": "READY",
        "execution_available": True,
        "capability_status": "CAPABILITY_EXISTS",
        "evidence_status": "LOCAL_MOCK_SUMMARY",
        "local_mock_working": True,
        "real_contract_ready": True,
        "read_only_validation_ready": False,
        "real_execution_requires_owner_authorization": True,
        "missing_capabilities": [
            "Approved read-only customer or line lookup",
        ],
        "future_read_only_validation_prerequisite": (
            "Approved operation/scenario-scoped customer or line read-only lookup "
            "identity, hash, destination, and result shape."
        ),
        "real_operation": "CREATE_OFFERS_CUSTOMER",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "real_execution_status": "REAL EXECUTION CONTRACT READY - AUTHORIZATION REQUIRED",
        "post_execution_validation": "NOT AVAILABLE",
        "real_contract_references": {
            "adapter": "qa4_offers_customer_adapter",
            "bridge": "qa4_real_controlled_bridge",
            "runner": "qa4_standard_mock_runner",
            "ledger": "OneRunAttemptLedger",
            "evidence": "sanitized_evidence",
        },
    },
    {
        "id": "recharge-basic",
        "name": "Recharge Basic",
        "description": "Simulates a prepaid recharge locally and verifies the generated mock request plan; no QA4 recharge is sent.",
        "risk_level": "medium",
        "environments": ["QA4"],
        "data_requirement": "Synthetic customer",
        "execution_mode": "mock",
        "execution_mode_notice": "Local simulation - no QA4 request",
        "validation_strategy": "Local deterministic request-plan validation",
        "availability": "READY",
        "execution_available": True,
        "capability_status": "CAPABILITY_EXISTS",
        "operation_mapping": "processEvent",
        "api_mapping": "post-evento-de-recarga-6954ef3458",
        "local_mock_working": True,
        "real_contract_ready": False,
        "read_only_validation_ready": False,
        "real_execution_requires_owner_authorization": True,
        "missing_capabilities": ["Governed real binding", "Approved read-only result validation"],
    },
    {
        "id": "activate-offer-basic",
        "name": "Add Offer Basic",
        "description": "Offer activation needs a governed operation contract and validated offer input before it can be safely simulated or executed.",
        "risk_level": "medium",
        "environments": ["QA4"],
        "data_requirement": "Synthetic customer and governed offer discovery",
        "execution_mode": "blocked",
        "validation_strategy": "Unavailable until the operation contract and read-only validation are approved",
        "availability": "BLOCKED_EXTERNAL_INFORMATION",
        "execution_available": False,
        "capability_status": "EXTERNAL_INFORMATION_REQUIRED",
        "operation_mapping": "processEvent",
        "api_mapping": "post-o-vivo-next-troca-de-oferta-fedbfb981e",
        "missing_capabilities": [
            "Operation-scoped add-offer contract",
            "Governed offer input or discovery",
            "Approved read-only validation",
        ],
    },
)


def _public_product_test(item):
    """Return a UI-safe catalog projection with ASCII-only notices."""
    test = dict(item)
    if test["id"] == "recharge-basic":
        test["execution_mode_notice"] = "Local simulation - no QA4 request"
    return test


def list_product_tests():
    return [_public_product_test(item) for item in PRODUCT_TESTS]


def get_product_test(test_id):
    item = next((item for item in PRODUCT_TESTS if item["id"] == test_id), None)
    return _public_product_test(item) if item else None


def validate_contract_plan(test):
    """Validate a catalog-backed local plan without creating a request or binding.

    The selected API catalog is a tracked, sanitized source.  We expose only a
    small, safe preview and reject stale metadata before a caller can treat the
    entry as ready for any kind of execution.
    """
    if test.get("availability") not in {"CONTRACT_READY", "READY"}:
        return None

    api_mapping = test.get("api_mapping")
    if not api_mapping:
        return None
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
