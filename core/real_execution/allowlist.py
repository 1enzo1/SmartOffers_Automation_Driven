from core.real_execution.policy import CANDIDATE_QA4_API_ID


FIRST_QA4_ALLOWLIST = {
    CANDIDATE_QA4_API_ID: {
        "api_id": CANDIDATE_QA4_API_ID,
        "method": "POST",
        "environment": "QA4",
        "timeout_seconds": 5,
        "retry_count": 0,
        "status": "conceptual_candidate",
    }
}


def build_first_qa4_allowlist():
    """Return the conceptual first-call allowlist, separate from catalog data."""
    return {
        "allowed_api_ids": [CANDIDATE_QA4_API_ID],
        "items": {api_id: dict(item) for api_id, item in FIRST_QA4_ALLOWLIST.items()},
    }


def validate_first_qa4_allowlist(request, allowlist=None):
    request_data = request if isinstance(request, dict) else {}
    allowlist_data = allowlist if isinstance(allowlist, dict) else build_first_qa4_allowlist()
    items = allowlist_data.get("items") or {}
    api_id = request_data.get("api_id")
    item = items.get(api_id)
    blocked_reasons = []

    if not item:
        blocked_reasons.append("api_not_in_first_qa4_allowlist")
    else:
        if str(request_data.get("method") or "").upper() != item["method"]:
            blocked_reasons.append("method_not_allowlisted")
        if request_data.get("environment") != item["environment"]:
            blocked_reasons.append("environment_not_allowlisted")
        if request_data.get("timeout_seconds") != item["timeout_seconds"]:
            blocked_reasons.append("timeout_not_allowlisted")
        if request_data.get("retry_count") != item["retry_count"]:
            blocked_reasons.append("retry_not_allowlisted")
        if item.get("operation") and request_data.get("operation") != item["operation"]:
            blocked_reasons.append("operation_not_allowlisted")
        if item.get("scenario_id") and request_data.get("scenario_id") != item["scenario_id"]:
            blocked_reasons.append("scenario_not_allowlisted")

    return {
        "valid": not blocked_reasons,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "allowlist_item": _sanitized_item(item),
    }


def _sanitized_item(item):
    if not item:
        return {}
    return {
        "api_id": item["api_id"],
        "method": item["method"],
        "environment": item["environment"],
        "timeout_seconds": item["timeout_seconds"],
        "retry_count": item["retry_count"],
        "status": item["status"],
        "operation": item.get("operation"),
        "scenario_id": item.get("scenario_id"),
        "auth_required": item.get("auth_required", True),
    }
