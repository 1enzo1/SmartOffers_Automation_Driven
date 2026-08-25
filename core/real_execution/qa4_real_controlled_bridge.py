"""Local-only bridge from Standard evidence to the existing QA4 executor."""

from core.real_execution.qa4_offers_customer_adapter import execute_qa4_offers_customer_create
from core.real_execution.qa4_standard_mock_facade import run_standard_qa4_application_mock


_BLOCKERS = (
    "REAL_QA4_OPERATION_NOT_CONFIRMED",
    "QA4_TEST_DATA_REQUIRED",
    "QA4_CREDENTIAL_OR_CONFIG_REQUIRED",
)


def run_standard_qa4_real_controlled(
    context,
    *,
    mode,
    evaluated_at,
    environ=None,
    runtime_refs=None,
    runtime_secrets=None,
    policy=None,
    client=None,
    approval=None,
    owner_opt_in=None,
    ledger=None,
):
    """Run Standard first, then delegate the exact Offers contract to legacy gates.

    The default call provides no client, refs, secrets, policy, or approval, so it
    remains a zero-send ``BLOCKED`` preflight.  The injected seam is intentionally
    local-test-only and delegates to the existing manual executor through the
    Offers adapter; it does not create a second execution implementation.
    """

    if mode != "real-controlled" or not _is_standard_context(context):
        return _terminal_report({"result": "BLOCKED"}, {})

    standard_report = run_standard_qa4_application_mock(
        context, mode="mock", evaluated_at=evaluated_at
    )
    if standard_report.get("result") != "PASS":
        return _terminal_report(standard_report, {})

    offers_adapter = execute_qa4_offers_customer_create(
        {**context, "event_time": evaluated_at},
        environ=environ,
        runtime_refs=runtime_refs,
        runtime_secrets=runtime_secrets,
        policy=policy,
        client=client,
        approval=approval,
        owner_opt_in=owner_opt_in,
        ledger=ledger,
    )
    return _terminal_report(standard_report, offers_adapter)


def _is_standard_context(context):
    return (
        isinstance(context, dict)
        and context.get("environment") == "qa4"
        and context.get("workflow_profile") == "smartoffers_qa4_full_smoke"
    )


def _terminal_report(standard_report, offers_adapter):
    adapter_data = offers_adapter if isinstance(offers_adapter, dict) else {}
    result = adapter_data.get("result")
    if result not in {"PASS", "FAIL", "BLOCKED"}:
        result = standard_report.get("result") if standard_report.get("result") in {"FAIL", "BLOCKED"} else "BLOCKED"
    return {
        "result": result,
        "standard_report": standard_report,
        "blockers": _ordered_blockers(adapter_data.get("blockers") or _BLOCKERS),
        "guard_decision": adapter_data.get("executor_decision", "not_called"),
        "offers_adapter": adapter_data,
        "evidence": dict(adapter_data.get("evidence") or {}),
        "real_call_executed": adapter_data.get("real_call_executed") is True,
        "executor_send_attempted": adapter_data.get("send_attempted") is True,
        # Compatibility field: the bridge no longer constructs a FakeHttpClient.
        "fake_client_send_calls": 0,
    }


def _ordered_blockers(blockers):
    blocker_set = set(blockers)
    return [blocker for blocker in _BLOCKERS if blocker in blocker_set] + sorted(
        blocker_set.difference(_BLOCKERS)
    )
