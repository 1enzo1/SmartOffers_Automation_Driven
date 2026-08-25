"""Local-only bridge from Standard evidence to the QA4 manual guard."""

from core.real_execution.executor import execute_first_qa4_call_manual
from core.real_execution.http_client import FakeHttpClient
from core.real_execution.policy import CANDIDATE_QA4_API_ID
from core.real_execution.qa4_standard_mock_facade import run_standard_qa4_application_mock


_BLOCKERS = (
    "REAL_QA4_OPERATION_NOT_CONFIRMED",
    "QA4_TEST_DATA_REQUIRED",
    "QA4_CREDENTIAL_OR_CONFIG_REQUIRED",
)


def run_standard_qa4_real_controlled(context, *, mode, evaluated_at):
    """Show the controlled QA4 boundary without permitting transport."""

    if mode != "real-controlled" or not _is_standard_context(context):
        return _blocked_report({"result": "BLOCKED"}, 0)

    standard_report = run_standard_qa4_application_mock(
        context, mode="mock", evaluated_at=evaluated_at
    )
    client = FakeHttpClient()
    guard_result = execute_first_qa4_call_manual(
        _placeholder_request(), {}, {}, _disabled_policy(), client, {}
    )
    return _blocked_report(standard_report, len(client.sent_requests), guard_result)


def _is_standard_context(context):
    return (
        isinstance(context, dict)
        and context.get("environment") == "qa4"
        and context.get("workflow_profile") == "smartoffers_qa4_full_smoke"
    )


def _placeholder_request():
    return {
        "api_id": CANDIDATE_QA4_API_ID,
        "method": "POST",
        "environment": "QA4",
        "explicit_opt_in": False,
        "timeout_seconds": 5,
        "retry_count": 0,
        "source": "alpha-real-controlled-bridge",
    }


def _disabled_policy():
    return {"runtime_flags": {"REAL_EXECUTION_ENABLED": False}}


def _blocked_report(standard_report, send_calls, guard_result=None):
    return {
        "result": "BLOCKED",
        "standard_report": standard_report,
        "blockers": list(_BLOCKERS),
        "guard_decision": (guard_result or {}).get("decision", "blocked"),
        "real_call_executed": False,
        "fake_client_send_calls": send_calls,
    }
