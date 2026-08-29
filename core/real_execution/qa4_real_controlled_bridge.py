"""Local-only bridge from Standard evidence to the existing QA4 executor."""

from core.real_execution.qa4_offers_customer_adapter import (
    execute_one_synthetic_qa4_offers_customer_create,
    execute_qa4_offers_customer_create,
)
from core.real_execution.qa4_standard_mock_facade import run_standard_qa4_application_mock


_BLOCKERS = (
    "REAL_QA4_OPERATION_NOT_CONFIRMED",
    "QA4_TEST_DATA_REQUIRED",
    "QA4_CREDENTIAL_OR_CONFIG_REQUIRED",
)
SYNTHETIC_OFFERS_SCENARIO = "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4"
ATOMIC_BDA_AUTHORIZATION = "ONE_ATOMIC_QA4_BDA_DISCOVERY_AND_OFFERS_CREATE_RUN"
RUN_02_BDA_AUTHORIZATION = "ONE_QA4_REPEATABILITY_SMOKE_RUN_02"
RUN_03A_BDA_AUTHORIZATION = "ONE_QA4_CREATE_CUSTOMER_WITH_OFFER_RUN_03A"
RUN_01_ID = "ALPHA_REAL_RUN_01"
RUN_02_ID = "ALPHA_REAL_RUN_02"
RUN_03A_ID = "ALPHA_REAL_RUN_03A"


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
    scenario_id=None,
    runtime_provider=None,
    offer=None,
):
    """Run Standard first, then delegate the exact Offers contract to legacy gates.

    The default call provides no client, refs, secrets, policy, or approval, so it
    remains a zero-send ``BLOCKED`` preflight.  The injected seam is intentionally
    local-test-only and delegates to the existing manual executor through the
    Offers adapter; it does not create a second execution implementation.
    """

    if mode != "real-controlled" or not _is_standard_context(context):
        return _terminal_report({"result": "BLOCKED"}, {})
    if scenario_id is not None and scenario_id != SYNTHETIC_OFFERS_SCENARIO:
        return _terminal_report(
            {"result": "BLOCKED"},
            {"result": "BLOCKED", "blockers": ["SCENARIO_NOT_ALLOWED"]},
        )

    standard_report = run_standard_qa4_application_mock(
        context, mode="mock", evaluated_at=evaluated_at
    )
    if standard_report.get("result") != "PASS":
        return _terminal_report(standard_report, {})

    if callable(runtime_provider):
        runtime_inputs = runtime_provider(context)
        if isinstance(runtime_inputs, dict):
            environ = runtime_inputs.get("environ", environ)
            runtime_refs = runtime_inputs.get("runtime_refs", runtime_refs)
            runtime_secrets = runtime_inputs.get("runtime_secrets", runtime_secrets)
            policy = runtime_inputs.get("policy", policy)
            client = runtime_inputs.get("client", client)
            approval = runtime_inputs.get("approval", approval)
            owner_opt_in = runtime_inputs.get("owner_opt_in", owner_opt_in)
            ledger = runtime_inputs.get("ledger", ledger)
            runtime_factory = runtime_inputs.get("runtime_factory")
        else:
            runtime_factory = None
    else:
        runtime_factory = None

    if scenario_id == SYNTHETIC_OFFERS_SCENARIO:
        adapter_kwargs = {
            "environ": environ,
            "runtime_refs": runtime_refs,
            "runtime_secrets": runtime_secrets,
            "policy": policy,
            "client": client,
            "approval": approval,
            "owner_opt_in": owner_opt_in,
            "ledger": ledger,
        }
        if offer is not None:
            adapter_kwargs["offer"] = offer
        if callable(runtime_factory):
            adapter_kwargs["runtime_factory"] = runtime_factory
        offers_adapter = execute_one_synthetic_qa4_offers_customer_create(
            context,
            **adapter_kwargs,
        )
    else:
        adapter_kwargs = {
            "environ": environ,
            "runtime_refs": runtime_refs,
            "runtime_secrets": runtime_secrets,
            "policy": policy,
            "client": client,
            "approval": approval,
            "owner_opt_in": owner_opt_in,
            "ledger": ledger,
        }
        if offer is not None:
            adapter_kwargs["offer"] = offer
        if callable(runtime_factory):
            adapter_kwargs["runtime_factory"] = runtime_factory
        offers_adapter = execute_qa4_offers_customer_create(
            {**context, "event_time": evaluated_at},
            **adapter_kwargs,
        )
    return _terminal_report(standard_report, offers_adapter)


def run_atomic_qa4_bda_offer_discovery_and_offers_create(
    context,
    *,
    mode,
    evaluated_at,
    scenario_id,
    bda_environ,
    bda_driver=None,
    bda_driver_factory=None,
    bda_authorization,
    bda_ledger=None,
    runtime_provider=None,
):
    """Discover one offer and hand it directly to the controlled runner.

    The offer is deliberately confined to this stack frame and is never added to
    environment, evidence, or a provider result.
    """
    if (
        mode != "real-controlled"
        or scenario_id != SYNTHETIC_OFFERS_SCENARIO
        or not _is_standard_context(context)
        or (bda_driver is None and not callable(bda_driver_factory))
        or not isinstance(bda_authorization, dict)
        or not _atomic_bda_authorization_matches_context(context, bda_authorization)
    ):
        return _atomic_report({"status": "QA4_BDA_OFFER_DISCOVERY_BLOCKED"}, None)

    from core.real_execution.qa4_bda_offer_discovery import run_qa4_bda_offer_discovery
    from core.real_execution.qa4_bda_offer_discovery import BdaDiscoveryAttemptLedger

    discovered_offer = []
    discovery = run_qa4_bda_offer_discovery(
        environ=bda_environ,
        driver=bda_driver,
        driver_factory=bda_driver_factory,
        offer_sink=discovered_offer.append,
        authorization=bda_authorization,
        attempt_ledger=bda_ledger or BdaDiscoveryAttemptLedger(),
    )
    if (
        discovery.get("status") != "QA4_BDA_OFFER_DISCOVERY_OK"
        or len(discovered_offer) != 1
        or not isinstance(discovered_offer[0], str)
        or not discovered_offer[0].strip()
    ):
        return _atomic_report(discovery, None)

    report = run_standard_qa4_real_controlled(
        context,
        mode=mode,
        evaluated_at=evaluated_at,
        scenario_id=scenario_id,
        runtime_provider=runtime_provider,
        offer=discovered_offer[0],
    )
    return _atomic_report(discovery, report)


def _atomic_bda_authorization_matches_context(context, bda_authorization):
    """Bind the one BDA authorization to its exact Alpha run before discovery."""
    run_id = context.get("run_id") if isinstance(context, dict) else None
    expected = (
        RUN_02_BDA_AUTHORIZATION
        if run_id == RUN_02_ID
        else RUN_03A_BDA_AUTHORIZATION
        if run_id == RUN_03A_ID
        else ATOMIC_BDA_AUTHORIZATION
        if run_id in (None, RUN_01_ID)
        else None
    )
    return expected is not None and bda_authorization.get("owner_authorization") == expected


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


def _atomic_report(discovery, report):
    report_data = report if isinstance(report, dict) else {}
    discovery_data = discovery if isinstance(discovery, dict) else {}
    return {
        **report_data,
        "result": report_data.get("result", "BLOCKED"),
        "bda_discovery": {
            "status": discovery_data.get("status"),
            "found_valid_offer": discovery_data.get("found_valid_offer") is True,
            "select_only": discovery_data.get("select_only") is True,
        },
    }


def _ordered_blockers(blockers):
    blocker_set = set(blockers)
    return [blocker for blocker in _BLOCKERS if blocker in blocker_set] + sorted(
        blocker_set.difference(_BLOCKERS)
    )
