import re


STATUS_ORDER = (
    "mock_allowed",
    "read_only_allowed",
    "future_controlled_required",
    "blocked",
)

STATUS_DETAILS = {
    "mock_allowed": {
        "risk_level": "low",
        "allowed_mode": "mock",
        "safe_next_step": "Continue only with mock planning or local simulation.",
    },
    "read_only_allowed": {
        "risk_level": "medium",
        "allowed_mode": "read-only",
        "safe_next_step": "Review sanitized evidence or catalog data without executing anything.",
    },
    "future_controlled_required": {
        "risk_level": "high",
        "allowed_mode": "none",
        "safe_next_step": "Document future guardrails and keep the action read-only/conceptual.",
    },
    "blocked": {
        "risk_level": "critical",
        "allowed_mode": "none",
        "safe_next_step": "Stop and keep execution blocked until a future approved MVP defines guardrails.",
    },
}

BASE_SUPERVISORS = (
    "adapter-supervisor",
    "safety-supervisor",
)

BLOCKED_PATTERNS = (
    ("mode_real", re.compile(r"\bmode\b[\"']?\s*(?:[=:]\s*)?\breal\b", re.IGNORECASE)),
    (
        "safe_for_real_execution_true",
        re.compile(r"\bsafe_for_real_execution\b[\"']?\s*(?:[=:]\s*)?\btrue\b", re.IGNORECASE),
    ),
    (
        "real_execution_true",
        re.compile(r"\breal_execution\b[\"']?\s*(?:[=:]\s*)?\btrue\b", re.IGNORECASE),
    ),
    ("real_ip", re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")),
    ("real_host", re.compile(r"\bhost\b[\"']?\s*(?:[=:]\s*)?[A-Za-z0-9.-]+\b", re.IGNORECASE)),
    ("real_host", re.compile(r"\breal_host\b", re.IGNORECASE)),
    ("secret", re.compile(r"\bsecret\b", re.IGNORECASE)),
    ("token", re.compile(r"\btoken\b", re.IGNORECASE)),
    ("credential", re.compile(r"\bcredential\b", re.IGNORECASE)),
    ("password", re.compile(r"\bpassword\b", re.IGNORECASE)),
    ("password", re.compile(r"\bsenha\b", re.IGNORECASE)),
    ("real_payload", re.compile(r"\breal_payload\b", re.IGNORECASE)),
    ("real_payload", re.compile(r"\bpayload real\b", re.IGNORECASE)),
    ("external_call", re.compile(r"\bexternal_call(?:s)?\b[\"']?\s*(?:[=:]\s*)?\btrue\b", re.IGNORECASE)),
    ("network_call", re.compile(r"\bnetwork_call(?:s)?\b[\"']?\s*(?:[=:]\s*)?\btrue\b", re.IGNORECASE)),
    ("catalog_mutation", re.compile(r"\bcatalog_mutation\b", re.IGNORECASE)),
    ("catalog_mutation", re.compile(r"\bmutacao de catalogo\b", re.IGNORECASE)),
    ("execution_status_released", re.compile(r"\bexecution_status\b[\"']?\s*(?:[=:]\s*)?\breleased\b", re.IGNORECASE)),
    ("execution_status_released", re.compile(r"\bexecution_status\b[\"']?\s*(?:[=:]\s*)?\ballowed\b", re.IGNORECASE)),
    ("oracle_real", re.compile(r"\boracle\b.*\breal\b|\breal\b.*\boracle\b", re.IGNORECASE)),
    ("api_real", re.compile(r"\bapi\b.*\breal\b|\breal\b.*\bapi\b", re.IGNORECASE)),
    ("kafka_real", re.compile(r"\bkafka\b.*\breal\b|\breal\b.*\bkafka\b", re.IGNORECASE)),
    ("jenkins_real", re.compile(r"\bjenkins\b.*\breal\b|\breal\b.*\bjenkins\b", re.IGNORECASE)),
    ("job_real", re.compile(r"\bjob\b.*\breal\b|\breal\b.*\bjob\b", re.IGNORECASE)),
)

FUTURE_PATTERNS = (
    ("future_controlled", re.compile(r"\bfuture[-_ ]controlled\b", re.IGNORECASE)),
    ("future_controlled", re.compile(r"\bfuturo controlado\b", re.IGNORECASE)),
    ("future_controlled", re.compile(r"\bopt-in futuro\b", re.IGNORECASE)),
    ("kafka_trace_future_controlled", re.compile(r"\bkafka_trace\b", re.IGNORECASE)),
    ("jenkins_job_future_controlled", re.compile(r"\bjenkins\.job\b", re.IGNORECASE)),
)

READ_ONLY_PATTERNS = (
    ("read_only_evidence", re.compile(r"\bread[-_ ]only\b", re.IGNORECASE)),
    ("read_only_evidence", re.compile(r"\bevidence_layer\b", re.IGNORECASE)),
    ("read_only_query", re.compile(r"\bquery\b", re.IGNORECASE)),
)

MOCK_PATTERNS = (
    ("mock_mode", re.compile(r"\bmode\b[\"']?\s*(?:[=:]\s*)?\bmock\b", re.IGNORECASE)),
    ("mock_mode", re.compile(r"\bmock_only\b", re.IGNORECASE)),
    ("mock_mode", re.compile(r"\bplanning_mode\b[\"']?\s*(?:[=:]\s*)?\bmock_only\b", re.IGNORECASE)),
    ("mock_mode", re.compile(r"\bfake-", re.IGNORECASE)),
    ("mock_mode", re.compile(r"\bmocked\b|\bmockado\b", re.IGNORECASE)),
    ("request_plan_mock_only", re.compile(r"\brequest_plan\b", re.IGNORECASE)),
)

BLOCKED_GUARDRAILS = (
    "keep-mode-real-blocked",
    "do-not-call-external-systems",
    "require-future-approved-mvp",
)

FUTURE_GUARDRAILS = (
    "require-explicit-opt-in",
    "require-allowlist-policy",
    "require-sanitized-logs",
    "keep-action-read-only",
)

READ_ONLY_GUARDRAILS = (
    "review-sanitized-input-only",
    "do-not-mutate-state",
)

MOCK_GUARDRAILS = (
    "mock-only",
    "local-only",
)


def classify_adapter_risk(work_item):
    """Classify conceptual adapter risk without I/O, mutation, or execution."""
    if not isinstance(work_item, dict):
        work_item = {}

    text = _flatten_text(work_item)

    blocked_reasons = []
    required_guardrails = []
    related_supervisors = list(BASE_SUPERVISORS)
    statuses = ["mock_allowed"]

    blocked_matches = _match_reasons(text, BLOCKED_PATTERNS)
    future_matches = _match_reasons(text, FUTURE_PATTERNS)
    read_only_matches = _match_reasons(text, READ_ONLY_PATTERNS)
    mock_matches = _match_reasons(text, MOCK_PATTERNS)

    if _dict_status(work_item, "blocked") or _dict_status(work_item, "critical"):
        blocked_matches.append("upstream_blocked_status")

    if blocked_matches:
        statuses.append("blocked")
        blocked_reasons.extend(blocked_matches)
        required_guardrails.extend(BLOCKED_GUARDRAILS)

    if future_matches or _dict_status(work_item, "future-controlled") or _dict_status(
        work_item, "future_controlled_required"
    ):
        statuses.append("future_controlled_required")
        blocked_reasons.extend(future_matches or ["future_controlled_dependency"])
        required_guardrails.extend(FUTURE_GUARDRAILS)

    if read_only_matches or _is_sanitized_catalog_item(work_item):
        statuses.append("read_only_allowed")
        blocked_reasons.extend(read_only_matches)
        required_guardrails.extend(READ_ONLY_GUARDRAILS)
        related_supervisors.extend(("evidence-supervisor", "catalog-config-supervisor"))

    if mock_matches:
        statuses.append("mock_allowed")
        blocked_reasons.extend(mock_matches)
        required_guardrails.extend(MOCK_GUARDRAILS)

    if _has_catalog_or_request_plan_signal(text):
        related_supervisors.append("catalog-config-supervisor")

    if _has_evidence_signal(text):
        related_supervisors.append("evidence-supervisor")

    risk_status = _highest_status(statuses)
    details = STATUS_DETAILS[risk_status]

    return {
        "risk_level": details["risk_level"],
        "risk_status": risk_status,
        "blocked_reasons": _dedupe_ordered(blocked_reasons),
        "allowed_mode": details["allowed_mode"],
        "required_guardrails": _dedupe_ordered(required_guardrails),
        "related_supervisors": _dedupe_ordered(related_supervisors),
        "safe_next_step": details["safe_next_step"],
    }


def _highest_status(statuses):
    rank = {status: index for index, status in enumerate(STATUS_ORDER)}
    return max(statuses, key=lambda status: rank[status])


def _match_reasons(text, patterns):
    reasons = []
    for reason, pattern in patterns:
        if pattern.search(text):
            reasons.append(reason)
    return _dedupe_ordered(reasons)


def _dedupe_ordered(items):
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _flatten_text(value):
    parts = []

    def visit(item):
        if isinstance(item, dict):
            for key in sorted(item):
                parts.append(_text(key))
                visit(item[key])
        elif isinstance(item, list):
            for entry in item:
                visit(entry)
        else:
            parts.append(_text(item))

    visit(value)
    return " ".join(parts)


def _text(value):
    if value is None:
        return ""
    return str(value)


def _dict_status(work_item, status):
    candidates = (
        work_item.get("overall_status"),
        work_item.get("risk_status"),
        work_item.get("status"),
        work_item.get("risk_level"),
    )
    normalized = status.lower().replace("_", "-")
    for candidate in candidates:
        text = _text(candidate).lower().replace("_", "-")
        if text == normalized:
            return True
    return False


def _is_sanitized_catalog_item(work_item):
    return (
        _text(work_item.get("planning_mode")).lower() != "mock_only"
        and work_item.get("execution_status") == "blocked"
        and work_item.get("safe_for_real_execution") is False
    )


def _has_catalog_or_request_plan_signal(text):
    return bool(re.search(r"\bcatalog\b|\brequest_plan\b|\bapi_id\b|\bplanning_mode\b", text, re.IGNORECASE))


def _has_evidence_signal(text):
    return bool(re.search(r"\bevidence\b|\bevidence_layer\b|\bkafka_trace\b", text, re.IGNORECASE))
