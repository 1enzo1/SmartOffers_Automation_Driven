import re
from copy import deepcopy


EVENT_TIME_PATTERN = re.compile(r"^\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}$")


def analyze_payload_contract(payload):
    """Return a sanitized structural diagnosis for a SmartOffers event payload."""
    if not isinstance(payload, dict):
        return {
            "status": "invalid",
            "classification": "invalid_payload",
            "issues": ["payload_is_not_object"],
            "root_keys": [],
            "attributes_count": 0,
            "attribute_details_count": 0,
            "missing_attribute_details": [],
            "extra_attribute_details": [],
            "has_event_time": False,
            "event_time_shape": "missing",
        }

    attributes = payload.get("attributes")
    attribute_details = payload.get("attributeDetails")

    attributes_map = attributes if isinstance(attributes, dict) else {}
    details_map = attribute_details if isinstance(attribute_details, dict) else {}

    attribute_keys = set(attributes_map)
    detail_keys = set(details_map)
    missing_details = sorted(attribute_keys - detail_keys)
    extra_details = sorted(detail_keys - attribute_keys)

    issues = []
    if not attributes_map:
        issues.append("attributes_missing_or_empty")
    if attribute_keys and not isinstance(attribute_details, dict):
        issues.append("attributeDetails_missing")
    if missing_details:
        issues.append("attribute_metadata_missing")
    if extra_details:
        issues.append("attribute_metadata_without_attribute")

    event_time = payload.get("eventTime")
    event_time_shape = _event_time_shape(event_time)
    if "eventTime" not in payload:
        issues.append("eventTime_missing")
    elif event_time_shape != "dd-mm-yyyy HH:MM:SS":
        issues.append("eventTime_unexpected_shape")

    status = "complete" if not issues else "incomplete"
    classification = "complete_payload" if status == "complete" else _classify_incomplete(issues)

    return {
        "status": status,
        "classification": classification,
        "issues": issues,
        "root_keys": sorted(payload.keys()),
        "attributes_count": len(attributes_map),
        "attribute_details_count": len(details_map),
        "missing_attribute_details": missing_details,
        "extra_attribute_details": extra_details,
        "has_event_time": "eventTime" in payload,
        "event_time_shape": event_time_shape,
    }


def compare_payload_contracts(reference_payload, candidate_payload):
    reference = analyze_payload_contract(reference_payload)
    candidate = analyze_payload_contract(candidate_payload)

    return {
        "reference": reference,
        "candidate": candidate,
        "candidate_is_regression": reference["status"] == "complete"
        and candidate["status"] != "complete",
        "attribute_details_delta": (
            candidate["attribute_details_count"] - reference["attribute_details_count"]
        ),
        "attributes_delta": candidate["attributes_count"] - reference["attributes_count"],
        "event_time_shape_changed": (
            candidate["event_time_shape"] != reference["event_time_shape"]
        ),
    }


def clone_payload(payload):
    return deepcopy(payload)


def _classify_incomplete(issues):
    if "attributeDetails_missing" in issues:
        return "incomplete_missing_attribute_details"
    if "attribute_metadata_missing" in issues:
        return "incomplete_attribute_metadata_gap"
    if "attributes_missing_or_empty" in issues:
        return "incomplete_missing_attributes"
    if "eventTime_missing" in issues:
        return "incomplete_missing_event_time"
    return "incomplete_payload"


def _event_time_shape(value):
    if value is None:
        return "missing"
    if not isinstance(value, str):
        return type(value).__name__
    if EVENT_TIME_PATTERN.match(value):
        return "dd-mm-yyyy HH:MM:SS"
    return "unexpected_string"
