import re

from core.risk import classify_adapter_risk


SENSITIVE_KEYWORDS = (
    "host",
    "ip",
    "token",
    "secret",
    "credential",
    "password",
    "senha",
    "real_payload",
    "payload real",
    "msisdn",
    "account",
    "document",
    "documento",
    "bearer",
    "cookie",
    "response_body",
    "raw_response",
)

FALLBACK_PATTERNS = (
    re.compile(r"\bfallback\b.*\bexecution\b", re.IGNORECASE),
    re.compile(r"\bexecucao\b.*\bfallback\b", re.IGNORECASE),
    re.compile(r"\bexecute\b.*\bif\b.*\bfail", re.IGNORECASE),
)

IP_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")


def evaluate_real_execution_readiness(request, policy):
    """Evaluate future real-execution readiness without I/O or side effects."""
    request_data = request if isinstance(request, dict) else {}
    policy_data = policy if isinstance(policy, dict) else {}

    blocked_reasons = []

    if not request_data.get("explicit_opt_in"):
        blocked_reasons.append("missing_explicit_opt_in")

    runtime_flags = policy_data.get("runtime_flags") or {}
    if runtime_flags.get("REAL_EXECUTION_ENABLED") is not True:
        blocked_reasons.append("real_execution_flag_disabled")

    if _kill_switch_active(runtime_flags):
        blocked_reasons.append("kill_switch_active")

    if request_data.get("environment") not in set(policy_data.get("allowed_environments") or []):
        blocked_reasons.append("environment_not_allowed")

    api_id = request_data.get("api_id")
    if api_id not in set(policy_data.get("allowed_api_ids") or []):
        blocked_reasons.append("api_not_allowlisted")

    method = _normalize_method(request_data.get("method"))
    allowed_method = _normalize_method((policy_data.get("allowed_methods_by_api_id") or {}).get(api_id))
    if not method or not allowed_method or method != allowed_method:
        blocked_reasons.append("method_not_allowed")

    if not _valid_timeout(request_data.get("timeout_seconds"), policy_data.get("timeout_limits") or {}):
        blocked_reasons.append("invalid_timeout")

    if request_data.get("retry_count") != policy_data.get("required_retry_count", 0):
        blocked_reasons.append("retry_not_allowed")

    risk_assessment = _risk_assessment(request_data)
    if risk_assessment.get("risk_status") == "blocked":
        blocked_reasons.append("risk_classifier_blocked")

    sensitive_reasons = _sensitive_reasons(request_data)
    blocked_reasons.extend(sensitive_reasons)

    if _has_fallback_execution_signal(request_data):
        blocked_reasons.append("fallback_execution_attempt")

    blocked_reasons = _dedupe_sorted(blocked_reasons)
    decision = "blocked" if blocked_reasons else "ready_for_manual_review"

    return {
        "decision": decision,
        "allowed": decision == "ready_for_manual_review",
        "blocked_reasons": blocked_reasons,
        "required_guardrails": _dedupe_sorted(policy_data.get("required_guardrails") or []),
        "sanitized_log": _sanitized_log(request_data, risk_assessment, decision, blocked_reasons),
        "next_step": _next_step(decision),
        "ready_for_real_call": False,
    }


def _kill_switch_active(runtime_flags):
    return any(
        runtime_flags.get(name) is True
        for name in (
            "REAL_EXECUTION_KILL_SWITCH",
            "KILL_SWITCH_ACTIVE",
            "REAL_EXECUTION_DISABLED",
        )
    )


def _normalize_method(value):
    if value is None:
        return ""
    return str(value).upper()


def _valid_timeout(value, limits):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    min_seconds = limits.get("min_seconds", 1)
    max_seconds = limits.get("max_seconds", 10)
    return min_seconds <= value <= max_seconds


def _risk_assessment(request_data):
    supplied = request_data.get("risk_assessment")
    if isinstance(supplied, dict):
        return supplied
    return classify_adapter_risk(request_data.get("risk_input") or request_data)


def _sensitive_reasons(value):
    text = _flatten_text(value)
    reasons = []
    if IP_PATTERN.search(text):
        reasons.append("sensitive_ip_detected")
    lowered = text.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in lowered:
            reasons.append("sensitive_data_detected")
            break
    return _dedupe_sorted(reasons)


def _has_fallback_execution_signal(value):
    text = _flatten_text(value)
    return any(pattern.search(text) for pattern in FALLBACK_PATTERNS)


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


def _dedupe_sorted(items):
    return sorted(set(item for item in items if item))


def _sanitized_log(request_data, risk_assessment, decision, blocked_reasons):
    return {
        "api_id": request_data.get("api_id"),
        "method": request_data.get("method"),
        "environment": request_data.get("environment"),
        "requested_mode": request_data.get("requested_mode"),
        "decision": decision,
        "blocked_reasons": list(blocked_reasons),
        "risk_status": risk_assessment.get("risk_status"),
        "timeout_seconds": request_data.get("timeout_seconds"),
        "retry_count": request_data.get("retry_count"),
        "ready_for_real_call": False,
    }


def _next_step(decision):
    if decision == "ready_for_manual_review":
        return "Prepare a sanitized human review package; keep execution blocked."
    return "Keep execution blocked and correct readiness preconditions before any future review."
