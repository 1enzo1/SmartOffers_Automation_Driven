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
    assert "View evidence" not in html
