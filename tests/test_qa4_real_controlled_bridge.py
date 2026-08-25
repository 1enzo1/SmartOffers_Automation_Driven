from pathlib import Path

import app as app_module
from core.real_execution import qa4_real_controlled_bridge


EVALUATED_AT = "2026-08-25T12:00:00+00:00"


def _context():
    return {
        "environment": "qa4",
        "workflow_profile": "smartoffers_qa4_full_smoke",
        "orchestration_id": "alpha-bridge-ref",
        "operational_window_ref": "qa4-window-ref",
        "window_started_at": "2026-08-25T11:55:00+00:00",
        "window_expires_at": "2026-08-25T12:05:00+00:00",
    }


def test_real_controlled_bridge_runs_standard_facade_then_blocks_before_fake_send(monkeypatch):
    facade_calls = []

    def facade(context, *, mode, evaluated_at):
        facade_calls.append((context, mode, evaluated_at))
        return {"result": "PASS", "full": {"status": "FULL_SMOKE_OK"}}

    monkeypatch.setattr(qa4_real_controlled_bridge, "run_standard_qa4_application_mock", facade)

    result = qa4_real_controlled_bridge.run_standard_qa4_real_controlled(
        _context(), mode="real-controlled", evaluated_at=EVALUATED_AT
    )

    assert facade_calls == [(_context(), "mock", EVALUATED_AT)]
    assert result["result"] == "BLOCKED"
    assert result["standard_report"]["result"] == "PASS"
    assert result["real_call_executed"] is False
    assert result["fake_client_send_calls"] == 0
    assert result["blockers"] == [
        "REAL_QA4_OPERATION_NOT_CONFIRMED",
        "QA4_TEST_DATA_REQUIRED",
        "QA4_CREDENTIAL_OR_CONFIG_REQUIRED",
    ]
    assert "secret" not in str(result).lower()
    assert "payload" not in str(result).lower()


def test_real_controlled_bridge_has_no_transport_imports():
    source = Path("core/real_execution/qa4_real_controlled_bridge.py").read_text()

    for forbidden in (
        "import requests",
        "from requests",
        "import urllib",
        "import socket",
        "RealHttpClient",
    ):
        assert forbidden not in source


def test_real_controlled_api_entry_returns_sanitized_blocked_bridge(app_client_factory, monkeypatch):
    client, _ = app_client_factory("qa4-real-controlled")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_real_controlled",
        lambda context, *, mode, evaluated_at: {
            "result": "BLOCKED",
            "standard_report": {"result": "PASS"},
            "blockers": ["REAL_QA4_OPERATION_NOT_CONFIRMED"],
            "real_call_executed": False,
            "fake_client_send_calls": 0,
        },
    )

    response = client.post(
        "/api/qa4/standard/real-controlled-run",
        json={
            **_context(),
            "environment": "QA4",
            "mode": "real-controlled",
            "evaluated_at": EVALUATED_AT,
            "secret": "must-not-appear",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["result"] == "BLOCKED"
    assert "must-not-appear" not in response.get_data(as_text=True)
