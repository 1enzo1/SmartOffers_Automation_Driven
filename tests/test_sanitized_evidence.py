import json
from pathlib import Path
from uuid import uuid4

from core.real_execution.sanitized_evidence import (
    load_sanitized_real_run_evidence,
    list_sanitized_real_run_evidence,
    persist_sanitized_real_run_evidence,
)


def test_real_run_evidence_is_immutable_allowlisted_and_redacted(monkeypatch):
    monkeypatch.setenv("SMARTOFFERS_SOURCE_REVISION", "abc123")
    report = {
        "result": "PASS",
        "executor_send_attempted": True,
        "offers_adapter": {"attempts_used": 1, "password": "never-store"},
        "evidence": {
            "http_status": 201,
            "response_received": True,
            "endpoint": "https://must-not-appear",
            "offer": "must-not-appear",
        },
    }
    context = {
        "run_id": "ALPHA_REAL_RUN_02",
        "environment": "qa4",
        "operation": "CREATE_OFFERS_CUSTOMER",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "static_preflight": "READY",
        "operational_preflight": "READY",
        "destination_attestation": "READY",
        "authorization_verification": "READY",
        "bda_discovery_executed": True,
        "bda_read_only_confirmed": True,
        "test_offer_ready": True,
        "atomic_in_process_handoff": True,
        "standard_runner_real_path": True,
        "msisdn": "must-not-appear",
    }

    evidence_root = Path("evidencias") / f"test-sanitized-{uuid4().hex}"
    saved = persist_sanitized_real_run_evidence(report, context=context, evidence_root=evidence_root)
    path = evidence_root / "real-controlled" / f"{saved['run_id']}.json"
    content = path.read_text(encoding="utf-8")
    record = json.loads(content)

    assert saved["recorded"] is True
    assert record["environment"] == "QA4"
    assert record["run_id"] == "ALPHA_REAL_RUN_02"
    assert record["evidence_capture_version"] == "2"
    assert record["bda_discovery_executed"] is True
    assert record["bda_read_only_confirmed"] is True
    assert record["test_offer_ready"] is True
    assert record["atomic_in_process_handoff"] is True
    assert record["standard_runner_real_path"] is True
    assert record["http_status_class"] == "2xx"
    assert record["attempts_before"] == 0
    assert record["attempts_after"] == 1
    assert record["retry_count"] == 0
    assert record["attempt_ledger"] == {"attempts_used": 1, "max_attempts": 1, "retry_count": 0}
    assert record["source_revision"] == "abc123"
    assert "must-not-appear" not in content
    assert "password" not in content
    path.unlink()
    path.parent.rmdir()
    evidence_root.rmdir()


def test_evidence_writer_does_not_create_an_artifact_without_a_send_attempt():
    evidence_root = Path("evidencias") / f"test-no-send-{uuid4().hex}"

    result = persist_sanitized_real_run_evidence(
        {"result": "BLOCKED", "executor_send_attempted": False},
        context={"environment": "qa4"},
        evidence_root=evidence_root,
    )

    assert result == {"recorded": False, "reason": "REQUEST_NOT_SENT"}
    assert not evidence_root.exists()


def test_sent_report_without_response_cannot_be_persisted_as_pass():
    evidence_root = Path("evidencias") / f"test-sent-without-response-{uuid4().hex}"
    saved = persist_sanitized_real_run_evidence(
        {"result": "PASS", "executor_send_attempted": True, "evidence": {"response_received": False}},
        context={"run_id": "ALPHA_REAL_RUN_02", "environment": "qa4"},
        evidence_root=evidence_root,
    )
    path = evidence_root / "real-controlled" / "ALPHA_REAL_RUN_02.json"
    record = json.loads(path.read_text(encoding="utf-8"))

    assert saved["recorded"] is True
    assert record["result"] == "FAIL"
    assert record["attempts_after"] == 1
    assert record["attempt_ledger"]["attempts_used"] == 1
    path.unlink()
    path.parent.rmdir()
    evidence_root.rmdir()


def test_public_evidence_reader_uses_fixed_run_ids_and_field_allowlist():
    root = Path("evidencias") / f"test-public-reader-{uuid4().hex}"
    directory = root / "real-controlled"
    directory.mkdir(parents=True)
    (directory / "ALPHA_REAL_RUN_02.json").write_text(json.dumps({
        "run_id": "ALPHA_REAL_RUN_02", "environment": "QA4", "result": "FAIL",
        "endpoint": "must-not-leak", "password": "must-not-leak",
    }), encoding="utf-8")

    public = load_sanitized_real_run_evidence("ALPHA_REAL_RUN_02", evidence_root=root)

    assert public["run_id"] == "ALPHA_REAL_RUN_02"
    assert public["result"] == "FAIL"
    assert public["consistency_reason"] == "REQUEST_NOT_CONFIRMED"
    assert "endpoint" not in public
    assert "password" not in public
    assert load_sanitized_real_run_evidence("../ALPHA_REAL_RUN_02", evidence_root=root) is None
    (directory / "ALPHA_REAL_RUN_02.json").unlink()
    directory.rmdir()
    root.rmdir()


def test_public_reader_normalizes_the_persisted_run_02_inconsistency_shape():
    root = Path("evidencias") / f"test-run-02-shape-{uuid4().hex}"
    directory = root / "real-controlled"
    directory.mkdir(parents=True)
    (directory / "ALPHA_REAL_RUN_02.json").write_text(json.dumps({
        "run_id": "ALPHA_REAL_RUN_02",
        "request_sent": True,
        "response_received": False,
        "http_status_class": "none",
        "attempts_after": None,
        "result": "PASS",
    }), encoding="utf-8")

    public = load_sanitized_real_run_evidence("ALPHA_REAL_RUN_02", evidence_root=root)

    assert public["result"] == "FAIL"
    assert public["consistency_reason"] == "RESPONSE_NOT_CONFIRMED"
    (directory / "ALPHA_REAL_RUN_02.json").unlink()
    directory.rmdir()
    root.rmdir()


def test_public_evidence_list_only_includes_recognized_existing_records():
    root = Path("evidencias") / f"test-public-list-{uuid4().hex}"
    directory = root / "real-controlled"
    directory.mkdir(parents=True)
    (directory / "ALPHA_REAL_RUN_02.json").write_text(json.dumps({
        "run_id": "ALPHA_REAL_RUN_02", "environment": "QA4", "result": "PASS",
        "request_sent": True, "response_received": True, "http_status_class": "2xx", "attempts_after": 1,
    }), encoding="utf-8")
    (directory / "unrecognized.json").write_text("{}", encoding="utf-8")

    records = list_sanitized_real_run_evidence(evidence_root=root)

    assert records == [{"run_id": "ALPHA_REAL_RUN_02", "timestamp": None, "environment": "QA4", "scenario": None, "result": "PASS", "consistency_reason": ""}]
    (directory / "ALPHA_REAL_RUN_02.json").unlink()
    (directory / "unrecognized.json").unlink()
    directory.rmdir()
    root.rmdir()
