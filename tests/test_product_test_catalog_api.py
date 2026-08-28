import app as app_module
from core.api_catalog import get_api_catalog_entry
import core.product_test_catalog as product_catalog


def test_product_catalog_exposes_only_three_curated_tests(app_client_factory):
    client, _ = app_client_factory("product-catalog")
    response = client.get("/api/product-tests")
    tests = response.get_json()["tests"]

    assert response.status_code == 200
    assert [item["id"] for item in tests] == [
        "create-customer-basic", "recharge-basic", "activate-offer-basic"
    ]
    assert tests[0]["availability"] == "READY"
    assert tests[0]["execution_available"] is True
    assert [item["availability"] for item in tests[1:]] == ["CONTRACT_READY", "CONTRACT_READY"]
    assert all(item["execution_available"] is False for item in tests[1:])
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
    assert executed.get_json()["validation"] == {
        "result": "PASS",
        "strategy": "LOCAL_CUSTOMER_LINE_SIMULATION",
        "external_read_only_lookup_used": False,
    }
    assert executed.get_json()["evidence_summary"] == {
        "preflight": "PASS",
        "execution": "PASS",
        "local_verification": "PASS",
        "request_sent": False,
    }
    assert calls[0][0] == {
        "environment": "qa4",
        "workflow_profile": "smartoffers_qa4_full_smoke",
        "test_data": {
            "entity": "customer_line",
            "environment": "QA4",
            "lifecycle": "CREATE",
            "synthetic": True,
            "reference": "LOCAL_SIMULATION_CUSTOMER_LINE_V1",
        },
    }
    assert calls[0][1] == "mock"


def test_create_customer_local_execution_keeps_synthetic_data_in_memory_and_returns_only_opaque_reference(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog-synthetic-data")
    received_contexts = []

    def fake_mock(context, *, mode, evaluated_at):
        received_contexts.append(context)
        return {"result": "PASS"}

    monkeypatch.setattr(app_module, "run_standard_qa4_application_mock", fake_mock)
    response = client.post("/api/product-tests/create-customer-basic/execute")
    body = response.get_json()

    assert received_contexts[0]["test_data"] == {
        "entity": "customer_line",
        "environment": "QA4",
        "lifecycle": "CREATE",
        "synthetic": True,
        "reference": "LOCAL_SIMULATION_CUSTOMER_LINE_V1",
    }
    assert body["evidence_reference"] == "MOCK_RUN_NOT_PERSISTED"
    assert body["synthetic_data"] == {
        "prepared": True,
        "reference": "LOCAL_SIMULATION_CUSTOMER_LINE_V1",
    }
    assert body["validation"] == {
        "result": "PASS",
        "strategy": "LOCAL_CUSTOMER_LINE_SIMULATION",
        "external_read_only_lookup_used": False,
    }
    assert "test_data" not in body
    assert "msisdn" not in str(body).lower()


def test_create_customer_local_validator_rejects_an_invalid_synthetic_record():
    invalid_record = {
        "entity": "customer_line",
        "environment": "QA4",
        "lifecycle": "CREATE",
        "synthetic": False,
        "reference": "LOCAL_SIMULATION_CUSTOMER_LINE_V1",
    }

    assert app_module._validate_local_customer_line_simulation(invalid_record, "PASS") == "FAIL"


def test_create_customer_local_execution_propagates_mock_failure_to_validation_and_evidence(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog-local-fail")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: {"result": "FAIL"},
    )

    body = client.post("/api/product-tests/create-customer-basic/execute").get_json()

    assert body["result"] == "FAIL"
    assert body["validation"]["result"] == "FAIL"
    assert body["evidence_summary"] == {
        "preflight": "FAIL",
        "execution": "FAIL",
        "local_verification": "FAIL",
        "request_sent": False,
    }


def test_create_customer_catalog_truthfully_describes_real_readiness():
    from core.product_test_catalog import get_product_test

    test = get_product_test("create-customer-basic")

    assert test["local_mock_working"] is True
    assert test["real_contract_ready"] is False
    assert test["read_only_validation_ready"] is False
    assert test["real_execution_requires_owner_authorization"] is True
    assert test["missing_capabilities"] == [
        "Exact governed create binding",
        "Approved read-only customer or line lookup",
    ]
    assert test["future_read_only_validation_prerequisite"] == (
        "Approved operation/scenario-scoped customer or line read-only lookup "
        "identity, hash, destination, and result shape."
    )


def test_contract_ready_capabilities_validate_locally_but_never_execute(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )
    validated = client.post("/api/product-tests/activate-offer-basic/validate")
    response = client.post("/api/product-tests/activate-offer-basic/execute")

    assert validated.get_json()["result"] == "PASS"
    assert validated.get_json()["execution_available"] is False
    assert validated.get_json()["mode"] == "static-plan"
    assert validated.get_json()["phase"] == "VALIDATION"
    assert validated.get_json()["display_status"] == "READY_FOR_CONTRACT_REVIEW"
    assert validated.get_json()["contract_preview"] == {
        "api_mapping": "post-o-vivo-next-troca-de-oferta-fedbfb981e",
        "operation": "processEvent",
        "method": "POST",
        "environment": "QA4",
        "mode": "STATIC_MOCK_PLAN",
    }
    assert response.status_code == 200
    assert response.get_json()["result"] == "BLOCKED"
    assert response.get_json()["reason"] == "REAL_BINDING_AND_VALIDATION_NOT_READY"
    assert response.get_json()["attempts"] == "0/0"


def test_contract_ready_catalog_entries_expose_only_sanitized_existing_mappings():
    from core.product_test_catalog import get_product_test

    recharge = get_product_test("recharge-basic")
    offer = get_product_test("activate-offer-basic")

    assert recharge["operation_mapping"] == "processEvent"
    assert recharge["api_mapping"] == "post-evento-de-recarga-6954ef3458"
    assert offer["operation_mapping"] == "processEvent"
    assert offer["api_mapping"] == "post-o-vivo-next-troca-de-oferta-fedbfb981e"
    assert "host" not in str(recharge).lower()


def test_contract_ready_mappings_align_to_the_tracked_sanitized_catalog():
    from core.product_test_catalog import get_product_test

    for test_id in ("recharge-basic", "activate-offer-basic"):
        test = get_product_test(test_id)
        entry = get_api_catalog_entry(test["api_mapping"])
        assert entry["payload_base"]["operation"] == test["operation_mapping"]
        validation = product_catalog.validate_contract_plan(test)
        assert validation["valid"] is True
        assert validation["preview"]["api_mapping"] == test["api_mapping"]


def test_missing_or_invalid_contract_mapping_blocks_before_any_execution(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog-contract-invalid")
    monkeypatch.setattr(product_catalog, "_get_catalog_entry", lambda _api_id: None)
    missing = client.post("/api/product-tests/recharge-basic/validate")

    assert missing.get_json()["result"] == "BLOCKED"
    assert missing.get_json()["reason"] == "CONTRACT_MAPPING_INVALID"

    monkeypatch.setattr(
        product_catalog,
        "_get_catalog_entry",
        lambda _api_id: {"method": "POST", "supported_environments": ["QA4"], "execution_status": "blocked", "safe_for_real_execution": False, "payload_base": {"operation": "wrong"}},
    )
    invalid = client.post("/api/product-tests/activate-offer-basic/validate")
    assert invalid.get_json()["result"] == "BLOCKED"
    assert invalid.get_json()["reason"] == "CONTRACT_MAPPING_INVALID"


def test_both_contract_ready_execute_routes_block_before_mock_facade(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog-no-contract-execute")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    for test_id in ("recharge-basic", "activate-offer-basic"):
        response = client.post(f"/api/product-tests/{test_id}/execute")
        assert response.get_json()["result"] == "BLOCKED"
        assert response.get_json()["reason"] == "REAL_BINDING_AND_VALIDATION_NOT_READY"


def test_primary_ui_hides_legacy_controls_and_resets_validation_on_selection(app_client_factory):
    client, _ = app_client_factory("product-catalog-ui")
    html = client.get("/").get_data(as_text=True)

    assert 'class="app product-active" id="appShell"' in html
    assert "legacy-sidebar-control" in html
    assert 'onchange="resetProductValidation()"' in html
    assert 'id="productExecute"' in html and "disabled>Execute test" in html
    assert 'id="productViewEvidence"' in html
    assert 'id="productTechnicalDetails"' in html
    assert "Local mock run: no persisted evidence artifact." in html
    assert "Contract ready" in html
    assert "data.execution_available !== true" in html
    assert 'isContractValidation ? "Validation" : "Status"' in html
    assert "Customer/line local simulation" in html
    assert "Real QA4 execution requires Owner authorization." in html
    assert "Local simulation &mdash; no QA4 request" in html
    assert "Customer/line local simulation passed" in html
    assert 'data.validation.strategy === "LOCAL_CUSTOMER_LINE_SIMULATION"' in html
    assert 'data.validation.result === "PASS"' in html
    assert '"Ready for contract review"' in html
    assert '"Existing QA4 contract checked. No request was sent."' in html
    assert "Contract preview" not in html


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
