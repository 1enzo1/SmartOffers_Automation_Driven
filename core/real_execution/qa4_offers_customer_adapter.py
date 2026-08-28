"""Local, zero-transport wrapper for the legacy Offers customer-create shape."""

import json
import re
from datetime import datetime
from os import environ as process_environ
from random import randint
from threading import Lock

from core.api_catalog import get_api_catalog_entry
from core.legacy_execution.runtime_config import resolve_legacy_runtime_config
from core.real_execution.executor import execute_first_qa4_call_manual
from core.real_execution.runtime_profiles import get_sanitized_runtime_profile
from core.utils.evidence_payload_builders import build_postpaid_payload


_QA4_ENVIRONMENT = "qa4"
_STANDARD_PROFILE = "smartoffers_qa4_full_smoke"
_OPERATION = "CREATE_OFFERS_CUSTOMER"
_SYNTHETIC_SCENARIO = "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4"
_CATALOG_API_ID = "post-vivo-next-habilitacao-de-cliente-ade0841563"
_LEGACY_OPERATION = "processEvent"
_TEST_MSISDN_REF = "SMARTOFFERS_QA4_TEST_MSISDN"
_TEST_OFFER_REF = "SMARTOFFERS_QA4_TEST_OFFER"
_ATTEMPT_POLICY = {"max_attempts": 1, "retry_count": 0, "fallback": False}
_ONE_RUN_OPT_IN = "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN"
_RUN_02_OPT_IN = "ONE_QA4_REPEATABILITY_SMOKE_RUN_02"
_ALLOWED_ONE_RUN_OPT_INS = {_ONE_RUN_OPT_IN, _RUN_02_OPT_IN}
_EVENT_TIME_FORMAT = "%d-%m-%Y %H:%M:%S"
_EVENT_TIME_PATTERN = re.compile(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}")


class OneRunAttemptLedger:
    """Process-local, thread-safe budget for explicitly scoped one-shot runs."""

    def __init__(self):
        self._lock = Lock()
        self._consumed_scopes = set()

    def consume(self, scope):
        with self._lock:
            if scope in self._consumed_scopes:
                return False
            self._consumed_scopes.add(scope)
            return True

    def snapshot(self, scope):
        """Return the sanitized state for one scope without exposing its value."""
        with self._lock:
            used = 1 if scope in self._consumed_scopes else 0
        return {"attempts_before": 0, "attempts_used": used, "attempts_after": used,
                "max_attempts": 1, "retry_count": 0}


_DEFAULT_ATTEMPT_LEDGER = OneRunAttemptLedger()


def prepare_qa4_offers_customer_create(
    context, *, environ=None, approval=None, synthetic_customer=None, offer=None, defer_offer_validation=False
):
    """Preflight the legacy POST payload without exposing it or sending it."""

    context_data = context if isinstance(context, dict) else {}
    blockers = _context_blockers(context_data)
    catalog_contract = _catalog_contract()
    if not catalog_contract["operationally_released"] and not _approval_matches_operation(
        approval
    ):
        blockers.append("REAL_QA4_OPERATION_NOT_CONFIRMED")
    runtime_config = _runtime_config(environ)

    if not runtime_config["valid"]:
        blockers.append("QA4_CREDENTIAL_OR_CONFIG_REQUIRED")

    test_data = _test_data(environ, synthetic_customer=synthetic_customer, offer=offer)
    if not test_data["available"] and not defer_offer_validation:
        blockers.append("QA4_TEST_DATA_REQUIRED")

    builder_applied = False
    if not defer_offer_validation and not _payload_build_blockers(blockers):
        try:
            build_postpaid_payload(
                test_data["msisdn"],
                test_data["offer"],
                context_data["event_time"],
            )
            builder_applied = True
        except (TypeError, ValueError):
            blockers.append("LEGACY_PAYLOAD_CONTRACT_INVALID")

    blockers = sorted(set(blockers))
    local_preflight_ready = not any(
        blocker != "REAL_QA4_OPERATION_NOT_CONFIRMED" for blocker in blockers
    )
    return {
        "decision": "READY" if not blockers else "BLOCKED",
        "operation": _OPERATION,
        "blockers": blockers,
        "preflight_status": "READY" if local_preflight_ready else "BLOCKED",
        "runtime_preflight": _sanitized_runtime_preflight(runtime_config),
        "test_data": _sanitized_test_data(test_data),
        "request_contract": {
            **catalog_contract["request_contract"],
            "legacy_builder_applied": builder_applied,
        },
        "attempt_policy": dict(_ATTEMPT_POLICY),
        "transport_permitted": False,
        "send_attempted": False,
        "real_call_executed": False,
    }


def prepare_one_synthetic_qa4_offers_customer_create(
    context, *, environ=None, approval=None, current_time=None, random_int=None,
    defer_offer_validation=False,
):
    """Prepare exactly one synthetic QA4 candidate entirely in memory.

    The candidate is deliberately absent from the returned evidence.  A caller
    intending a controlled mutation must use the matching execute helper so the
    same one-time candidate is carried through its internal preflight.
    """

    context_with_today = _context_with_today(context, current_time=current_time)
    candidate = (
        _generate_synthetic_customer(random_int=random_int)
        if context_with_today.get("event_time")
        else None
    )
    return prepare_qa4_offers_customer_create(
        context_with_today,
        environ=environ,
        approval=approval,
        synthetic_customer=candidate,
        defer_offer_validation=defer_offer_validation,
    )


def execute_one_synthetic_qa4_offers_customer_create(
    context,
    *,
    environ=None,
    runtime_refs=None,
    runtime_secrets=None,
    policy=None,
    client=None,
    approval=None,
    owner_opt_in=None,
    ledger=None,
    current_time=None,
    random_int=None,
    offer=None,
    runtime_factory=None,
):
    """Execute the one-shot path without persisting or reporting test data."""

    context_with_today = _context_with_today(context, current_time=current_time)
    candidate = (
        _generate_synthetic_customer(random_int=random_int)
        if context_with_today.get("event_time")
        else None
    )
    return execute_qa4_offers_customer_create(
        context_with_today,
        environ=environ,
        runtime_refs=runtime_refs,
        runtime_secrets=runtime_secrets,
        policy=policy,
        client=client,
        approval=approval,
        owner_opt_in=owner_opt_in,
        ledger=ledger,
        synthetic_customer=candidate,
        offer=offer,
        runtime_factory=runtime_factory,
    )


def execute_qa4_offers_customer_create(
    context,
    *,
    environ=None,
    runtime_refs=None,
    runtime_secrets=None,
    policy=None,
    client=None,
    approval=None,
    owner_opt_in=None,
    ledger=None,
    synthetic_customer=None,
    offer=None,
    runtime_factory=None,
    client_factory=None,
):
    """Route the exact Offers contract through the existing manual executor.

    A transport-marked client may pass only the one-run QA4 gate.  The ordinary
    default is still a zero-send preflight because no runtime inputs or opt-in are
    supplied by application entrypoints.
    """

    preflight = prepare_qa4_offers_customer_create(
        context,
        environ=environ,
        approval=approval,
        synthetic_customer=synthetic_customer,
        offer=offer,
    )
    if preflight["preflight_status"] != "READY":
        return _terminal_result("BLOCKED", preflight, None)
    if callable(runtime_factory):
        runtime_inputs = runtime_factory()
        if not isinstance(runtime_inputs, dict):
            return _terminal_result("BLOCKED", preflight, None)
        runtime_refs = runtime_inputs.get("runtime_refs", runtime_refs)
        runtime_secrets = runtime_inputs.get("runtime_secrets", runtime_secrets)
        policy = runtime_inputs.get("policy", policy)
        approval = runtime_inputs.get("approval", approval)
        owner_opt_in = runtime_inputs.get("owner_opt_in", owner_opt_in)
        ledger = runtime_inputs.get("ledger", ledger)
        client_factory = runtime_inputs.get("client_factory", client_factory)
        preflight = prepare_qa4_offers_customer_create(
            context, environ=environ, approval=approval,
            synthetic_customer=synthetic_customer, offer=offer,
        )
    if preflight["decision"] != "READY":
        return _terminal_result("BLOCKED", preflight, None)
    if _is_real_transport_client(client) or callable(client_factory):
        transport_blockers = _transport_gate_blockers(
            context, preflight, policy, approval, owner_opt_in
        )
        if not transport_blockers:
            return _execute_with_manual_executor(
                context,
                environ,
                runtime_refs,
                runtime_secrets,
                policy,
                client,
                approval,
                preflight,
                owner_opt_in=owner_opt_in,
                ledger=ledger,
                synthetic_customer=synthetic_customer,
                offer=offer,
                client_factory=client_factory,
            )
        return _terminal_result(
            "BLOCKED",
            preflight,
            {"decision": "blocked", "blocked_reasons": transport_blockers},
        )

    return _execute_with_manual_executor(
        context,
        environ,
        runtime_refs,
        runtime_secrets,
        policy,
        client,
        approval,
        preflight,
        owner_opt_in=owner_opt_in,
        synthetic_customer=synthetic_customer,
        offer=offer,
        client_factory=client_factory,
    )


def _execute_with_manual_executor(
    context,
    environ,
    runtime_refs,
    runtime_secrets,
    policy,
    client,
    approval,
    preflight,
    owner_opt_in=None,
    ledger=None,
    synthetic_customer=None,
    offer=None,
    client_factory=None,
):
    request = _executor_request(
        preflight["request_contract"],
        scenario_id=_SYNTHETIC_SCENARIO if synthetic_customer else None,
    )
    executor_result = execute_first_qa4_call_manual(
        request,
        runtime_refs if isinstance(runtime_refs, dict) else {},
        _runtime_secrets_with_legacy_body(
            context,
            environ,
            runtime_secrets,
            synthetic_customer=synthetic_customer,
            offer=offer,
        ),
        policy if isinstance(policy, dict) else {},
        client,
        approval if isinstance(approval, dict) else {},
        attempt_ledger=ledger if (_is_real_transport_client(client) or callable(client_factory)) else None,
        attempt_scope=(owner_opt_in or {}).get("authorization") if (_is_real_transport_client(client) or callable(client_factory)) else None,
        client_factory=client_factory,
    )
    return _terminal_result(_terminal_status(executor_result), preflight, executor_result)


def _transport_gate_blockers(context, preflight, policy, approval, owner_opt_in):
    context_data = context if isinstance(context, dict) else {}
    policy_data = policy if isinstance(policy, dict) else {}
    opt_in = owner_opt_in if isinstance(owner_opt_in, dict) else {}
    blockers = []
    if preflight.get("preflight_status") != "READY" or context_data.get("environment") != _QA4_ENVIRONMENT:
        blockers.append("QA4_PREFLIGHT_REQUIRED")
    if not _approval_is_complete_for_operation(approval):
        blockers.append("MANUAL_APPROVAL_REQUIRED")
    bounded_opt_in = _bounded_one_run_opt_in_matches(opt_in)
    if not bounded_opt_in:
        blockers.append(f"{_ONE_RUN_OPT_IN}_OPT_IN_REQUIRED")
    runtime_flags = policy_data.get("runtime_flags") or {}
    if runtime_flags.get("REAL_TRANSPORT_ALLOWED") is not True:
        blockers.append("REAL_TRANSPORT_ALLOWED_REQUIRED")
    if runtime_flags.get("PRODUCTION") is not False:
        blockers.append("PRODUCTION_TRANSPORT_DENIED")
    if runtime_flags.get("GLOBAL_NO_AUTH_ENABLED") is not False:
        blockers.append("GLOBAL_NO_AUTH_MUST_BE_DISABLED")
    if runtime_flags.get("REAL_EXECUTION_ENABLED") is not True:
        blockers.append("REAL_EXECUTION_ENABLED_REQUIRED")
    if runtime_flags.get("REAL_EXECUTION_KILL_SWITCH") is not False:
        blockers.append("REAL_EXECUTION_KILL_SWITCH_MUST_BE_FALSE")
    if bounded_opt_in and not _exact_no_auth_transport_scope(policy_data, opt_in):
        blockers.append("OPERATION_SCOPED_NO_AUTH_REQUIRED")
    if not _destination_attestation_matches(policy_data):
        blockers.append("DESTINATION_ATTESTATION_REQUIRED")
    return sorted(set(blockers))


def _approval_is_complete_for_operation(approval):
    approval_data = approval if isinstance(approval, dict) else {}
    required_refs = ("approver_ref", "ticket_ref", "approved_at_ref")
    return _approval_matches_operation(approval_data) and all(
        approval_data.get(key) for key in required_refs
    )


def _bounded_one_run_opt_in_matches(opt_in):
    return (
        opt_in.get("approved") is True
        and opt_in.get("operation") in _ALLOWED_ONE_RUN_OPT_INS
        and opt_in.get("authorization") == opt_in.get("operation")
        and opt_in.get("environment") == "QA4"
        and opt_in.get("mode") == "real-controlled"
        and opt_in.get("scenario_id") == _SYNTHETIC_SCENARIO
        and opt_in.get("application_confirmation") == "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER"
        and opt_in.get("max_attempts") == _ATTEMPT_POLICY["max_attempts"]
        and opt_in.get("retry_count") == _ATTEMPT_POLICY["retry_count"]
        and opt_in.get("fallback") is _ATTEMPT_POLICY["fallback"]
        and opt_in.get("production") is False
    )


def _exact_no_auth_transport_scope(policy_data, opt_in):
    allowlist = policy_data.get("first_qa4_allowlist") or {}
    item = (allowlist.get("items") or {}).get(_CATALOG_API_ID) or {}
    scoped_no_auth = policy_data.get("operation_scoped_no_auth") or {}
    return (
        item.get("api_id") == _CATALOG_API_ID
        and item.get("method") == "POST"
        and item.get("environment") == "QA4"
        and item.get("operation") == _OPERATION
        and item.get("scenario_id") == _SYNTHETIC_SCENARIO
        and item.get("auth_required") is False
        and scoped_no_auth
        == {
            "authorization": scoped_no_auth.get("authorization"),
            "operation": _OPERATION,
            "scenario_id": _SYNTHETIC_SCENARIO,
            "environment": "QA4",
            "auth_required": False,
        }
        and scoped_no_auth.get("authorization") in _ALLOWED_ONE_RUN_OPT_INS
        and scoped_no_auth.get("authorization") == opt_in.get("authorization")
    )


def _destination_attestation_matches(policy_data):
    attestation = policy_data.get("destination_attestation") or {}
    legacy_local_attestation = (
        attestation.get("source") == "local_runtime_config"
        and attestation.get("environment") == "QA4"
        and attestation.get("allowlist_match") is True
        and attestation.get("status") == "MATCH"
    )
    scoped_derived_attestation = attestation == {
        "source": "derived_qa4_api_url",
        "environment": "QA4",
        "operation": _OPERATION,
        "scenario_id": _SYNTHETIC_SCENARIO,
        "api_id": _CATALOG_API_ID,
        "allowlist_match": True,
        "status": "MATCH",
    }
    return legacy_local_attestation or scoped_derived_attestation


def _consume_one_run_budget(ledger):
    active_ledger = ledger if hasattr(ledger, "consume") else _DEFAULT_ATTEMPT_LEDGER
    return active_ledger.consume(_ONE_RUN_OPT_IN) is True


def _context_blockers(context):
    blockers = []
    if context.get("environment") != _QA4_ENVIRONMENT:
        blockers.append("ENVIRONMENT_NOT_QA4")
    if context.get("workflow_profile") != _STANDARD_PROFILE:
        blockers.append("WORKFLOW_PROFILE_NOT_ALLOWED")
    if not isinstance(context.get("event_time"), str) or not context["event_time"]:
        blockers.append("INVALID_EVENT_TIME")
    return blockers


def _payload_build_blockers(blockers):
    return [
        blocker
        for blocker in blockers
        if blocker != "REAL_QA4_OPERATION_NOT_CONFIRMED"
    ]


def _runtime_config(environ):
    return resolve_legacy_runtime_config(
        get_sanitized_runtime_profile(_STANDARD_PROFILE), base_env=environ
    )


def _test_data(environ, *, synthetic_customer=None, offer=None):
    env = environ if isinstance(environ, dict) else process_environ
    candidate = synthetic_customer if isinstance(synthetic_customer, dict) else {}
    msisdn = candidate.get("msisdn") or env.get(_TEST_MSISDN_REF)
    resolved_offer = offer if isinstance(offer, str) and offer.strip() else env.get(_TEST_OFFER_REF)
    return {
        "available": bool(str(msisdn or "").strip()) and bool(str(resolved_offer or "").strip()),
        "msisdn": msisdn,
        "offer": resolved_offer,
        "source": "synthetic" if candidate else "runtime_ref",
    }


def _sanitized_runtime_preflight(runtime_config):
    preflight = runtime_config.get("preflight") or {}
    return {
        "status": preflight.get("status"),
        "environment": preflight.get("environment"),
        "profile": preflight.get("profile"),
        "resources": list(preflight.get("resources") or []),
        "missing_refs": list(preflight.get("missing_refs") or []),
    }


def _catalog_contract():
    entry = get_api_catalog_entry(_CATALOG_API_ID) or {}
    request_contract = {
        "api_id": entry.get("api_id"),
        "method": entry.get("method"),
        "path": entry.get("path"),
        "legacy_operation": _LEGACY_OPERATION,
    }
    valid_shape = (
        entry.get("api_id") == _CATALOG_API_ID
        and entry.get("method") == "POST"
        and entry.get("path") == "/ws/integration/online/process"
        and "QA4" in (entry.get("supported_environments") or [])
    )
    return {
        "request_contract": request_contract,
        "operationally_released": valid_shape
        and entry.get("execution_status") != "blocked"
        and entry.get("safe_for_real_execution") is True,
    }


def _approval_matches_operation(approval):
    approval_data = approval if isinstance(approval, dict) else {}
    return (
        approval_data.get("approved") is True
        and approval_data.get("risk_acceptance") is True
        and approval_data.get("approved_api_id") == _CATALOG_API_ID
        and approval_data.get("approved_environment") == "QA4"
    )


def _executor_request(request_contract, *, scenario_id=None):
    return {
        "api_id": request_contract.get("api_id"),
        "method": request_contract.get("method"),
        "environment": "QA4",
        "explicit_opt_in": True,
        "timeout_seconds": 5,
        "retry_count": 0,
        "source": "alpha-offers-customer-create",
        "operation": _OPERATION,
        "scenario_id": scenario_id,
    }


def _runtime_secrets_with_legacy_body(
    context, environ, runtime_secrets, *, synthetic_customer=None, offer=None
):
    secrets = dict(runtime_secrets) if isinstance(runtime_secrets, dict) else {}
    test_data = _test_data(environ, synthetic_customer=synthetic_customer, offer=offer)
    if test_data["available"]:
        payload, _ = build_postpaid_payload(
            test_data["msisdn"], test_data["offer"], context["event_time"]
        )
        secrets["body"] = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    return secrets


def _generate_synthetic_customer(*, random_int=None):
    generator = random_int if callable(random_int) else randint
    suffix = generator(20_000_000, 99_999_999)
    if not isinstance(suffix, int) or not 20_000_000 <= suffix <= 99_999_999:
        raise ValueError("synthetic MSISDN suffix must be an eight-digit integer")
    msisdn = f"119{suffix}"
    return {"msisdn": msisdn, "account": msisdn[3:], "external_id": f"NEXT_{msisdn[3:]}"}


def _context_with_today(context, *, current_time=None):
    raw_timestamp = current_time() if callable(current_time) else datetime.now()
    timestamp = (
        raw_timestamp.strftime(_EVENT_TIME_FORMAT)
        if isinstance(raw_timestamp, datetime)
        else raw_timestamp
    )
    event_time = timestamp if _is_local_today_event_time(timestamp) else None
    return {**(context if isinstance(context, dict) else {}), "event_time": event_time}


def _is_local_today_event_time(timestamp):
    if not isinstance(timestamp, str) or not _EVENT_TIME_PATTERN.fullmatch(timestamp):
        return False
    try:
        return datetime.strptime(timestamp, _EVENT_TIME_FORMAT).date() == datetime.now().date()
    except ValueError:
        return False


def _sanitized_test_data(test_data):
    result = {"available": test_data["available"]}
    if test_data.get("source") == "synthetic":
        result["source"] = "synthetic"
    return result


def _terminal_status(executor_result):
    decision = (executor_result or {}).get("decision")
    if decision == "manual_call_completed":
        status_code = ((executor_result or {}).get("evidence") or {}).get("status_code")
        return "PASS" if isinstance(status_code, int) and 200 <= status_code < 300 else "FAIL"
    if decision == "client_error_after_send":
        return "FAIL"
    return "BLOCKED"


def _terminal_result(result, preflight, executor_result):
    executor_data = executor_result or {}
    return {
        "result": result,
        "operation": _OPERATION,
        "blockers": list(executor_data.get("blocked_reasons") or preflight["blockers"]),
        "request_contract": dict(preflight["request_contract"]),
        "attempt_policy": dict(_ATTEMPT_POLICY),
        "preflight": preflight,
        "executor_decision": executor_data.get("decision", "not_called"),
        "evidence": dict(executor_data.get("evidence") or {}),
        "attempt_ledger": dict(executor_data.get("attempt_ledger") or {}),
        "real_call_executed": executor_data.get("real_call_executed") is True,
        "send_attempted": executor_data.get("real_call_executed") is True
        or executor_data.get("decision") == "client_error_after_send",
    }


def _is_real_transport_client(client):
    return client is not None and getattr(client, "is_real_transport_client", False) is True
