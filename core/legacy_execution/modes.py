from core.real_execution.environments import get_sanitized_qa_environment
from core.real_execution.runtime_profiles import (
    get_default_runtime_profile_for_environment,
    get_sanitized_runtime_profile,
    normalize_runtime_profile,
)


EXECUTION_MODE_DRY_RUN = "dry_run"
EXECUTION_MODE_MOCK = "mock"
EXECUTION_MODE_REAL_QA_MANUAL = "real_qa_manual"
DEFAULT_EXECUTION_MODE = EXECUTION_MODE_MOCK
ALLOWED_EXECUTION_MODES = (
    EXECUTION_MODE_DRY_RUN,
    EXECUTION_MODE_MOCK,
    EXECUTION_MODE_REAL_QA_MANUAL,
)


def evaluate_execution_mode_request(
    mode=None,
    environment=None,
    real_confirmed=False,
    runtime_profile=None,
):
    normalized_mode = normalize_execution_mode(mode)
    normalized_environment = normalize_environment(environment)
    normalized_runtime_profile = normalize_runtime_profile(runtime_profile)
    environment_contract = (
        get_sanitized_qa_environment(normalized_environment)
        if normalized_environment
        else None
    )
    runtime_profile_contract = (
        get_sanitized_runtime_profile(normalized_runtime_profile)
        if normalized_runtime_profile
        else None
    )
    blocked_reasons = []

    if normalized_mode not in ALLOWED_EXECUTION_MODES:
        blocked_reasons.append("invalid_execution_mode")

    if normalized_environment and not environment_contract:
        blocked_reasons.append("invalid_environment")

    if normalized_runtime_profile and not runtime_profile_contract:
        blocked_reasons.append("invalid_runtime_profile")

    if normalized_mode == EXECUTION_MODE_REAL_QA_MANUAL:
        if not normalized_environment:
            blocked_reasons.append("missing_environment")
        if not is_explicit_real_confirmation(real_confirmed):
            blocked_reasons.append("missing_real_confirmation")
        if (
            not normalized_runtime_profile
            and not runtime_profile_contract
            and environment_contract
        ):
            runtime_profile_contract = get_default_runtime_profile_for_environment(
                normalized_environment
            )
            if runtime_profile_contract:
                normalized_runtime_profile = runtime_profile_contract["id"]
        if (
            runtime_profile_contract
            and normalized_environment
            and runtime_profile_contract.get("environment") != normalized_environment
        ):
            blocked_reasons.append("runtime_profile_environment_mismatch")

    blocked_reasons = sorted(set(blocked_reasons))
    allowed = not blocked_reasons
    return {
        "allowed": allowed,
        "status": "ALLOWED" if allowed else "BLOCKED",
        "mode": normalized_mode,
        "environment": normalized_environment,
        "environment_contract": environment_contract,
        "runtime_profile": normalized_runtime_profile,
        "runtime_profile_contract": runtime_profile_contract,
        "runtime_contract": runtime_profile_contract or environment_contract,
        "blocked_reasons": blocked_reasons,
        "allow_legacy_real_script": allowed
        and normalized_mode == EXECUTION_MODE_REAL_QA_MANUAL,
        "dry_run_only": allowed and normalized_mode == EXECUTION_MODE_DRY_RUN,
    }


def normalize_execution_mode(mode):
    if mode is None or mode == "":
        return DEFAULT_EXECUTION_MODE
    return str(mode).strip().lower()


def normalize_environment(environment):
    if environment is None:
        return ""
    return str(environment).strip().lower()


def is_explicit_real_confirmation(value):
    if value is True:
        return True
    if value is False or value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes_i_understand"}
