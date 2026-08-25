import re


REQUIRED_RUNTIME_KEYS = (
    "QA4_HOST_REF",
    "AUTH_REF",
    "SENSITIVE_HEADERS_REF",
    "TEST_PAYLOAD_REF",
    "CORRELATION_ID",
)

REQUIRED_RUNTIME_SECRET_KEYS = (
    "endpoint",
    "auth",
    "headers",
    "body",
    "correlation_id",
)

RAW_VALUE_KEYS = (
    "HOST",
    "TOKEN",
    "SECRET",
    "CREDENTIAL",
    "PASSWORD",
    "PAYLOAD",
    "MSISDN",
    "ACCOUNT",
    "DOCUMENT",
    "DOCUMENTO",
    "BEARER",
    "COOKIE",
    "RESPONSE_BODY",
)

RAW_VALUE_PATTERNS = (
    ("raw_network_address", re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")),
    ("raw_endpoint", re.compile(r"\bhttps?://", re.IGNORECASE)),
    ("raw_auth_material", re.compile(r"\bbearer\b|\bcookie\b", re.IGNORECASE)),
    ("raw_secret_material", re.compile(r"\btoken\b|\bsecret\b|\bcredential\b|\bpassword\b", re.IGNORECASE)),
    ("raw_payload_material", re.compile(r"\bmsisdn\b|\baccount\b|\bdocumento?\b|\breal_payload\b", re.IGNORECASE)),
)


def validate_runtime_contract(runtime, *, auth_required=True):
    """Validate injected runtime references without I/O or mutation."""
    runtime_data = runtime if isinstance(runtime, dict) else {}
    blocked_reasons = []

    for key in REQUIRED_RUNTIME_KEYS:
        if key == "AUTH_REF" and auth_required is False:
            continue
        if not runtime_data.get(key):
            blocked_reasons.append(f"missing_{key.lower()}")

    blocked_reasons.extend(_raw_key_reasons(runtime_data))
    blocked_reasons.extend(_raw_value_reasons(runtime_data))
    blocked_reasons = _dedupe_sorted(blocked_reasons)

    return {
        "valid": not blocked_reasons,
        "blocked_reasons": blocked_reasons,
        "sanitized_runtime": _sanitized_runtime(runtime_data, not blocked_reasons),
    }


def validate_runtime_secrets_contract(runtime_secrets, *, auth_required=True):
    """Validate in-memory runtime material presence without returning values."""
    runtime_data = runtime_secrets if isinstance(runtime_secrets, dict) else {}
    blocked_reasons = []

    for key in REQUIRED_RUNTIME_SECRET_KEYS:
        if key == "auth" and auth_required is False:
            continue
        if not runtime_data.get(key):
            blocked_reasons.append(f"missing_runtime_{key}")

    if runtime_data.get("timeout_seconds") is None:
        blocked_reasons.append("missing_runtime_timeout")

    blocked_reasons = _dedupe_sorted(blocked_reasons)
    return {
        "valid": not blocked_reasons,
        "blocked_reasons": blocked_reasons,
        "sanitized_runtime": {
            "valid": not blocked_reasons,
            "endpoint_present": bool(runtime_data.get("endpoint")),
            "auth_present": bool(runtime_data.get("auth")),
            "headers_present": bool(runtime_data.get("headers")),
            "body_present": bool(runtime_data.get("body")),
            "correlation_reference": _mask_correlation(str(runtime_data.get("correlation_id") or "")),
            "timeout_present": runtime_data.get("timeout_seconds") is not None,
        },
    }


def _raw_key_reasons(runtime_data):
    reasons = []
    for key in runtime_data:
        normalized = str(key).upper()
        if normalized in REQUIRED_RUNTIME_KEYS:
            continue
        if any(raw_key in normalized for raw_key in RAW_VALUE_KEYS):
            reasons.append("raw_runtime_key_detected")
    return reasons


def _raw_value_reasons(runtime_data):
    text = _flatten_text(runtime_data)
    reasons = []
    for reason, pattern in RAW_VALUE_PATTERNS:
        if pattern.search(text):
            reasons.append(reason)
    return reasons


def _flatten_text(value):
    parts = []

    def visit(item):
        if isinstance(item, dict):
            for key in sorted(item):
                parts.append(str(key))
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            for entry in item:
                visit(entry)
        elif item is not None:
            parts.append(str(item))

    visit(value)
    return " ".join(parts)


def _sanitized_runtime(runtime_data, valid):
    correlation = str(runtime_data.get("CORRELATION_ID") or "")
    return {
        "valid": valid,
        "endpoint_reference": bool(runtime_data.get("QA4_HOST_REF")),
        "auth_reference": bool(runtime_data.get("AUTH_REF")),
        "headers_reference": bool(runtime_data.get("SENSITIVE_HEADERS_REF")),
        "body_reference": bool(runtime_data.get("TEST_PAYLOAD_REF")),
        "correlation_reference": _mask_correlation(correlation),
    }


def _mask_correlation(value):
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:3]}***{value[-3:]}"


def _dedupe_sorted(items):
    return sorted(set(item for item in items if item))
