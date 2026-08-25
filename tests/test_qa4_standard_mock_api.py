import app as app_module


EVALUATED_AT = "2026-08-22T12:10:00+00:00"


def _payload(**overrides):
    payload = {
        "environment": "QA4",
        "mode": "mock",
        "workflow_profile": "smartoffers_qa4_full_smoke",
        "orchestration_id": "alpha-run-ref",
        "operational_window_ref": "qa4-window-ref",
        "window_started_at": "2026-08-22T12:00:00+00:00",
        "window_expires_at": "2026-08-22T12:15:00+00:00",
        "evaluated_at": EVALUATED_AT,
    }
    payload.update(overrides)
    return payload


def test_standard_mock_api_runs_only_allowlisted_context_once(app_client_factory, monkeypatch):
    client, _ = app_client_factory("qa4-standard-api")
    calls = []
    expected_report = {"result": "PASS", "full": {"status": "FULL_SMOKE_OK"}}

    def fake_facade(context, *, mode, evaluated_at):
        calls.append((context, mode, evaluated_at))
        return expected_report

    monkeypatch.setattr(app_module, "run_standard_qa4_application_mock", fake_facade)

    response = client.post(
        "/api/qa4/standard/mock-run",
        json=_payload(secret="must-not-appear", unknown="discard-me"),
    )

    assert response.status_code == 200
    assert response.get_json() == {"result": "PASS", "report": expected_report}
    assert calls == [
        (
            {
                "environment": "qa4",
                "workflow_profile": "smartoffers_qa4_full_smoke",
                "orchestration_id": "alpha-run-ref",
                "operational_window_ref": "qa4-window-ref",
                "window_started_at": "2026-08-22T12:00:00+00:00",
                "window_expires_at": "2026-08-22T12:15:00+00:00",
            },
            "mock",
            EVALUATED_AT,
        )
    ]
    assert "must-not-appear" not in response.get_data(as_text=True)


def test_standard_mock_api_blocks_real_mode_without_invoking_facade(app_client_factory, monkeypatch):
    client, _ = app_client_factory("qa4-standard-api")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    response = client.post("/api/qa4/standard/mock-run", json=_payload(mode="real"))

    assert response.status_code == 400
    assert response.get_json() == {"result": "BLOCKED", "reason": "MODE_NOT_ALLOWED"}


def test_standard_mock_api_blocks_non_standard_profile_and_environment(app_client_factory, monkeypatch):
    client, _ = app_client_factory("qa4-standard-api")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    for payload, reason in (
        (_payload(workflow_profile="smartoffers_variant_smoke"), "WORKFLOW_PROFILE_NOT_ALLOWED"),
        (_payload(workflow_profile="smartoffers_copy_smoke"), "WORKFLOW_PROFILE_NOT_ALLOWED"),
        (_payload(environment="DEV"), "ENVIRONMENT_NOT_ALLOWED"),
    ):
        response = client.post("/api/qa4/standard/mock-run", json=payload)
        assert response.status_code == 400
        assert response.get_json() == {"result": "BLOCKED", "reason": reason}


def test_standard_mock_api_blocks_malformed_or_incomplete_request_without_echoing_it(app_client_factory, monkeypatch):
    client, _ = app_client_factory("qa4-standard-api")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    cases = (
        (None, "MALFORMED_REQUEST"),
        ({}, "MISSING_ORCHESTRATION_CONTEXT"),
        (_payload(window_expires_at="not-a-timestamp", secret="must-not-appear"), "INVALID_OPERATIONAL_WINDOW"),
        (_payload(evaluated_at="not-a-timestamp"), "INVALID_EVALUATED_AT"),
    )
    for payload, reason in cases:
        response = client.post("/api/qa4/standard/mock-run", json=payload)
        assert response.status_code == 400
        assert response.get_json() == {"result": "BLOCKED", "reason": reason}
        assert "must-not-appear" not in response.get_data(as_text=True)

    malformed_response = client.post(
        "/api/qa4/standard/mock-run",
        data="{",
        content_type="application/json",
    )
    assert malformed_response.status_code == 400
    assert malformed_response.get_json() == {
        "result": "BLOCKED",
        "reason": "MALFORMED_REQUEST",
    }
