import re

import pytest

from core.execution.service import AdapterRunModeError, run_adapter_scenario
from core.legacy_execution import service
from core.legacy_execution.modes import (
    DEFAULT_EXECUTION_MODE,
    EXECUTION_MODE_MOCK,
    EXECUTION_MODE_REAL_QA_MANUAL,
    evaluate_execution_mode_request,
)
from core.real_execution.environments import list_sanitized_qa_environments


def test_default_execution_mode_is_not_real():
    decision = evaluate_execution_mode_request()

    assert DEFAULT_EXECUTION_MODE in {"dry_run", "mock"}
    assert decision["mode"] == EXECUTION_MODE_MOCK
    assert decision["allow_legacy_real_script"] is False
    assert decision["allowed"] is True


@pytest.mark.parametrize("mode", ["dry_run", "mock"])
def test_non_real_modes_do_not_require_environment(mode):
    decision = evaluate_execution_mode_request(mode=mode)

    assert decision["allowed"] is True
    assert decision["status"] == "ALLOWED"
    assert decision["environment"] == ""
    assert decision["allow_legacy_real_script"] is False


def test_real_qa_manual_requires_environment():
    decision = evaluate_execution_mode_request(
        mode=EXECUTION_MODE_REAL_QA_MANUAL,
        real_confirmed=True,
    )

    assert decision["allowed"] is False
    assert decision["status"] == "BLOCKED"
    assert "missing_environment" in decision["blocked_reasons"]


def test_invalid_environment_is_blocked():
    decision = evaluate_execution_mode_request(
        mode=EXECUTION_MODE_REAL_QA_MANUAL,
        environment="prod",
        real_confirmed=True,
    )

    assert decision["allowed"] is False
    assert decision["status"] == "BLOCKED"
    assert "invalid_environment" in decision["blocked_reasons"]


def test_real_without_confirmation_is_blocked_and_does_not_start_process():
    def fail_if_started(*args, **kwargs):
        raise AssertionError("process must not start without explicit real confirmation")

    events = _collect_events(
        service.stream_legacy_execution(
            "variante",
            analisar=False,
            execution_mode=EXECUTION_MODE_REAL_QA_MANUAL,
            environment="qa4",
            real_confirmed=False,
            process_factory=fail_if_started,
        )
    )

    assert any("missing_real_confirmation" in event for event in events)
    assert _last_run_end(events) == "RUN|END|BLOCKED|0|1"


def test_real_with_confirmation_injects_legacy_guard_with_fake_process():
    process_factory, captured = _fake_process_factory([], returncode=0)

    events = _collect_events(
        service.stream_legacy_execution(
            "copy",
            analisar=True,
            execution_mode=EXECUTION_MODE_REAL_QA_MANUAL,
            environment="qa4",
            real_confirmed=True,
            process_factory=process_factory,
        )
    )

    assert captured["env"][service.LEGACY_REAL_SCRIPT_ENV] == service.LEGACY_REAL_SCRIPT_CONFIRMATION
    assert captured["env"]["SMARTOFFERS_EXECUTION_MODE"] == EXECUTION_MODE_REAL_QA_MANUAL
    assert captured["env"]["SMARTOFFERS_QA_ENVIRONMENT"] == "qa4"
    assert _last_run_end(events) == "RUN|END|PASS|0|0"


def test_legacy_allow_flag_without_real_mode_does_not_inject_guard():
    process_factory, captured = _fake_process_factory([], returncode=0)

    events = _collect_events(
        service.stream_legacy_execution(
            "copy",
            analisar=False,
            allow_legacy_real_script=True,
            process_factory=process_factory,
        )
    )

    assert service.LEGACY_REAL_SCRIPT_ENV not in captured["env"]
    assert captured["env"]["SMARTOFFERS_EXECUTION_MODE"] == "mock"
    assert _last_run_end(events) == "RUN|END|PASS|0|0"


def test_dry_run_mode_does_not_start_legacy_process():
    def fail_if_started(*args, **kwargs):
        raise AssertionError("dry_run must not start a subprocess")

    events = _collect_events(
        service.stream_legacy_execution(
            "padrao",
            analisar=False,
            execution_mode="dry_run",
            process_factory=fail_if_started,
        )
    )

    assert "RUN|END|PASS|0|0" in events
    assert any("Dry-run local" in event for event in events)


def test_qa1_qa2_qa3_qa4_exist_in_sanitized_contract():
    environments = list_sanitized_qa_environments()

    assert {environment["id"] for environment in environments} == {"qa1", "qa2", "qa3", "qa4"}


def test_sanitized_contract_versions_only_environment_refs():
    environments = list_sanitized_qa_environments()
    value_pattern = re.compile(r"^SMARTOFFERS_QA[1-4]_(API_URL|DB_DSN|DB_USER|DB_PASSWORD)$")
    raw_patterns = [
        re.compile(r"https?://", re.IGNORECASE),
        re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
        re.compile(r"bearer\s+", re.IGNORECASE),
    ]

    for environment in environments:
        values = [
            environment["api_url_ref"],
            environment["db_dsn_ref"],
            environment["db_user_ref"],
            environment["db_password_ref"],
        ]
        assert all(value_pattern.match(value) for value in values)
        assert not any(pattern.search(value) for value in values for pattern in raw_patterns)


def test_adapter_run_real_mode_still_blocked():
    with pytest.raises(AdapterRunModeError):
        run_adapter_scenario({"id": "synthetic", "execution_steps": []}, mode="real")


def test_execution_route_real_without_confirmation_returns_blocked(app_client_factory, monkeypatch):
    def fail_if_started(*args, **kwargs):
        raise AssertionError("route must not start real process without confirmation")

    monkeypatch.setattr(service.subprocess, "Popen", fail_if_started)
    client, _ = app_client_factory("execution-mode-selector")

    response = client.get(
        "/executar?tipo=variante&analisar=false"
        "&execution_mode=real_qa_manual&environment=qa4&confirm_real=false",
        buffered=True,
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "missing_real_confirmation" in body
    assert "RUN|END|BLOCKED|0|1" in body


def test_home_renders_execution_mode_and_environment_selector(app_client_factory):
    client, _ = app_client_factory("execution-mode-ui")

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="executionMode"' in html
    assert '<option value="mock" selected>mock</option>' in html
    assert '<option value="real_qa_manual">real_qa_manual</option>' in html
    assert 'id="executionEnvironment"' in html
    for environment in ("qa1", "qa2", "qa3", "qa4"):
        assert f'value="{environment}"' in html


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
