import json
from copy import deepcopy


SMARTOFFERS_PASS = "PASS"
SMARTOFFERS_FAIL = "FAIL"


def analyze_smartoffers_response(response):
    """Classify a SmartOffers response without exposing raw response content."""
    body, location = _extract_response_body(response)

    if not isinstance(body, dict):
        return {
            "status": SMARTOFFERS_FAIL,
            "classification": "invalid_response",
            "issues": ["response_body_is_not_object"],
            "location": location,
            "status_value": None,
            "result_value": None,
            "has_unique_id": False,
        }

    status_value = body.get("status")
    result_value = body.get("result")
    unique_id = body.get("uniqueId")
    event_value = body.get("event")
    indicates_error = status_value == "Error" or result_value is False

    issues = []
    if status_value == "Error":
        issues.append("status_error")
    elif status_value != "Success":
        issues.append("status_not_success")

    if result_value is False:
        issues.append("result_false")
    elif result_value is not True:
        issues.append("result_not_true")

    if not unique_id:
        issues.append("uniqueId_missing")

    if indicates_error and _is_empty(event_value):
        issues.append("event_empty_on_error")

    status = SMARTOFFERS_PASS if not issues else SMARTOFFERS_FAIL
    return {
        "status": status,
        "classification": "functional_success" if status == SMARTOFFERS_PASS else "functional_failure",
        "issues": issues,
        "location": location,
        "status_value": status_value if isinstance(status_value, str) else None,
        "result_value": result_value if isinstance(result_value, bool) else None,
        "has_unique_id": bool(unique_id),
    }


def clone_response(response):
    return deepcopy(response)


def _extract_response_body(response):
    if not isinstance(response, dict):
        return response, "root"

    body = response.get("body")
    if isinstance(body, dict):
        return body, "body"

    if isinstance(body, str):
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return response, "root"
        if isinstance(parsed, dict):
            return parsed, "body"

    return response, "root"


def _is_empty(value):
    return value in (None, "", [], {})
