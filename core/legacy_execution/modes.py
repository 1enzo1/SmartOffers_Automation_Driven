from core.real_execution.environments import get_sanitized_qa_environment


EXECUTION_MODE_DRY_RUN = "dry_run"
EXECUTION_MODE_MOCK = "mock"
EXECUTION_MODE_REAL_QA_MANUAL = "real_qa_manual"
DEFAULT_EXECUTION_MODE = EXECUTION_MODE_MOCK
ALLOWED_EXECUTION_MODES = (
    EXECUTION_MODE_DRY_RUN,
    EXECUTION_MODE_MOCK,
    EXECUTION_MODE_REAL_QA_MANUAL,
)


def evaluate_execution_mode_request(mode=None, environment=None, real_confirmed=False):
    normalized_mode = normalize_execution_mode(mode)
    normalized_environment = normalize_environment(environment)
    environment_contract = (
        get_sanitized_qa_environment(normalized_environment)
        if normalized_environment
        else None
    )
    blocked_reasons = []

    if normalized_mode not in ALLOWED_EXECUTION_MODES:
        blocked_reasons.append("invalid_execution_mode")

    if normalized_environment and not environment_contract:
        blocked_reasons.append("invalid_environment")

    if normalized_mode == EXECUTION_MODE_REAL_QA_MANUAL:
        if not normalized_environment:
            blocked_reasons.append("missing_environment")
        if not is_explicit_real_confirmation(real_confirmed):
            blocked_reasons.append("missing_real_confirmation")

    blocked_reasons = sorted(set(blocked_reasons))
    allowed = not blocked_reasons
    return {
        "allowed": allowed,
        "status": "ALLOWED" if allowed else "BLOCKED",
        "mode": normalized_mode,
        "environment": normalized_environment,
        "environment_contract": environment_contract,
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
