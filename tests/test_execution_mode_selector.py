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
from core.legacy_execution.runtime_config import (
    ORACLE_CLIENT_LIB_DIR_ENV,
    preflight_legacy_runtime_config,
    resolve_legacy_runtime_config,
)
from core.real_execution.environments import (
    list_sanitized_qa_environments,
)
from core.real_execution.runtime_profiles import (
    SMARTOFFERS_BASIC_SMOKE,
    get_sanitized_runtime_profile,
    list_sanitized_runtime_profiles,
)


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


def test_real_qa4_defaults_to_official_runtime_profile():
    decision = evaluate_execution_mode_request(
        mode=EXECUTION_MODE_REAL_QA_MANUAL,
        environment="qa4",
        real_confirmed=True,
    )

    assert decision["allowed"] is True
    assert decision["runtime_profile"] == SMARTOFFERS_BASIC_SMOKE
    assert decision["runtime_contract"]["id"] == SMARTOFFERS_BASIC_SMOKE


def test_runtime_profile_must_match_selected_environment():
    decision = evaluate_execution_mode_request(
        mode=EXECUTION_MODE_REAL_QA_MANUAL,
        environment="qa2",
        runtime_profile=SMARTOFFERS_BASIC_SMOKE,
        real_confirmed=True,
    )

    assert decision["allowed"] is False
    assert "runtime_profile_environment_mismatch" in decision["blocked_reasons"]


def test_invalid_runtime_profile_is_blocked_without_defaulting():
    decision = evaluate_execution_mode_request(
        mode=EXECUTION_MODE_REAL_QA_MANUAL,
        environment="qa4",
        runtime_profile="missing-profile",
        real_confirmed=True,
    )

    assert decision["allowed"] is False
    assert decision["runtime_profile"] == "missing-profile"
    assert decision["runtime_profile_contract"] is None
    assert "invalid_runtime_profile" in decision["blocked_reasons"]


def test_runtime_preflight_qa4_complete_fake_env_returns_ready(monkeypatch):
    _set_fake_qa4_profile_runtime(monkeypatch)

    preflight = preflight_legacy_runtime_config(
        get_sanitized_runtime_profile(SMARTOFFERS_BASIC_SMOKE)
    )

    assert preflight == {
        "status": "READY",
        "environment": "qa4",
        "profile": SMARTOFFERS_BASIC_SMOKE,
        "flow": "smartoffers_basic_smoke",
        "resources": ["smartoffers_api", "acm_custom_db", "oracle_client"],
        "legacy_alias_refs_used": [],
        "missing_refs": [],
        "checked_refs": [
            "SMARTOFFERS_QA4_API_URL",
            "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
            "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
            "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
            "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
        ],
    }


def test_runtime_preflight_qa4_missing_env_returns_blocked(monkeypatch):
    for name in (
        "SMARTOFFERS_QA4_API_URL",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
        "SMARTOFFERS_QA4_DB_DSN",
        "SMARTOFFERS_QA4_DB_USER",
        "SMARTOFFERS_QA4_DB_PASSWORD",
        ORACLE_CLIENT_LIB_DIR_ENV,
    ):
        monkeypatch.delenv(name, raising=False)

    preflight = preflight_legacy_runtime_config(
        get_sanitized_runtime_profile(SMARTOFFERS_BASIC_SMOKE)
    )

    assert preflight["status"] == "BLOCKED"
    assert preflight["environment"] == "qa4"
    assert preflight["profile"] == SMARTOFFERS_BASIC_SMOKE
    assert preflight["missing_refs"] == [
        "SMARTOFFERS_QA4_API_URL",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    ]
    assert ORACLE_CLIENT_LIB_DIR_ENV in preflight["checked_refs"]


def test_runtime_preflight_accepts_qa4_db_legacy_aliases_when_explicit_refs_absent(monkeypatch):
    monkeypatch.setenv("SMARTOFFERS_QA4_API_URL", "fake-qa4-api-url")
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_DSN", "fake-legacy-qa4-db-dsn")
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_USER", "fake-legacy-qa4-db-user")
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_PASSWORD", "fake-legacy-qa4-db-password")
    monkeypatch.setenv(ORACLE_CLIENT_LIB_DIR_ENV, "fake-oracle-client-dir")
    for name in (
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    runtime_config = resolve_legacy_runtime_config(
        get_sanitized_runtime_profile(SMARTOFFERS_BASIC_SMOKE)
    )

    assert runtime_config["preflight"]["status"] == "READY"
    assert runtime_config["preflight"]["legacy_alias_refs_used"] == [
        "SMARTOFFERS_QA4_DB_DSN",
        "SMARTOFFERS_QA4_DB_USER",
        "SMARTOFFERS_QA4_DB_PASSWORD",
    ]
    assert runtime_config["normalized_env"]["SMARTOFFERS_DB_DSN"] == "fake-legacy-qa4-db-dsn"
    rendered = repr(runtime_config["preflight"])
    assert "fake-legacy-qa4-db-dsn" not in rendered
    assert "fake-legacy-qa4-db-user" not in rendered
    assert "fake-legacy-qa4-db-password" not in rendered


def test_runtime_preflight_prefers_explicit_acm_custom_refs_over_legacy_aliases(monkeypatch):
    _set_fake_qa4_profile_runtime(monkeypatch)
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_DSN", "fake-legacy-qa4-db-dsn")
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_USER", "fake-legacy-qa4-db-user")
    monkeypatch.setenv("SMARTOFFERS_QA4_DB_PASSWORD", "fake-legacy-qa4-db-password")

    runtime_config = resolve_legacy_runtime_config(
        get_sanitized_runtime_profile(SMARTOFFERS_BASIC_SMOKE)
    )

    assert runtime_config["preflight"]["status"] == "READY"
    assert runtime_config["preflight"]["legacy_alias_refs_used"] == []
    assert runtime_config["normalized_env"]["SMARTOFFERS_DB_DSN"] == "fake-qa4-acm-custom-db-dsn"


def test_runtime_preflight_returns_refs_never_values(monkeypatch):
    _set_fake_qa4_profile_runtime(monkeypatch)

    preflight = preflight_legacy_runtime_config(
        get_sanitized_runtime_profile(SMARTOFFERS_BASIC_SMOKE)
    )
    rendered = repr(preflight)

    assert "SMARTOFFERS_QA4_API_URL" in rendered
    assert "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD" in rendered
    assert "fake-qa4-api-url" not in rendered
    assert "fake-qa4-acm-custom-db-dsn" not in rendered
    assert "fake-qa4-acm-custom-db-user" not in rendered
    assert "fake-qa4-acm-custom-db-password" not in rendered
    assert "fake-oracle-client-dir" not in rendered


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


def test_real_with_confirmation_injects_legacy_guard_with_fake_process(monkeypatch):
    _set_fake_qa4_profile_runtime(monkeypatch)
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
    assert captured["env"]["SMARTOFFERS_RUNTIME_PROFILE"] == SMARTOFFERS_BASIC_SMOKE
    assert captured["env"]["SMARTOFFERS_API_URL"] == "fake-qa4-api-url"
    assert captured["env"]["SMARTOFFERS_DB_DSN"] == "fake-qa4-acm-custom-db-dsn"
    assert captured["env"]["SMARTOFFERS_DB_USER"] == "fake-qa4-acm-custom-db-user"
    assert captured["env"]["SMARTOFFERS_DB_PASSWORD"] == "fake-qa4-acm-custom-db-password"
    assert _last_run_end(events) == "RUN|END|PASS|0|0"


def test_real_qa_without_local_config_is_blocked(monkeypatch):
    for name in (
        "SMARTOFFERS_QA4_API_URL",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
        ORACLE_CLIENT_LIB_DIR_ENV,
    ):
        monkeypatch.delenv(name, raising=False)

    def fail_if_started(*args, **kwargs):
        raise AssertionError("process must not start without complete runtime config")

    events = _collect_events(
        service.stream_legacy_execution(
            "copy",
            analisar=False,
            execution_mode=EXECUTION_MODE_REAL_QA_MANUAL,
            environment="qa4",
            real_confirmed=True,
            process_factory=fail_if_started,
        )
    )

    assert any("Runtime preflight blocked" in event for event in events)
    assert any("missing_runtime_ref:SMARTOFFERS_QA4_API_URL" in event for event in events)
    assert any("missing_runtime_ref:SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN" in event for event in events)
    assert _last_run_end(events) == "RUN|END|BLOCKED|0|1"


def test_runtime_config_log_uses_refs_not_values(monkeypatch):
    _set_fake_qa_runtime(monkeypatch, "qa2")
    process_factory, captured = _fake_process_factory([], returncode=0)

    events = _collect_events(
        service.stream_legacy_execution(
            "variante",
            analisar=False,
            execution_mode=EXECUTION_MODE_REAL_QA_MANUAL,
            environment="qa2",
            real_confirmed=True,
            process_factory=process_factory,
        )
    )

    runtime_logs = [event for event in events if "RUNTIME_CONFIG|" in event]
    assert runtime_logs
    assert "SMARTOFFERS_QA2_API_URL" in runtime_logs[0]
    assert "SMARTOFFERS_QA2_DB_DSN" in runtime_logs[0]
    assert "fake-qa2-api-url" not in runtime_logs[0]
    assert "fake-qa2-db-password" not in runtime_logs[0]
    assert captured["env"]["SMARTOFFERS_API_URL"] == "fake-qa2-api-url"


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


def test_build_env_does_not_inject_guard_without_resolved_runtime_config():
    env = service.build_legacy_execution_env(
        analisar=False,
        allow_legacy_real_script=True,
        execution_mode=EXECUTION_MODE_REAL_QA_MANUAL,
        environment="qa4",
        base_env={},
    )

    assert service.LEGACY_REAL_SCRIPT_ENV not in env
    assert "SMARTOFFERS_API_URL" not in env


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


def test_mock_mode_does_not_require_runtime_config(monkeypatch):
    for name in (
        "SMARTOFFERS_QA1_API_URL",
        "SMARTOFFERS_QA1_DB_DSN",
        "SMARTOFFERS_QA1_DB_USER",
        "SMARTOFFERS_QA1_DB_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)
    process_factory, captured = _fake_process_factory([], returncode=0)

    events = _collect_events(
        service.stream_legacy_execution(
            "padrao",
            analisar=False,
            execution_mode="mock",
            environment="qa1",
            process_factory=process_factory,
        )
    )

    assert service.LEGACY_REAL_SCRIPT_ENV not in captured["env"]
    assert "SMARTOFFERS_API_URL" not in captured["env"]
    assert _last_run_end(events) == "RUN|END|PASS|0|0"


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


def test_official_runtime_profile_versions_only_multi_resource_refs():
    profiles = list_sanitized_runtime_profiles("qa4")
    profile = get_sanitized_runtime_profile(SMARTOFFERS_BASIC_SMOKE)

    assert [entry["id"] for entry in profiles] == [SMARTOFFERS_BASIC_SMOKE]
    assert profile["environment"] == "qa4"
    assert profile["access_profile"] == "acm_custom_read_only"
    assert [resource["id"] for resource in profile["resources"]] == [
        "smartoffers_api",
        "acm_custom_db",
        "oracle_client",
    ]
    assert profile["resources"][1]["schema"] == "ACM_CUSTOM"
    assert profile["resources"][1]["access"] == "read_only"

    rendered = repr(profile)
    for ref in (
        "SMARTOFFERS_QA4_API_URL",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    ):
        assert ref in rendered

    assert profile["resources"][1]["legacy_refs"] == {
        "dsn": ["SMARTOFFERS_QA4_DB_DSN"],
        "user": ["SMARTOFFERS_QA4_DB_USER"],
        "password": ["SMARTOFFERS_QA4_DB_PASSWORD"],
    }
    assert "SMARTOFFERS_QA4_FTM_ENGINE_URL" not in rendered
    assert "SMARTOFFERS_QA4_ACMV4_DB_" not in rendered
    assert "SMARTOFFERS_QA4_BDA_DB_" not in rendered
    assert "://" not in rendered
    assert not re.search(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", rendered)


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
    assert 'id="runtimeProfile"' in html
    assert f'value="{SMARTOFFERS_BASIC_SMOKE}"' in html
    for environment in ("qa1", "qa2", "qa3", "qa4"):
        assert f'value="{environment}"' in html


def _fake_process_factory(lines, returncode=0):
    captured = {}

    def factory(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return _FakeProcess(lines, returncode)

    return factory, captured


def _set_fake_qa_runtime(monkeypatch, environment):
    prefix = environment.upper()
    monkeypatch.setenv(f"SMARTOFFERS_{prefix}_API_URL", f"fake-{environment}-api-url")
    monkeypatch.setenv(f"SMARTOFFERS_{prefix}_DB_DSN", f"fake-{environment}-db-dsn")
    monkeypatch.setenv(f"SMARTOFFERS_{prefix}_DB_USER", f"fake-{environment}-db-user")
    monkeypatch.setenv(f"SMARTOFFERS_{prefix}_DB_PASSWORD", f"fake-{environment}-db-password")
    monkeypatch.setenv(ORACLE_CLIENT_LIB_DIR_ENV, "fake-oracle-client-dir")


def _set_fake_qa4_profile_runtime(monkeypatch):
    monkeypatch.setenv("SMARTOFFERS_QA4_API_URL", "fake-qa4-api-url")
    monkeypatch.setenv("SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN", "fake-qa4-acm-custom-db-dsn")
    monkeypatch.setenv("SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER", "fake-qa4-acm-custom-db-user")
    monkeypatch.setenv(
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
        "fake-qa4-acm-custom-db-password",
    )
    monkeypatch.setenv(ORACLE_CLIENT_LIB_DIR_ENV, "fake-oracle-client-dir")


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
