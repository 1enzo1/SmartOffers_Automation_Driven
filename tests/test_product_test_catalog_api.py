import app as app_module


def test_product_catalog_exposes_only_three_curated_tests(app_client_factory):
    client, _ = app_client_factory("product-catalog")
    response = client.get("/api/product-tests")
    tests = response.get_json()["tests"]

    assert response.status_code == 200
    assert [item["id"] for item in tests] == [
        "create-customer-basic", "recharge-basic", "activate-offer-basic"
    ]
    assert tests[0]["availability"] == "READY"
    assert all(item["environments"] == ["QA4"] for item in tests)


def test_product_catalog_validate_and_execute_are_mock_only(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog")
    calls = []

    def fake_mock(context, *, mode, evaluated_at):
        calls.append((context, mode, evaluated_at))
        return {"result": "PASS"}

    monkeypatch.setattr(app_module, "run_standard_qa4_application_mock", fake_mock)
    validated = client.post("/api/product-tests/create-customer-basic/validate")
    executed = client.post("/api/product-tests/create-customer-basic/execute")

    assert validated.get_json()["result"] == "PASS"
    assert executed.get_json()["result"] == "PASS"
    assert executed.get_json()["attempts"] == "0/0"
    assert calls[0][0] == {"environment": "qa4", "workflow_profile": "smartoffers_qa4_full_smoke"}
    assert calls[0][1] == "mock"


def test_unready_product_capabilities_are_blocked_without_mock_execution(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )
    response = client.post("/api/product-tests/activate-offer-basic/execute")

    assert response.status_code == 200
    assert response.get_json()["result"] == "BLOCKED"
    assert response.get_json()["reason"] == "CAPABILITY_NOT_READY"


def test_primary_ui_hides_legacy_controls_and_resets_validation_on_selection(app_client_factory):
    client, _ = app_client_factory("product-catalog-ui")
    html = client.get("/").get_data(as_text=True)

    assert 'class="app product-active" id="appShell"' in html
    assert "legacy-sidebar-control" in html
    assert 'onchange="resetProductValidation()"' in html
    assert 'id="productExecute"' in html and "disabled>Execute test" in html
    assert 'id="productViewEvidence"' in html
    assert "Local mock run: no persisted evidence artifact." in html


def test_evidence_endpoint_is_read_only_allowlisted_and_sanitized(app_client_factory):
    client, _ = app_client_factory("product-evidence")

    response = client.get("/api/evidence/ALPHA_REAL_RUN_02")
    traversal = client.get("/api/evidence/..%2FALPHA_REAL_RUN_02")

    assert response.status_code == 200
    assert response.get_json()["result"] == "FAIL"
    evidence = response.get_json()["evidence"]
    assert evidence["run_id"] == "ALPHA_REAL_RUN_02"
    assert evidence["result"] == "FAIL"
    assert evidence["consistency_reason"] == "RESPONSE_NOT_CONFIRMED"
    assert "endpoint" not in evidence
    assert "password" not in evidence
    assert traversal.status_code == 404


def test_evidence_list_is_separate_from_mock_flow_and_only_lists_known_records(app_client_factory):
    client, _ = app_client_factory("product-evidence-list")
    response = client.get("/api/evidence")
    html = client.get("/").get_data(as_text=True)

    assert response.status_code == 200
    assert all(item["run_id"] in {"ALPHA_REAL_RUN_01", "ALPHA_REAL_RUN_02"} for item in response.get_json()["evidence"])
    assert "Recent controlled evidence" in html
    assert "Separate from local mock results" in html
