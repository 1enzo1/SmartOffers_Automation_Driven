import json
import uuid
from pathlib import Path

import pytest

from core.execution.service import AdapterRunModeError, run_adapter_scenario
from core.legacy_execution import service
from core.utils.evidence_response_contract import analyze_smartoffers_response


def test_blocked_guard_output_is_classified_as_blocked():
    process_factory, _ = _fake_process_factory(
        [
            (
                "Execucao real bloqueada. Defina "
                "SMARTOFFERS_ALLOW_LEGACY_REAL_SCRIPT=YES_I_UNDERSTAND."
            )
        ],
        returncode=1,
    )

    events = _collect_events(
        service.stream_legacy_execution(
            "variante",
            analisar=False,
            process_factory=process_factory,
        )
    )

    assert any(event.startswith("ERROR|Execucao real bloqueada") for event in events)
    assert "RUN|END|BLOCKED|0|1" in events


def test_execution_route_reports_blocked_instead_of_pass(app_client_factory, monkeypatch):
    process_factory, _ = _fake_process_factory(
        ["Execucao real bloqueada. Defina SMARTOFFERS_ALLOW_LEGACY_REAL_SCRIPT=YES_I_UNDERSTAND."],
        returncode=1,
    )
    monkeypatch.setattr(service.subprocess, "Popen", process_factory)
    client, _ = app_client_factory("legacy_result_semantics")

    response = client.get("/executar?tipo=variante&analisar=false", buffered=True)
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "RUN|END|BLOCKED|0|1" in body
    assert "RUN|END|PASS" not in body


def test_exit_code_zero_with_error_response_is_fail():
    scenario = _scenario_folder(
        {"status": "Error", "result": False, "uniqueId": None, "event": {}}
    )
    process_factory, _ = _fake_process_factory(
        [
            f"SCENARIO|START|pos/upsell|1|CASE_ID|{scenario}",
            "STEP|pos/upsell|1|01_response",
            f"SCENARIO|END|pos/upsell|1|CASE_ID|{scenario}",
        ],
        returncode=0,
    )

    events = _collect_events(
        service.stream_legacy_execution(
            "copy",
            analisar=True,
            process_factory=process_factory,
        )
    )

    assert any("SmartOffers functional response failure" in event for event in events)
    assert _last_run_end(events) == "RUN|END|FAIL|1|1"


def test_http_200_with_result_false_is_functional_fail():
    result = analyze_smartoffers_response(
        {
            "status_code": 200,
            "body": {
                "status": "Success",
                "result": False,
                "uniqueId": "UNIQUE_TEST_ID",
                "event": {"name": "synthetic"},
            },
        }
    )

    assert result["status"] == "FAIL"
    assert "result_false" in result["issues"]


def test_success_response_at_root_is_pass():
    result = analyze_smartoffers_response(
        {
            "status": "Success",
            "result": True,
            "uniqueId": "UNIQUE_TEST_ID",
        }
    )

    assert result["status"] == "PASS"
    assert result["location"] == "root"


def test_success_response_inside_body_is_pass():
    scenario = _scenario_folder(
        {
            "body": {
                "status": "Success",
                "result": True,
                "uniqueId": "UNIQUE_TEST_ID",
            }
        },
    )
    process_factory, _ = _fake_process_factory(
        [f"SCENARIO|START|pre|1|CASE_ID|{scenario}"],
        returncode=0,
    )

    events = _collect_events(
        service.stream_legacy_execution(
            "copy",
            analisar=False,
            process_factory=process_factory,
        )
    )

    assert _last_run_end(events) == "RUN|END|PASS|0|0"


def test_started_scenario_without_response_evidence_is_fail():
    scenario = Path(".test_output") / "legacy_result_semantics" / uuid.uuid4().hex / "scenario"
    scenario.mkdir(parents=True, exist_ok=True)
    process_factory, _ = _fake_process_factory(
        [f"SCENARIO|START|pos/upsell|1|CASE_ID|{scenario}"],
        returncode=0,
    )

    events = _collect_events(
        service.stream_legacy_execution(
            "variante",
            analisar=False,
            process_factory=process_factory,
        )
    )

    assert any("SmartOffers response evidence missing" in event for event in events)
    assert _last_run_end(events) == "RUN|END|FAIL|0|1"


def test_missing_unique_id_is_functional_fail():
    result = analyze_smartoffers_response(
        {
            "status": "Success",
            "result": True,
            "uniqueId": None,
        }
    )

    assert result["status"] == "FAIL"
    assert "uniqueId_missing" in result["issues"]


def test_error_response_with_empty_event_is_functional_fail():
    result = analyze_smartoffers_response(
        {
            "status": "Error",
            "result": False,
            "uniqueId": None,
            "event": [],
        }
    )

    assert result["status"] == "FAIL"
    assert "event_empty_on_error" in result["issues"]


def test_runner_does_not_pass_guard_without_explicit_authorization(monkeypatch):
    monkeypatch.setenv(service.LEGACY_REAL_SCRIPT_ENV, service.LEGACY_REAL_SCRIPT_CONFIRMATION)
    process_factory, captured = _fake_process_factory([], returncode=0)

    events = _collect_events(
        service.stream_legacy_execution(
            "variante",
            analisar=False,
            process_factory=process_factory,
        )
    )

    assert service.LEGACY_REAL_SCRIPT_ENV not in captured["env"]
    assert captured["env"]["ANALISAR_EXECUCAO"] == "0"
    assert _last_run_end(events) == "RUN|END|PASS|0|0"


def test_runner_can_pass_guard_with_explicit_authorization(monkeypatch):
    monkeypatch.setenv("SMARTOFFERS_QA4_API_URL", "fake-qa4-api-url")
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_DSN", "fake-qa4-db-dsn")
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_USER", "fake-qa4-db-user")
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_PASSWORD", "fake-qa4-db-password")
    process_factory, captured = _fake_process_factory([], returncode=0)

    events = _collect_events(
        service.stream_legacy_execution(
            "copy",
            analisar=True,
            allow_legacy_real_script=True,
            execution_mode="real_qa_manual",
            environment="qa4",
            real_confirmed=True,
            process_factory=process_factory,
        )
    )

    assert captured["env"][service.LEGACY_REAL_SCRIPT_ENV] == service.LEGACY_REAL_SCRIPT_CONFIRMATION
    assert captured["env"]["ANALISAR_EXECUCAO"] == "1"
    assert captured["env"]["SMARTOFFERS_API_URL"] == "fake-qa4-api-url"
    assert _last_run_end(events) == "RUN|END|PASS|0|0"


def test_adapter_run_real_mode_remains_blocked():
    with pytest.raises(AdapterRunModeError):
        run_adapter_scenario({"id": "synthetic", "execution_steps": []}, mode="real")


def _scenario_folder(response):
    scenario = Path(".test_output") / "legacy_result_semantics" / uuid.uuid4().hex / "scenario"
    scenario.mkdir(parents=True, exist_ok=True)
    (scenario / "01_response.json").write_text(
        json.dumps(response),
        encoding="utf-8",
    )
    return scenario


def _fake_process_factory(lines, returncode=0):
    captured = {}

    def factory(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return _FakeProcess(lines, returncode)

    return factory, captured


class _FakeProcess:
    def __init__(self, lines, returncode):
        self.stdout = [f"{line}\n" for line in lines]
        self.returncode = returncode

    def wait(self):
        return self.returncode


def _collect_events(stream):
    return [event.removeprefix("data:").strip() for event in stream]


def _last_run_end(events):
    return [event for event in events if event.startswith("RUN|END|")][-1]
