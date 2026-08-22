"""Guarded QA4 SmartOffers API health checkpoint with no default real execution."""

import argparse
import importlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from core.real_execution.api_health_local_runtime_preflight import (
    API_CHECKPOINT,
    API_ENVIRONMENT,
    API_OPERATION_ID,
    API_PROFILE,
    API_REQUIRED_REFS,
    API_RESOURCE_ID,
    API_RUNTIME_READY,
    preflight_api_health_local_runtime,
)
from core.real_execution.gate_dag import (
    DB_CHECKPOINT_GATES_READY,
    validate_api_db_gate_bundle,
)


API_HEALTH_CHECKPOINT_OK = "SMARTOFFERS_API_QA4_CHECKPOINT_OK"
API_HEALTH_CHECKPOINT_FAILED = "SMARTOFFERS_API_QA4_CHECKPOINT_FAILED"
API_HEALTH_CHECKPOINT_BLOCKED = "SMARTOFFERS_API_QA4_CHECKPOINT_BLOCKED"
_APPROVAL = "EXECUTION_APPROVED"
_OPERATIONAL_RELEASE = "OPERATIONAL_EXECUTION_RELEASED"
_MAX_RESPONSE_BYTES = 1024


class _Blocked(Exception):
    def __init__(self, category):
        super().__init__(category)
        self.category = category


class FakeResponse:
    """In-memory response used by all automated tests."""

    def __init__(self, status_code=200, body=b"", headers=None):
        self.status_code = status_code
        self._body = bytes(body)
        self._headers = dict(headers or {})

    def bounded_body_size(self, limit):
        return min(len(self._body), limit + 1)


class FakeHttpClient:
    """Network-free transport double for the API checkpoint."""

    is_fake_http_client = True

    def __init__(self, response=None, error=None):
        self.response = response or FakeResponse()
        self.error = error
        self.calls = []

    def send(self, request):
        self.calls.append(dict(request))
        if self.error is not None:
            raise self.error
        return self.response


class _RedirectDenyHttpClient:
    """Lazy real transport. It sends one GET and never follows a redirect."""

    is_real_http_client = True

    def send(self, request):
        http_client = importlib.import_module("http.client")
        endpoint = request["endpoint"]
        parsed = urlsplit(endpoint)
        connection_class = (
            http_client.HTTPSConnection if parsed.scheme == "https" else http_client.HTTPConnection
        )
        connection = connection_class(parsed.netloc, timeout=request["connect_timeout"])
        try:
            connection.request("GET", request["path"], headers={})
            response = connection.getresponse()
            if getattr(connection, "sock", None) is not None:
                connection.sock.settimeout(request["read_timeout"])
            body = response.read(request["max_response_bytes"] + 1)
            return _TransportResponse(response.status, len(body))
        finally:
            connection.close()


class _TransportResponse:
    def __init__(self, status_code, body_size):
        self.status_code = status_code
        self._body_size = body_size

    def bounded_body_size(self, limit):
        return self._body_size


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _Blocked("CONFIG_MISSING")


def build_parser():
    parser = _ArgumentParser(add_help=False)
    for name in ("checkpoint", "api-operation-id", "environment", "profile", "resource-id", "method"):
        parser.add_argument(f"--{name}", required=True)
    for name in ("attempts", "retry", "connect-timeout", "read-timeout", "total-timeout", "max-response-bytes"):
        parser.add_argument(f"--{name}", required=True, type=int)
    for name in (
        "redirects", "fallback", "payload-allowed", "query-parameters-allowed",
        "path-parameters-allowed", "customer-identifiers-allowed", "authentication-required",
    ):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--acm-custom-db-checkpoint-status")
    parser.add_argument("--acm-db-checkpoint-status")
    parser.add_argument("--bda-db-checkpoint-status")
    parser.add_argument("--basic-db-checkpoint-status")
    parser.add_argument("--operational-window-active", required=True)
    parser.add_argument("--approval", required=True)
    parser.add_argument("--operational-release", required=True)
    parser.add_argument("--preflight-status", required=True)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        result = run_api_health_checkpoint(vars(args))
    except _Blocked as error:
        result = _result(API_HEALTH_CHECKPOINT_BLOCKED, error.category, 0)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == API_HEALTH_CHECKPOINT_OK else 1


def run_api_health_checkpoint(arguments, environ=None, client=None, clock=None):
    """Run exactly one approved health GET only after all local gates pass."""
    args = arguments if isinstance(arguments, dict) else {}
    environment = environ if environ is not None else os.environ
    monotonic = clock or time.monotonic
    started = monotonic()
    validations = _denied_validations()
    try:
        _validate_arguments(args)
        validations["db_gate_bundle_validation"] = "MATCH"
        runtime = _load_runtime(environment)
        preflight = _validate_preflight(args, environment)
        validations.update(
            {
                "allowlist_validation": preflight["allowlist_validation"],
                "preflight_validation": "MATCH",
                "path_validation": preflight["path_validation"],
                "path_hash_validation": preflight["path_hash_validation"],
                "fingerprint_validation": preflight["fingerprint_validation"],
            }
        )
        _validate_destination(runtime)
        _ensure_total_timeout(started, args, monotonic)
        active_client = client if client is not None else _load_real_http_client()
        response = active_client.send(_transport_request(runtime, args))
        _ensure_total_timeout(started, args, monotonic)
        status = int(response.status_code)
        if 300 <= status < 400:
            raise _Blocked("REDIRECT_DENIED")
        if status != 200:
            return _result(
                API_HEALTH_CHECKPOINT_FAILED,
                "AUTHENTICATION_ERROR" if status in (401, 403) else "HTTP_STATUS_DENIED",
                _elapsed_ms(started, monotonic),
                validations,
            )
        if response.bounded_body_size(args["max_response_bytes"]) > args["max_response_bytes"]:
            return _result(
                API_HEALTH_CHECKPOINT_FAILED,
                "RESPONSE_LIMIT_EXCEEDED",
                _elapsed_ms(started, monotonic),
                validations,
            )
        return _result(
            API_HEALTH_CHECKPOINT_OK,
            "NONE",
            _elapsed_ms(started, monotonic),
            validations,
        )
    except _Blocked as error:
        return _result(
            API_HEALTH_CHECKPOINT_BLOCKED,
            error.category,
            _elapsed_ms(started, monotonic),
            validations,
        )
    except Exception as error:
        return _result(
            API_HEALTH_CHECKPOINT_FAILED,
            _classify_transport_error(error),
            _elapsed_ms(started, monotonic),
            validations,
        )


def _validate_arguments(args):
    bundle = validate_api_db_gate_bundle(
        args.get("db_checkpoint_gates"),
        args.get("orchestration_context"),
        evaluated_at=args.get("gate_evaluated_at"),
    )
    if bundle["status"] != DB_CHECKPOINT_GATES_READY:
        raise _Blocked("DB_CHECKPOINT_GATE_MISSING")

    expected = {
        "checkpoint": API_CHECKPOINT,
        "api_operation_id": API_OPERATION_ID,
        "environment": API_ENVIRONMENT,
        "profile": API_PROFILE,
        "resource_id": API_RESOURCE_ID,
        "method": "GET",
        "approval": _APPROVAL,
        "operational_release": _OPERATIONAL_RELEASE,
        "preflight_status": API_RUNTIME_READY,
    }
    if not _is_true(args.get("operational_window_active")):
        raise _Blocked("OPERATIONAL_WINDOW_INACTIVE")
    for name, value in expected.items():
        if args.get(name) != value:
            if name in {"approval", "operational_release"}:
                raise _Blocked("APPROVAL_MISSING")
            if name == "preflight_status":
                raise _Blocked("PREFLIGHT_DENIED")
            raise _Blocked("ALLOWLIST_DENIED")
    if args.get("attempts") != 1 or args.get("retry") != 0:
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if (
        args.get("connect_timeout") != 5
        or args.get("read_timeout") != 5
        or args.get("total_timeout") != 15
        or args.get("max_response_bytes") != _MAX_RESPONSE_BYTES
    ):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if any(
        not _is_false(args.get(name))
        for name in (
            "redirects", "fallback", "payload_allowed", "query_parameters_allowed",
            "path_parameters_allowed", "customer_identifiers_allowed",
        )
    ):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")
    if not _is_false(args.get("authentication_required")):
        raise _Blocked("AUTHENTICATION_UNCONFIRMED")


def _validate_preflight(args, environment):
    result = preflight_api_health_local_runtime(
        {
            "checkpoint": args["checkpoint"],
            "api_operation_id": args["api_operation_id"],
            "environment": args["environment"],
            "profile": args["profile"],
            "resource_id": args["resource_id"],
        },
        environment,
    )
    if result["status"] == API_RUNTIME_READY:
        return result
    if result["missing_refs"]:
        raise _Blocked("CONFIG_MISSING")
    if result["fingerprint_validation"] == "DENIED":
        raise _Blocked("FINGERPRINT_DENIED")
    if result["path_hash_validation"] == "DENIED":
        raise _Blocked("PATH_HASH_DENIED")
    raise _Blocked("PREFLIGHT_DENIED")


def _load_runtime(environment):
    missing = [ref for ref in API_REQUIRED_REFS if not str(environment.get(ref) or "").strip()]
    if missing:
        raise _Blocked("CONFIG_MISSING")
    return {
        "endpoint": str(environment["SMARTOFFERS_QA4_API_URL"]),
        "path": str(environment["SMARTOFFERS_QA4_API_HEALTH_PATH"]),
    }


def _validate_destination(runtime):
    parsed = urlsplit(runtime["endpoint"])
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise _Blocked("ALLOWLIST_DENIED")
    path = runtime["path"].strip()
    if not path.startswith("/") or any(marker in path for marker in ("?", "#", "{", "}", "<", ">")):
        raise _Blocked("READ_ONLY_POLICY_VIOLATION")


def _transport_request(runtime, args):
    return {
        "endpoint": runtime["endpoint"],
        "path": runtime["path"].strip(),
        "method": "GET",
        "connect_timeout": args["connect_timeout"],
        "read_timeout": args["read_timeout"],
        "total_timeout": args["total_timeout"],
        "max_response_bytes": args["max_response_bytes"],
    }


def _load_real_http_client():
    return _RedirectDenyHttpClient()


def _ensure_total_timeout(started, args, monotonic):
    if monotonic() - started > args["total_timeout"]:
        raise _Blocked("TOTAL_TIMEOUT")


def _is_false(value):
    return value is False or value == "false"


def _is_true(value):
    return value is True or value == "true"


def _elapsed_ms(started, monotonic):
    return max(0, int((monotonic() - started) * 1000))


def _classify_transport_error(error):
    class_name = error.__class__.__name__.lower()
    if "connect" in class_name and "timeout" in class_name:
        return "CONNECT_TIMEOUT"
    if "read" in class_name and "timeout" in class_name:
        return "READ_TIMEOUT"
    if isinstance(error, TimeoutError):
        return "TOTAL_TIMEOUT"
    if isinstance(error, PermissionError):
        return "AUTHENTICATION_ERROR"
    return "HTTP_TRANSPORT_ERROR"


def _denied_validations():
    return {
        "allowlist_validation": "DENIED",
        "preflight_validation": "DENIED",
        "path_validation": "DENIED",
        "path_hash_validation": "DENIED",
        "fingerprint_validation": "DENIED",
        "db_gate_bundle_validation": "DENIED",
        "response_body_logged": False,
        "response_headers_logged": False,
        "sensitive_values_logged": False,
    }


def _result(status, error_category, elapsed_ms, validations=None):
    validation_metadata = _denied_validations()
    if isinstance(validations, dict):
        validation_metadata.update(validations)
    return {
        "execution_id": uuid.uuid4().hex,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "checkpoint": API_CHECKPOINT,
        "api_operation_id": API_OPERATION_ID,
        "environment": API_ENVIRONMENT,
        "profile": API_PROFILE,
        "resource_id": API_RESOURCE_ID,
        "method": "GET",
        "status": status,
        "attempts_used": 1,
        "retry_count": 0,
        "connect_timeout_seconds": 5,
        "read_timeout_seconds": 5,
        "total_timeout_seconds": 15,
        "max_response_bytes": _MAX_RESPONSE_BYTES,
        "elapsed_ms": elapsed_ms,
        **validation_metadata,
        "sanitized_error_category": error_category,
        "stop_reason": "CHECKPOINT_COMPLETED" if status == API_HEALTH_CHECKPOINT_OK else "IMMEDIATE_STOP",
    }


if __name__ == "__main__":
    raise SystemExit(main())
