"""Pure, non-I/O readiness report for the future Run 03A operation."""

from collections.abc import Mapping


_REQUIRED_TRUE = (
    "product_real_binding_complete", "server_context_ready", "context_single_use_ready",
    "standard_runner_mapping_ready", "real_controlled_bridge_ready", "adapter_ready",
    "destination_attestation_contract_ready", "synthetic_data_ready", "one_shot_ledger_ready",
    "evidence_capture_ready", "active_run_evidence_view_ready", "pass_fail_blocked_mapping_ready",
)
_ALLOWED_FIELDS = set(_REQUIRED_TRUE) | {"attempts_used", "production"}


def build_run03a_static_preflight(state):
    """Return a sanitized report from injected static booleans only.

    This deliberately does not inspect runtime, authorization, environment, or
    transport state; those remain Owner/live-run gates.
    """
    if not isinstance(state, Mapping):
        return {"status": "BLOCKED", "reason": "MALFORMED_PREFLIGHT_INPUT"}
    if set(state).difference(_ALLOWED_FIELDS):
        return {"status": "BLOCKED", "reason": "UNEXPECTED_PREFLIGHT_FIELD"}
    if "production" not in state or type(state["production"]) is not bool:
        return {"status": "BLOCKED", "reason": "INVALID_PRODUCTION_FLAG"}
    attempts = state.get("attempts_used")
    production = state.get("production")
    missing = [key for key in _REQUIRED_TRUE if state.get(key) is not True]
    gates = {key: state.get(key) is True for key in _REQUIRED_TRUE}
    gates["production"] = production is False
    if attempts != "0/1" or production is not False:
        return {"status": "BLOCKED", "reason": "STATIC_GATE_FAILED", "missing": missing, "gates": gates}
    report = {
        "status": "READY_EXCEPT_OWNER_AUTHORIZATION_AND_LIVE_RUNTIME" if not missing else "BLOCKED",
        "db_postcondition_validation_ready": False,
        "db_validation_status": "NOT_CONFIGURED",
        "attempts_used": "0/1",
        "missing": missing,
        "gates": gates,
    }
    if missing:
        report["reason"] = "STATIC_GATE_FAILED"
    return report
