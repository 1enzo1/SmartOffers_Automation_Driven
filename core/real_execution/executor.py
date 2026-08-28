import re

from core.real_execution.allowlist import build_first_qa4_allowlist, validate_first_qa4_allowlist
from core.real_execution.http_client import is_fake_client
from core.real_execution.policy import build_readiness_policy
from core.real_execution.readiness import evaluate_real_execution_readiness
from core.real_execution.runtime import validate_runtime_contract, validate_runtime_secrets_contract
from core.risk import classify_adapter_risk


_IP_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
_NO_AUTH_API_ID = "post-vivo-next-habilitacao-de-cliente-ade0841563"
_NO_AUTH_OPERATION = "CREATE_OFFERS_CUSTOMER"
_NO_AUTH_SCENARIO = "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4"


def prepare_first_qa4_call(request, runtime, policy, client):
    """Prepare the first QA4 call path with a fake client only."""
    request_data = request if isinstance(request, dict) else {}
    runtime_data = runtime if isinstance(runtime, dict) else {}
    policy_data = policy if isinstance(policy, dict) else {}

    blocked_reasons = []
    runtime_result = validate_runtime_contract(runtime_data)
    allowlist = policy_data.get("first_qa4_allowlist") or build_first_qa4_allowlist()
    allowlist_result = validate_first_qa4_allowlist(request_data, allowlist)
    risk_result = classify_adapter_risk(request_data.get("risk_input") or _risk_work_item(request_data))
    readiness_policy = _readiness_policy(policy_data, allowlist_result)
    readiness_request = _readiness_request(request_data, risk_result)
    readiness_result = evaluate_real_execution_readiness(readiness_request, readiness_policy)

    if not is_fake_client(client):
        blocked_reasons.append("fake_client_required")
    if not runtime_result["valid"]:
        blocked_reasons.extend(runtime_result["blocked_reasons"])
    if not allowlist_result["valid"]:
        blocked_reasons.extend(allowlist_result["blocked_reasons"])
    if risk_result.get("risk_status") == "blocked":
        blocked_reasons.append("risk_classifier_blocked")
    if readiness_result.get("decision") == "blocked":
        blocked_reasons.append("readiness_blocked")
        blocked_reasons.extend(readiness_result.get("blocked_reasons") or [])

    blocked_reasons = _dedupe_sorted(blocked_reasons)
    if blocked_reasons:
        return _result(
            "blocked",
            blocked_reasons,
            request_data,
            runtime_result,
            allowlist_result,
            risk_result,
            readiness_result,
            client_response=None,
        )

    sanitized_request = _sanitized_request(request_data, runtime_result, allowlist_result)
    client_response = client.send(sanitized_request)
    return _result(
        "prepared_with_fake_client",
        [],
        request_data,
        runtime_result,
        allowlist_result,
        risk_result,
        readiness_result,
        client_response=client_response,
    )


def execute_first_qa4_call_manual(
    request, runtime_refs, runtime_secrets, policy, client, approval, *, attempt_ledger=None, attempt_scope=None, client_factory=None
):
    """Gate a manual QA4 call. Runtime values are only passed to the client."""
    request_data = request if isinstance(request, dict) else {}
    runtime_refs_data = runtime_refs if isinstance(runtime_refs, dict) else {}
    runtime_secrets_data = runtime_secrets if isinstance(runtime_secrets, dict) else {}
    policy_data = policy if isinstance(policy, dict) else {}
    approval_data = approval if isinstance(approval, dict) else {}

    blocked_reasons = []
    approval_result = _validate_manual_approval(approval_data, request_data)
    allowlist = policy_data.get("first_qa4_allowlist") or build_first_qa4_allowlist()
    allowlist_result = validate_first_qa4_allowlist(request_data, allowlist)
    allowlist_item = allowlist_result.get("allowlist_item") or {}
    auth_required = not _is_exact_no_auth_scope(
        request_data, allowlist_result, allowlist_item, policy_data
    )
    runtime_refs_result = validate_runtime_contract(
        runtime_refs_data, auth_required=auth_required
    )
    runtime_secrets_result = validate_runtime_secrets_contract(
        runtime_secrets_data, auth_required=auth_required
    )
    risk_result = classify_adapter_risk(_manual_risk_work_item(request_data, allowlist_result))
    readiness_policy = _readiness_policy(policy_data, allowlist_result)
    readiness_request = _readiness_request(request_data, risk_result)
    readiness_result = evaluate_real_execution_readiness(readiness_request, readiness_policy)

    if not _is_real_manual_client(client) and not callable(client_factory):
        blocked_reasons.append("real_manual_client_required")
    if not approval_result["valid"]:
        blocked_reasons.extend(approval_result["blocked_reasons"])
    if not runtime_refs_result["valid"]:
        blocked_reasons.extend(runtime_refs_result["blocked_reasons"])
    if not runtime_secrets_result["valid"]:
        blocked_reasons.extend(runtime_secrets_result["blocked_reasons"])
    if not allowlist_result["valid"]:
        blocked_reasons.extend(allowlist_result["blocked_reasons"])
    if risk_result.get("risk_status") == "blocked":
        blocked_reasons.append("risk_classifier_blocked")
    if readiness_result.get("decision") != "ready_for_manual_review":
        blocked_reasons.append("readiness_not_ready_for_manual_review")
        blocked_reasons.extend(readiness_result.get("blocked_reasons") or [])

    item = allowlist_result.get("allowlist_item") or {}
    if request_data.get("timeout_seconds") != item.get("timeout_seconds"):
        blocked_reasons.append("timeout_not_allowlisted")
    if request_data.get("retry_count") != 0:
        blocked_reasons.append("retry_not_allowed")
    if runtime_secrets_data.get("timeout_seconds") != item.get("timeout_seconds"):
        blocked_reasons.append("runtime_timeout_not_allowlisted")

    blocked_reasons = _dedupe_sorted(blocked_reasons)
    if blocked_reasons:
        return _manual_result(
            "blocked",
            blocked_reasons,
            request_data,
            approval_result,
            runtime_refs_result,
            runtime_secrets_result,
            allowlist_result,
            risk_result,
            readiness_result,
            client_response=None,
            send_attempted=False,
            error=None,
        )

    sanitized_request = _sanitized_request(request_data, runtime_refs_result, allowlist_result)
    active_client = client
    if active_client is None and callable(client_factory):
        active_client = client_factory()
    if not _is_real_manual_client(active_client):
        return _manual_result(
            "blocked", ["real_manual_client_required"], request_data,
            approval_result, runtime_refs_result, runtime_secrets_result,
            allowlist_result, risk_result, readiness_result, client_response=None,
            send_attempted=False, error=None,
        )
    if attempt_scope and not _consume_attempt_budget(attempt_ledger, attempt_scope):
        return _manual_result(
            "blocked", [f"{attempt_scope}_BUDGET_EXHAUSTED"], request_data,
            approval_result, runtime_refs_result, runtime_secrets_result,
            allowlist_result, risk_result, readiness_result, client_response=None,
            send_attempted=False, error=None,
        )
    try:
        client_response = active_client.send(
            sanitized_request,
            _copy_value(runtime_secrets_data),
            item.get("timeout_seconds"),
        )
    except Exception as exc:
        return _manual_result(
            "client_error_after_send",
            [],
            request_data,
            approval_result,
            runtime_refs_result,
            runtime_secrets_result,
            allowlist_result,
            risk_result,
            readiness_result,
            client_response=None,
            send_attempted=True,
            error=exc,
        )

    return _manual_result(
        "manual_call_completed",
        [],
        request_data,
        approval_result,
        runtime_refs_result,
        runtime_secrets_result,
        allowlist_result,
        risk_result,
        readiness_result,
        client_response=client_response,
        send_attempted=True,
        error=None,
    )


def _consume_attempt_budget(ledger, scope):
    return hasattr(ledger, "consume") and ledger.consume(scope) is True


def _is_exact_no_auth_scope(request_data, allowlist_result, allowlist_item, policy_data):
    return (
        allowlist_result.get("valid") is True
        and allowlist_item.get("auth_required") is False
        and allowlist_item.get("api_id") == _NO_AUTH_API_ID
        and allowlist_item.get("method") == "POST"
        and allowlist_item.get("environment") == "QA4"
        and allowlist_item.get("operation") == _NO_AUTH_OPERATION
        and allowlist_item.get("scenario_id") == _NO_AUTH_SCENARIO
        and policy_data.get("operation_scoped_no_auth")
        == {
            "authorization": "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
            "operation": _NO_AUTH_OPERATION,
            "scenario_id": _NO_AUTH_SCENARIO,
            "environment": "QA4",
            "auth_required": False,
        }
        and (policy_data.get("runtime_flags") or {}).get("GLOBAL_NO_AUTH_ENABLED") is False
        and request_data.get("api_id") == _NO_AUTH_API_ID
        and request_data.get("method") == "POST"
        and request_data.get("environment") == "QA4"
        and request_data.get("operation") == _NO_AUTH_OPERATION
        and request_data.get("scenario_id") == _NO_AUTH_SCENARIO
    )


def _risk_work_item(request_data):
    return {
        "api_id": request_data.get("api_id"),
        "method": request_data.get("method"),
        "environment": request_data.get("environment"),
        "planning_mode": "first_qa4_fake_only",
        "evidence_layer": "read-only readiness",
    }


def _manual_risk_work_item(request_data, allowlist_result):
    return {
        "api_id": request_data.get("api_id"),
        "method": request_data.get("method"),
        "environment": request_data.get("environment"),
        "timeout_seconds": request_data.get("timeout_seconds"),
        "retry_count": request_data.get("retry_count"),
        "manual_intent": "first_qa4_call_gate",
        "allowlist_status": "valid" if allowlist_result.get("valid") else "blocked",
        "risk_status": request_data.get("risk_status"),
        "planning_mode": "manual_gate_only",
    }


def _readiness_policy(policy_data, allowlist_result):
    item = allowlist_result.get("allowlist_item") or {}
    return build_readiness_policy(
        runtime_flags=policy_data.get("runtime_flags") or {},
        allowed_environments=[item.get("environment")] if item.get("environment") else [],
        allowed_api_ids=[item.get("api_id")] if item.get("api_id") else [],
        allowed_methods_by_api_id={item.get("api_id"): item.get("method")} if item.get("api_id") else {},
        timeout_limits={
            "min_seconds": item.get("timeout_seconds", 0),
            "max_seconds": item.get("timeout_seconds", 0),
        },
        required_retry_count=item.get("retry_count", 0),
    )


def _readiness_request(request_data, risk_result):
    return {
        "api_id": request_data.get("api_id"),
        "method": request_data.get("method"),
        "environment": request_data.get("environment"),
        "requested_mode": "first_qa4_manual_review",
        "explicit_opt_in": request_data.get("explicit_opt_in") is True,
        "timeout_seconds": request_data.get("timeout_seconds"),
        "retry_count": request_data.get("retry_count"),
        "risk_assessment": risk_result,
    }


def _sanitized_request(request_data, runtime_result, allowlist_result):
    item = allowlist_result.get("allowlist_item") or {}
    runtime = runtime_result.get("sanitized_runtime") or {}
    return {
        "api_id": item.get("api_id"),
        "method": item.get("method"),
        "environment": item.get("environment"),
        "timeout_seconds": item.get("timeout_seconds"),
        "retry_count": item.get("retry_count"),
        "runtime_ready": runtime.get("valid") is True,
        "endpoint_reference": runtime.get("endpoint_reference") is True,
        "auth_reference": runtime.get("auth_reference") is True,
        "headers_reference": runtime.get("headers_reference") is True,
        "body_reference": runtime.get("body_reference") is True,
        "correlation_reference": runtime.get("correlation_reference"),
        "source": request_data.get("source") or "mvp7.7.1.0",
    }


def _validate_manual_approval(approval_data, request_data):
    blocked_reasons = []
    required = (
        "approver_ref",
        "ticket_ref",
        "approved_api_id",
        "approved_environment",
        "approved_at_ref",
    )
    if approval_data.get("approved") is not True:
        blocked_reasons.append("approval_missing")
    if approval_data.get("risk_acceptance") is not True:
        blocked_reasons.append("risk_acceptance_missing")
    for key in required:
        if not approval_data.get(key):
            blocked_reasons.append(f"missing_{key}")
    if approval_data.get("approved_api_id") != request_data.get("api_id"):
        blocked_reasons.append("approved_api_id_mismatch")
    if approval_data.get("approved_environment") != "QA4":
        blocked_reasons.append("approved_environment_not_qa4")
    if approval_data.get("approved_environment") != request_data.get("environment"):
        blocked_reasons.append("approved_environment_mismatch")
    if _contains_sensitive_approval_text(approval_data):
        blocked_reasons.append("approval_contains_sensitive_text")

    return {
        "valid": not blocked_reasons,
        "blocked_reasons": _dedupe_sorted(blocked_reasons),
        "sanitized_approval": {
            "approver_reference": _mask_ref(str(approval_data.get("approver_ref") or "")),
            "ticket_reference": _mask_ref(str(approval_data.get("ticket_ref") or "")),
            "approved_api_id": approval_data.get("approved_api_id"),
            "approved_environment": approval_data.get("approved_environment"),
            "approved_at_reference": _mask_ref(str(approval_data.get("approved_at_ref") or "")),
        },
    }


def _contains_sensitive_approval_text(approval_data):
    text = " ".join(str(value).lower() for value in approval_data.values())
    forbidden = (
        "://",
        "token",
        "secret",
        "credential",
        "password",
        "bearer",
        "cookie",
    )
    return any(term in text for term in forbidden) or bool(_IP_PATTERN.search(text))


def _is_real_manual_client(client):
    return bool(getattr(client, "is_real_manual_client", False))


def _manual_result(
    decision,
    blocked_reasons,
    request_data,
    approval_result,
    runtime_refs_result,
    runtime_secrets_result,
    allowlist_result,
    risk_result,
    readiness_result,
    client_response,
    send_attempted,
    error,
):
    real_call_executed = send_attempted and client_response is not None
    evidence = {
        "api_id": request_data.get("api_id"),
        "method": request_data.get("method"),
        "environment": request_data.get("environment"),
        "decision": decision,
        "approval_reference": (approval_result.get("sanitized_approval") or {}).get("approver_reference"),
        "ticket_reference": (approval_result.get("sanitized_approval") or {}).get("ticket_reference"),
        "correlation_reference": (runtime_refs_result.get("sanitized_runtime") or {}).get("correlation_reference"),
        "status_code": (client_response or {}).get("status_code"),
        "elapsed_ms": (client_response or {}).get("elapsed_ms"),
        "real_call_executed": real_call_executed,
        "body_recorded": False,
        "error": _sanitize_error(error),
    }
    return {
        "decision": decision,
        "allowed": decision == "manual_call_completed",
        "blocked_reasons": list(blocked_reasons),
        "evidence": evidence,
        "sanitized_log": dict(evidence),
        "approval": approval_result.get("sanitized_approval"),
        "runtime_refs": runtime_refs_result.get("sanitized_runtime"),
        "allowlist": allowlist_result.get("allowlist_item"),
        "risk": risk_result,
        "readiness": readiness_result,
        "client_response": _sanitized_real_client_response(client_response),
        "real_call_executed": real_call_executed,
        "next_step": _manual_next_step(decision),
    }


def _sanitized_real_client_response(client_response):
    if not client_response:
        return {}
    return {
        "status_code": client_response.get("status_code"),
        "ok": client_response.get("ok") is True,
        "elapsed_ms": client_response.get("elapsed_ms"),
        "body_recorded": False,
    }


def _sanitize_error(error):
    if error is None:
        return None
    return error.__class__.__name__


def _mask_ref(value):
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:3]}***{value[-3:]}"


def _manual_next_step(decision):
    if decision == "manual_call_completed":
        return "Review sanitized evidence and keep adapter-run real mode blocked."
    if decision == "client_error_after_send":
        return "Review sanitized client error evidence without recording response details."
    return "Keep the manual QA4 call blocked and correct guardrail failures."


def _result(
    decision,
    blocked_reasons,
    request_data,
    runtime_result,
    allowlist_result,
    risk_result,
    readiness_result,
    client_response,
):
    sanitized_log = {
        "api_id": request_data.get("api_id"),
        "method": request_data.get("method"),
        "environment": request_data.get("environment"),
        "decision": decision,
        "blocked_reasons": list(blocked_reasons),
        "runtime_valid": runtime_result.get("valid") is True,
        "allowlist_valid": allowlist_result.get("valid") is True,
        "risk_status": risk_result.get("risk_status"),
        "readiness_decision": readiness_result.get("decision"),
        "client": "fake" if client_response else "not-called",
        "real_call_executed": False,
    }
    return {
        "decision": decision,
        "allowed": decision == "prepared_with_fake_client",
        "blocked_reasons": list(blocked_reasons),
        "sanitized_request": client_response.get("request") if client_response else {},
        "sanitized_log": sanitized_log,
        "risk": risk_result,
        "readiness": readiness_result,
        "runtime": runtime_result.get("sanitized_runtime"),
        "allowlist": allowlist_result.get("allowlist_item"),
        "client_response": _sanitized_client_response(client_response),
        "real_call_executed": False,
        "next_step": _next_step(decision),
    }


def _sanitized_client_response(client_response):
    if not client_response:
        return {}
    return {
        "client": client_response.get("client"),
        "status_code": client_response.get("status_code"),
        "simulated": client_response.get("simulated") is True,
    }


def _next_step(decision):
    if decision == "prepared_with_fake_client":
        return "Review sanitized fake-client evidence before any future approved MVP."
    return "Keep the future QA4 call blocked and correct guardrail failures."


def _dedupe_sorted(items):
    return sorted(set(item for item in items if item))


def _copy_value(value):
    if isinstance(value, dict):
        return {key: _copy_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_value(item) for item in value]
    return value
