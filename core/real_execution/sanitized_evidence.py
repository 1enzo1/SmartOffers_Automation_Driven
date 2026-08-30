"""Local, immutable and deliberately small evidence records for controlled runs.

The writer accepts a runtime report, but serializes only this module's explicit
allowlist.  This prevents transport data or stack-local offer data from being
copied to the local evidence directory.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


_ALLOWED_RESULTS = {"PASS", "FAIL", "BLOCKED"}
EVIDENCE_CAPTURE_VERSION = "2"
_ALLOWED_RUN_IDS = {"ALPHA_REAL_RUN_01", "ALPHA_REAL_RUN_02", "ALPHA_REAL_RUN_03A"}
_PUBLIC_FIELDS = (
    "run_id",
    "timestamp",
    "environment",
    "operation",
    "scenario",
    "static_preflight",
    "operational_preflight",
    "destination_attestation",
    "authorization_verification",
    "bda_discovery_executed",
    "bda_read_only_confirmed",
    "test_offer_ready",
    "atomic_in_process_handoff",
    "request_sent",
    "response_received",
    "http_status_class",
    "attempts_before",
    "attempts_after",
    "retry_count",
    "result",
    "standard_runner_real_path",
    "product_test_name",
    "db_postcondition_verified",
    "db_validation_status",
    "source_revision",
    "evidence_capture_version",
)


def persist_sanitized_real_run_evidence(report, *, context, evidence_root="evidencias"):
    """Write one append-only sanitized result artifact and return its reference.

    Raises ``OSError`` to the caller when local persistence is unavailable.  A
    caller must report that failure rather than claiming evidence was captured.
    """
    report = report if isinstance(report, dict) else {}
    if report.get("executor_send_attempted") is not True:
        return {"recorded": False, "reason": "REQUEST_NOT_SENT"}

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    requested_run_id = context.get("run_id") if isinstance(context, dict) else None
    run_id = requested_run_id if requested_run_id in _ALLOWED_RUN_IDS else "run-" + uuid4().hex
    record = _record(report, context, run_id=run_id, timestamp=timestamp)
    destination = Path(evidence_root) / "real-controlled" / f"{run_id}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    # x mode is intentional: an evidence ID is never silently overwritten.
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    return {"recorded": True, "reference": str(destination), "run_id": run_id}


def _record(report, context, *, run_id, timestamp):
    report = report if isinstance(report, dict) else {}
    context = context if isinstance(context, dict) else {}
    adapter = report.get("offers_adapter") if isinstance(report.get("offers_adapter"), dict) else {}
    evidence = report.get("evidence") if isinstance(report.get("evidence"), dict) else {}
    result = report.get("result") if report.get("result") in _ALLOWED_RESULTS else "BLOCKED"
    status = evidence.get("http_status", evidence.get("status_code"))
    status_class = _status_class(status)
    response_received = evidence.get("response_received") is True
    # A transport report without a response and a success status can never be
    # recorded as a successful run.
    if result == "PASS" and not (response_received and status_class == "2xx"):
        result = "FAIL"
    attempt_ledger = _attempt_ledger(adapter, evidence)
    return {
        "schema_version": "1",
        "evidence_capture_version": EVIDENCE_CAPTURE_VERSION,
        "run_id": run_id,
        "timestamp": timestamp,
        "environment": _qa4_only(context.get("environment")),
        "operation": _constant_or_empty(context.get("operation"), "CREATE_OFFERS_CUSTOMER"),
        "scenario": _constant_or_empty(context.get("scenario_id"), "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4"),
        "static_preflight": _terminal_preflight(context.get("static_preflight")),
        "operational_preflight": _terminal_preflight(context.get("operational_preflight")),
        "destination_attestation": _terminal_preflight(context.get("destination_attestation")),
        "authorization_verification": _terminal_preflight(context.get("authorization_verification")),
        "bda_discovery_executed": context.get("bda_discovery_executed") is True,
        "bda_read_only_confirmed": context.get("bda_read_only_confirmed") is True,
        "test_offer_ready": context.get("test_offer_ready") is True,
        "atomic_in_process_handoff": context.get("atomic_in_process_handoff") is True,
        "request_sent": report.get("executor_send_attempted") is True,
        "response_received": response_received,
        "http_status_class": status_class,
        "attempts_before": attempt_ledger["attempts_before"],
        "attempts_after": attempt_ledger["attempts_after"],
        "attempt_ledger": {
            "attempts_used": attempt_ledger["attempts_used"],
            "max_attempts": attempt_ledger["max_attempts"],
            "retry_count": attempt_ledger["retry_count"],
        },
        "retry_count": 0,
        "result": result,
        "standard_runner_real_path": context.get("standard_runner_real_path") is True,
        "product_test_name": _product_test_name(context.get("product_test_name")),
        "db_postcondition_verified": context.get("db_postcondition_verified") is True,
        "db_validation_status": _db_validation_status(context.get("db_validation_status")),
        "source_revision": _source_revision(context.get("source_revision")),
    }


def _qa4_only(value):
    return "QA4" if str(value).lower() == "qa4" else "UNKNOWN"


def _constant_or_empty(value, expected):
    return expected if value == expected else ""


def _terminal_preflight(value):
    return value if isinstance(value, str) and value in {"READY", "PASS", "BLOCKED", "NOT_RUN"} else "NOT_RECORDED"


def _product_test_name(value):
    return "Create Customer with Offer" if value == "Create Customer with Offer" else ""


def _db_validation_status(value):
    return "NOT_CONFIGURED" if value == "NOT_CONFIGURED" else "NOT_RECORDED"


def _status_class(value):
    try:
        code = int(value)
    except (TypeError, ValueError):
        return "none"
    return f"{code // 100}xx" if 100 <= code <= 599 else "none"


def _attempt_ledger(adapter, evidence):
    snapshot = adapter.get("attempt_ledger") if isinstance(adapter.get("attempt_ledger"), dict) else {}
    attempts = snapshot.get("attempts_used", adapter.get("attempts_used", evidence.get("attempts_used")))
    # The writer is only invoked after ``executor_send_attempted``.  The
    # executor reserves the one-shot immediately before send, so older
    # compatibility callers without its new snapshot still retain the factual
    # post-send one-shot state.
    used = int(attempts) if isinstance(attempts, int) else 1
    return {
        "attempts_before": snapshot.get("attempts_before", 0),
        "attempts_used": used,
        "attempts_after": snapshot.get("attempts_after", used),
        "max_attempts": snapshot.get("max_attempts", 1),
        "retry_count": snapshot.get("retry_count", 0),
    }


def load_sanitized_real_run_evidence(run_id, *, evidence_root="evidencias"):
    """Return the public, allowlisted view of one persisted evidence record.

    Run IDs are intentionally an enum rather than a path component supplied by
    callers.  This keeps the UI endpoint read-only and prevents traversal or
    accidental presentation of raw runtime output.
    """
    if run_id not in _ALLOWED_RUN_IDS:
        return None
    path = Path(evidence_root) / "real-controlled" / f"{run_id}.json"
    try:
        with path.open(encoding="utf-8") as handle:
            record = json.load(handle)
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(record, dict) or record.get("run_id") != run_id:
        return None
    if not _persisted_record_shape_is_safe(record):
        return None
    public = {field: record.get(field) for field in _PUBLIC_FIELDS}
    consistency_reason = _public_consistency_reason(public)
    if consistency_reason:
        # Keep the original local artifact immutable while refusing to surface a
        # contradictory success result as a successful run in the product UI.
        public["result"] = "FAIL"
        public["consistency_reason"] = consistency_reason
    return public


def _persisted_record_shape_is_safe(record):
    """Reject malformed persisted data before applying the public allowlist."""
    if "result" not in record or record["result"] not in _ALLOWED_RESULTS:
        return False
    status_class = record.get("http_status_class")
    if status_class is not None and status_class not in {"2xx", "3xx", "4xx", "5xx", "1xx", "none"}:
        return False
    for field in ("static_preflight", "operational_preflight", "destination_attestation", "authorization_verification"):
        if field in record and (not isinstance(record[field], str) or record[field] not in {"READY", "PASS", "BLOCKED", "NOT_RUN", "NOT_RECORDED"}):
            return False
    timestamp = record.get("timestamp")
    if timestamp is not None:
        if not isinstance(timestamp, str):
            return False
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return False
    for field in ("request_sent", "response_received"):
        if field in record and type(record[field]) is not bool:
            return False
    for field in ("attempts_before", "attempts_after", "retry_count"):
        if field in record and record[field] is not None and (type(record[field]) is not int or record[field] < 0):
            return False
    ledger = record.get("attempt_ledger")
    if ledger is not None:
        if not isinstance(ledger, dict):
            return False
        for field in ("attempts_used", "max_attempts", "retry_count"):
            if field in ledger and ledger[field] is not None and (type(ledger[field]) is not int or ledger[field] < 0):
                return False
    return True


def list_sanitized_real_run_evidence(*, evidence_root="evidencias"):
    """List only existing, recognized public evidence records."""
    records = []
    for run_id in sorted(_ALLOWED_RUN_IDS):
        record = load_sanitized_real_run_evidence(run_id, evidence_root=evidence_root)
        if record is not None:
            records.append({
                "run_id": record["run_id"],
                "timestamp": record["timestamp"],
                "environment": record["environment"],
                "scenario": record["scenario"],
                "result": record["result"],
                "consistency_reason": record.get("consistency_reason", ""),
            })
    return records


def _public_consistency_reason(record):
    if record.get("request_sent") is not True:
        return "REQUEST_NOT_CONFIRMED"
    if record.get("response_received") is not True:
        return "RESPONSE_NOT_CONFIRMED"
    if record.get("http_status_class") != "2xx":
        return "SUCCESS_STATUS_NOT_CONFIRMED"
    if record.get("attempts_after") != 1:
        return "ONE_SHOT_CONSUMPTION_NOT_CONFIRMED"
    return ""


def _source_revision(value):
    value = str(value or "").strip()
    # A revision is an identifier, never arbitrary environment content.
    return value if value and all(char.isalnum() or char in "._-" for char in value) else "NOT_AVAILABLE"
