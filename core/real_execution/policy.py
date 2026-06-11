CANDIDATE_QA4_API_ID = "post-consulta-de-saldo-f3317b27b3"

DEFAULT_ALLOWED_ENVIRONMENTS = ("QA4",)
DEFAULT_TIMEOUT_LIMITS = {
    "min_seconds": 1,
    "max_seconds": 10,
}
DEFAULT_REQUIRED_GUARDRAILS = (
    "explicit-opt-in",
    "qa4-only",
    "api-allowlist",
    "method-allowlist",
    "timeout-required",
    "retry-zero",
    "kill-switch-checked",
    "risk-classifier-not-blocked",
    "sanitized-logs",
    "no-real-data-versioned",
)


def build_readiness_policy(
    runtime_flags=None,
    allowed_environments=None,
    allowed_api_ids=None,
    allowed_methods_by_api_id=None,
    timeout_limits=None,
    required_retry_count=0,
    required_guardrails=None,
):
    """Build a deterministic readiness policy from injected values only."""
    return {
        "runtime_flags": dict(runtime_flags or {}),
        "allowed_environments": list(allowed_environments or DEFAULT_ALLOWED_ENVIRONMENTS),
        "allowed_api_ids": list(allowed_api_ids or []),
        "allowed_methods_by_api_id": dict(allowed_methods_by_api_id or {}),
        "timeout_limits": dict(timeout_limits or DEFAULT_TIMEOUT_LIMITS),
        "required_retry_count": required_retry_count,
        "required_guardrails": list(required_guardrails or DEFAULT_REQUIRED_GUARDRAILS),
    }
