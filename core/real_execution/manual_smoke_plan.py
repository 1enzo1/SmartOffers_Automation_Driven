"""Deterministic planning contract for the MVP7.8.3B manual QA4 smoke."""


EXECUTION_APPROVED = "EXECUTION_APPROVED"
EXECUTION_BLOCKED = "EXECUTION_BLOCKED"

_PROFILE_RESOURCES = {
    "smartoffers_basic_smoke": (
        "smartoffers_api",
        "acm_custom_db",
        "oracle_client",
    ),
    "smartoffers_qa4_full_smoke": (
        "smartoffers_api",
        "acm_custom_db",
        "acm_db",
        "bda_db",
        "oracle_client",
    ),
}

_REQUIRED_TIMEOUTS = (
    "connect_timeout_seconds",
    "read_timeout_seconds",
    "total_checkpoint_timeout_seconds",
)
_MANUAL_EXECUTION_MODE = "manual"


def build_manual_smoke_plan(request):
    """Build a sanitized QA4 plan without opening any connection or client."""
    request_data = request if isinstance(request, dict) else {}
    profile = request_data.get("profile")
    blocked_reasons = _planning_blocked_reasons(request_data, profile)
    planning_status = "READY_FOR_ARCHITECT_REVIEW" if not blocked_reasons else "BLOCKED"

    return {
        "mvp": "MVP7.8.3B",
        "execution_type": "manual_real_qa_smoke",
        "environment": request_data.get("environment"),
        "profile": profile,
        "resources": list(_PROFILE_RESOURCES.get(profile, ())),
        "planning_status": planning_status,
        "blocked_reasons": blocked_reasons,
        "execution_decision": EXECUTION_BLOCKED,
        "execution_approval_required": EXECUTION_APPROVED,
        "real_execution_implemented": False,
        "attempts_per_checkpoint": request_data.get("attempts_per_checkpoint"),
        "retry_count": request_data.get("retry_count"),
        "timeouts": _sanitized_timeouts(request_data),
        "stop_on_first_unexpected_error": request_data.get("stop_on_first_unexpected_error") is True,
        "evidence": _sanitized_evidence(profile),
    }


def _planning_blocked_reasons(request_data, profile):
    reasons = []
    allowed_resources = _PROFILE_RESOURCES.get(profile, ())

    if request_data.get("environment") != "qa4":
        reasons.append("environment_not_qa4")
    if profile not in _PROFILE_RESOURCES:
        reasons.append("profile_not_allowlisted")
    if not _requested_resources_match_profile(request_data, allowed_resources):
        reasons.append("resource_allowlist_violation")
    if request_data.get("destination_allowlisted") is not True:
        reasons.append("destination_not_allowlisted")
    if request_data.get("redirect_detected") is not False:
        reasons.append("redirect_not_allowed")
    if request_data.get("execution_mode") != _MANUAL_EXECUTION_MODE:
        reasons.append("execution_mode_not_manual")
    if request_data.get("automated_execution") is not False:
        reasons.append("automated_execution_not_disabled")
    if request_data.get("requested_integrations") not in (None, (), []):
        reasons.append("integration_not_allowlisted")
    if request_data.get("attempts_per_checkpoint") != 1:
        reasons.append("attempts_must_equal_one")
    if request_data.get("retry_count") != 0:
        reasons.append("retry_must_equal_zero")
    if request_data.get("automatic_fallback") is not False:
        reasons.append("automatic_fallback_not_disabled")
    if request_data.get("credential_guessing") is not False:
        reasons.append("credential_guessing_not_disabled")
    if request_data.get("alternative_password_attempt") is not False:
        reasons.append("alternative_password_not_disabled")
    if request_data.get("stop_on_first_unexpected_error") is not True:
        reasons.append("stop_on_error_not_enabled")
    if request_data.get("oracle_access") != "read_only":
        reasons.append("oracle_access_not_read_only")
    if request_data.get("api_payload_mode") != "none":
        reasons.append("api_payload_not_disabled")
    if request_data.get("execution_approval") != EXECUTION_APPROVED:
        reasons.append("execution_approval_missing")

    for name in _REQUIRED_TIMEOUTS:
        value = request_data.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            reasons.append(f"invalid_{name}")

    return sorted(set(reasons))


def _requested_resources_match_profile(request_data, allowed_resources):
    requested_resources = request_data.get("resource_ids")
    if requested_resources is None:
        return True
    if not isinstance(requested_resources, (list, tuple)):
        return False
    return tuple(requested_resources) == allowed_resources


def _sanitized_timeouts(request_data):
    return {name: request_data.get(name) for name in _REQUIRED_TIMEOUTS}


def _sanitized_evidence(profile):
    return {
        "execution_id": "not-issued",
        "timestamp": "not-issued",
        "environment": "qa4",
        "profile": profile,
        "checkpoint": "not-issued",
        "resource_id": "not-issued",
        "status": EXECUTION_BLOCKED,
        "elapsed_ms": None,
        "sanitized_error_category": "not-issued",
        "operator": "not-issued",
        "stop_reason": "execution_not_implemented",
    }
