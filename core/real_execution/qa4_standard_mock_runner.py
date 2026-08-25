"""Injected, Standard-only mock orchestration for Alpha QA4 sanity checks."""

from core.real_execution.gate_dag import (
    DB_CHECKPOINT_GATES_READY,
    normalize_checkpoint_evidence,
    validate_api_db_gate_bundle,
)
from core.real_execution.smoke_consolidation import consolidate_smoke_results


_CONTEXT_FIELDS = (
    "orchestration_id",
    "operational_window_ref",
    "window_started_at",
    "window_expires_at",
    "environment",
    "workflow_profile",
)


def run_standard_qa4_mock(
    context,
    *,
    evaluated_at,
    acm_custom_executor,
    acm_executor,
    bda_executor,
    api_client,
):
    """Run injected Standard collaborators and return only canonical evidence."""

    sanitized_context = _sanitized_context(context)
    records = [
        normalize_checkpoint_evidence(
            executor(sanitized_context), sanitized_context, evaluated_at=evaluated_at
        )
        for executor in (acm_custom_executor, acm_executor, bda_executor)
    ]
    db_gate_bundle = validate_api_db_gate_bundle(
        records, sanitized_context, evaluated_at=evaluated_at
    )
    if db_gate_bundle["status"] == DB_CHECKPOINT_GATES_READY:
        records.append(
            normalize_checkpoint_evidence(
                api_client(sanitized_context, db_gate_bundle),
                sanitized_context,
                evaluated_at=evaluated_at,
            )
        )

    summary = consolidate_smoke_results(
        records, sanitized_context, evaluated_at=evaluated_at
    )
    return {"records": records, **summary}


def _sanitized_context(context):
    context_data = context if isinstance(context, dict) else {}
    return {field: context_data.get(field) for field in _CONTEXT_FIELDS}
