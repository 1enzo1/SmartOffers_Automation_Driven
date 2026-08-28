"""Small user-facing catalog.  It intentionally describes only safe local work."""

PRODUCT_TESTS = (
    {
        "id": "create-customer-basic",
        "name": "Create Customer",
        "description": "Prepares a synthetic QA4 customer through the safe local test flow.",
        "risk_level": "low",
        "environments": ["QA4"],
        "data_requirement": "Automatic synthetic data",
        "execution_mode": "mock",
        "validation_strategy": "Local deterministic validation",
        "availability": "READY",
    },
    {
        "id": "recharge-basic",
        "name": "Recharge",
        "description": "Capability contract has not been established for this catalog yet.",
        "risk_level": "medium",
        "environments": ["QA4"],
        "data_requirement": "Synthetic customer",
        "execution_mode": "not-ready",
        "validation_strategy": "Not available",
        "availability": "NOT_READY",
    },
    {
        "id": "activate-offer-basic",
        "name": "Activate Offer",
        "description": "Offer activation remains unavailable until its governed contract is ready.",
        "risk_level": "medium",
        "environments": ["QA4"],
        "data_requirement": "Synthetic customer and governed offer discovery",
        "execution_mode": "not-ready",
        "validation_strategy": "Not available",
        "availability": "NOT_READY",
    },
)


def list_product_tests():
    return [dict(item) for item in PRODUCT_TESTS]


def get_product_test(test_id):
    return next((dict(item) for item in PRODUCT_TESTS if item["id"] == test_id), None)
