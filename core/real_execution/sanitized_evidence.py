"""Local, immutable and deliberately small evidence records for controlled runs.

The writer accepts a runtime report, but serializes only this module's explicit
allowlist.  This prevents transport data or stack-local offer data from being
copied to the local evidence directory.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


_ALLOWED_RESULTS = {"PASS", "FAIL", "BLOCKED"}
EVIDENCE_CAPTURE_VERSION = "2"
_ALLOWED_RUN_IDS = {"ALPHA_REAL_RUN_01", "ALPHA_REAL_RUN_02"}


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
    status = evidence.get("http_status")
    status_class = _status_class(status)
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
        "response_received": evidence.get("response_received") is True,
        "http_status_class": status_class,
        "attempts_before": 0,
        "attempts_after": _attempt_ledger(adapter, evidence)["attempts_used"],
        "attempt_ledger": _attempt_ledger(adapter, evidence),
        "retry_count": 0,
        "result": result,
        "standard_runner_real_path": context.get("standard_runner_real_path") is True,
        "source_revision": _source_revision(),
    }


def _qa4_only(value):
    return "QA4" if str(value).lower() == "qa4" else "UNKNOWN"


def _constant_or_empty(value, expected):
    return expected if value == expected else ""


def _terminal_preflight(value):
    return value if value in {"READY", "PASS", "BLOCKED", "NOT_RUN"} else "NOT_RECORDED"


def _status_class(value):
    try:
        code = int(value)
    except (TypeError, ValueError):
        return "none"
    return f"{code // 100}xx" if 100 <= code <= 599 else "none"


def _attempt_ledger(adapter, evidence):
    attempts = adapter.get("attempts_used", evidence.get("attempts_used"))
    return {"attempts_used": int(attempts) if isinstance(attempts, int) else None, "max_attempts": 1, "retry_count": 0}


def _source_revision():
    value = os.environ.get("SMARTOFFERS_SOURCE_REVISION", "").strip()
    # A revision is an identifier, never arbitrary environment content.
    return value if value and all(char.isalnum() or char in "._-" for char in value) else "NOT_AVAILABLE"
