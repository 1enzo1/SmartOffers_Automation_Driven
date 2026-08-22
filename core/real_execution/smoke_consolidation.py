"""Pure terminal consolidation for canonical Alpha checkpoint evidence."""

from core.real_execution.gate_dag import (
    CANONICAL_EVIDENCE_VALID,
    validate_canonical_evidence_record,
)


BASIC_COMPONENTS = ("ACM_CUSTOM_DB", "SMARTOFFERS_API")
FULL_COMPONENTS = (
    "ACM_CUSTOM_DB",
    "ACM_DB",
    "BDA_DB",
    "SMARTOFFERS_API",
)

_MISSING_EVIDENCE = "MISSING_CANONICAL_EVIDENCE"
_DUPLICATE_EVIDENCE = "DUPLICATE_COMPONENT_EVIDENCE"
_GLOBAL_SAFETY_STOP = "GLOBAL_SAFETY_STOP"


def consolidate_smoke_results(
    records,
    context,
    *,
    evaluated_at,
    global_safety_stop=False,
):
    """Build non-authoritative BASIC/FULL summaries without performing I/O."""

    routed = {component: [] for component in FULL_COMPONENTS}
    input_rejections = []
    inputs = records if isinstance(records, (list, tuple)) else (records,)

    for record in inputs:
        validation = validate_canonical_evidence_record(
            record,
            context,
            evaluated_at=evaluated_at,
        )
        component = record.get("component") if isinstance(record, dict) else None
        if isinstance(component, str) and component in routed:
            routed[component].append((record, validation))
        if validation["status"] != CANONICAL_EVIDENCE_VALID:
            input_rejections.append(validation["reason"])

    components = {
        component: _materialize_component(routed[component])
        for component in FULL_COMPONENTS
    }
    safety_stop = global_safety_stop is not False

    return {
        "record_type": "terminal_smoke_consolidation",
        "components": components,
        "input_rejections": input_rejections,
        "basic": _summarize(
            "BASIC_SMOKE",
            BASIC_COMPONENTS,
            components,
            global_safety_stop=safety_stop,
        ),
        "full": _summarize(
            "FULL_SMOKE",
            FULL_COMPONENTS,
            components,
            global_safety_stop=safety_stop,
        ),
        "operational_readiness": False,
        "authoritative": False,
    }


def _materialize_component(candidates):
    if not candidates:
        return {"outcome": "BLOCKED", "reason": _MISSING_EVIDENCE}
    if len(candidates) != 1:
        return {"outcome": "BLOCKED", "reason": _DUPLICATE_EVIDENCE}

    record, validation = candidates[0]
    if validation["status"] != CANONICAL_EVIDENCE_VALID:
        return {"outcome": "BLOCKED", "reason": validation["reason"]}
    return {
        "outcome": record["outcome"],
        "reason": record["sanitized_error_category"],
    }


def _summarize(prefix, component_names, components, *, global_safety_stop):
    outcomes = [components[name]["outcome"] for name in component_names]

    if global_safety_stop:
        suffix = "BLOCKED"
        reason = _GLOBAL_SAFETY_STOP
    elif all(outcome == "OK" for outcome in outcomes):
        suffix = "OK"
        reason = "ALL_COMPONENTS_OK"
    elif prefix == "BASIC_SMOKE" and "FAILED" in outcomes:
        suffix = "FAILED"
        reason = "COMPONENT_FAILURE"
    elif prefix == "FULL_SMOKE" and "OK" in outcomes:
        suffix = "PARTIAL"
        reason = "COMPONENTS_NOT_ALL_OK"
    elif "FAILED" in outcomes:
        suffix = "FAILED"
        reason = "COMPONENT_FAILURE"
    else:
        suffix = "BLOCKED"
        reason = "COMPONENTS_BLOCKED"

    return {
        "status": f"{prefix}_{suffix}",
        "reason": reason,
        "authoritative": False,
        "components": list(component_names),
    }
