from core.real_execution.allowlist import build_first_qa4_allowlist, validate_first_qa4_allowlist
from core.real_execution.http_client import is_fake_client
from core.real_execution.policy import build_readiness_policy
from core.real_execution.readiness import evaluate_real_execution_readiness
from core.real_execution.runtime import validate_runtime_contract
from core.risk import classify_adapter_risk


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


def _risk_work_item(request_data):
    return {
        "api_id": request_data.get("api_id"),
        "method": request_data.get("method"),
        "environment": request_data.get("environment"),
        "planning_mode": "first_qa4_fake_only",
        "evidence_layer": "read-only readiness",
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
