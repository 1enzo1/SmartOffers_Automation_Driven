"""Closed, fake-only Standard application facade for Alpha QA4 mock checks."""

from core.real_execution.qa4_standard_mock_runner import run_standard_qa4_mock
from core.real_execution.smoke_consolidation import consolidate_smoke_results


_STANDARD_PROFILE = "smartoffers_qa4_full_smoke"


def run_standard_qa4_application_mock(context, *, mode, evaluated_at):
    """Run the Standard mock-only application flow with canned collaborators."""

    if mode != "mock" or not _is_standard_context(context):
        summary = consolidate_smoke_results([], {}, evaluated_at=evaluated_at)
        return _with_terminal_result({"records": [], **summary})

    return _with_terminal_result(
        run_standard_qa4_mock(
            context,
            evaluated_at=evaluated_at,
            acm_custom_executor=lambda _context: _db_result(
                "ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01",
                "acm_custom_db",
                "smartoffers_basic_smoke",
                "CONNECT_AND_READ_OK",
                evaluated_at,
            ),
            acm_executor=lambda _context: _db_result(
                "ORACLE_ACM_TECHNICAL_READ_ONLY_01",
                "acm_db",
                _STANDARD_PROFILE,
                "CONNECT_AND_READ_OK",
                evaluated_at,
            ),
            bda_executor=lambda _context: _db_result(
                "ORACLE_BDA_TECHNICAL_READ_ONLY_01",
                "bda_db",
                _STANDARD_PROFILE,
                "BDA_DB_CHECKPOINT_OK",
                evaluated_at,
            ),
            api_client=lambda _context, _bundle: _api_result(evaluated_at),
        )
    )


def _is_standard_context(context):
    return (
        isinstance(context, dict)
        and context.get("workflow_profile") == _STANDARD_PROFILE
    )


def _with_terminal_result(output):
    """Add the facade-only PASS/FAIL/BLOCKED outcome without changing summary."""

    full_status = output.get("full", {}).get("status")
    if full_status == "FULL_SMOKE_OK":
        result = "PASS"
    elif full_status == "FULL_SMOKE_BLOCKED":
        result = "BLOCKED"
    else:
        result = "FAIL"
    return {**output, "result": result}


def _db_result(checkpoint, resource_id, profile, status, timestamp):
    return {
        "execution_id": f"mock-{resource_id}",
        "timestamp": timestamp,
        "environment": "qa4",
        "profile": profile,
        "checkpoint": checkpoint,
        "resource_id": resource_id,
        "status": status,
        "attempts_used": 1,
        "retry_count": 0,
        "sensitive_values_logged": False,
        "sanitized_error_category": "NONE",
        "stop_reason": "CHECKPOINT_COMPLETED",
        "environment_allowlist": "MATCH",
        "resource_allowlist": "MATCH",
        "destination_allowlist": "MATCH",
        "query_hash_validation": "MATCH",
        "read_only_validation": "PASS",
        "result_shape_validation": "MATCH",
        "fingerprint_validation": "MATCH",
        "preflight_validation": "MATCH",
    }


def _api_result(timestamp):
    return {
        "execution_id": "mock-smartoffers-api",
        "timestamp": timestamp,
        "environment": "qa4",
        "profile": _STANDARD_PROFILE,
        "checkpoint": "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01",
        "resource_id": "smartoffers_api",
        "status": "SMARTOFFERS_API_QA4_CHECKPOINT_OK",
        "attempts_used": 1,
        "retry_count": 0,
        "sensitive_values_logged": False,
        "sanitized_error_category": "NONE",
        "stop_reason": "CHECKPOINT_COMPLETED",
        "allowlist_validation": "MATCH",
        "preflight_validation": "MATCH",
        "path_validation": "MATCH",
        "path_hash_validation": "MATCH",
        "fingerprint_validation": "MATCH",
        "db_gate_bundle_validation": "MATCH",
        "response_body_logged": False,
        "response_headers_logged": False,
    }
