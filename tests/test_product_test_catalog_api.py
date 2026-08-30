import app as app_module
from core.real_execution.operational_release_store import OperationalReleaseStore


def _provision_trusted_product_release(monkeypatch):
    """Provide test-only server-side release material; the browser never sees it."""
    monkeypatch.setattr(app_module, "_PRODUCT_OPERATIONAL_RELEASES", OperationalReleaseStore())
    now = app_module._trusted_local_now()
    expires_at = now + app_module._PRODUCT_VALIDATION_CONTEXT_TTL
    release = {
        "release_key": "test-product-release",
        "request_plan": {
            "environment": "QA4",
            "workflow_profile": app_module._STANDARD_QA4_PROFILE,
            "mode": "real-controlled",
            "run_id": "ALPHA_REAL_RUN_03A",
            "owner_authorization": "ONE_QA4_CREATE_CUSTOMER_WITH_OFFER_RUN_03A",
            "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
            "application_confirmation": app_module._APPLICATION_CONFIRMATION,
            "orchestration_id": "test-product-release",
            "operational_window_ref": "test-product-window",
            "window_started_at": now.isoformat(),
            "window_expires_at": expires_at.isoformat(),
            "evaluated_at": now.isoformat(),
        },
    }
    assert app_module._provision_product_operational_release(
        "create-customer-basic", release, expires_at
    ) is True
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
    assert [item["name"] for item in tests] == [
        "Create Customer with Offer", "Recharge Basic", "Add Offer Basic"
    ]
    assert tests[0]["availability"] == "READY"
    assert tests[0]["execution_available"] is True
    assert tests[0]["real_operation"] == "CREATE_OFFERS_CUSTOMER"
    assert "scenario_id" not in tests[0]
    assert "real_run_id" not in tests[0]
    assert "real_authorization" not in tests[0]
    assert tests[0]["real_execution_status"] == "REAL EXECUTION CONTRACT READY - AUTHORIZATION REQUIRED"
    assert tests[0]["product_status"] == "QA READY"
    assert tests[0]["post_execution_validation"] == "NOT AVAILABLE"
    assert tests[1]["availability"] == "READY"
    assert tests[1]["execution_available"] is True
    assert tests[1]["execution_mode_notice"] == "LOCAL DIAGNOSTIC only; QA4 execution is not available for this operation."
    assert tests[1]["product_status"] == "LOCAL DIAGNOSTIC"
    assert "â" not in str(tests)
    assert tests[2]["availability"] == "BLOCKED_EXTERNAL_INFORMATION"
    assert tests[2]["execution_available"] is False
    assert tests[2]["product_status"] == "UNAVAILABLE"
    assert all(item["environments"] == ["QA4"] for item in tests)


def test_create_customer_product_execute_requires_explicit_qa_intent_and_never_falls_back_to_mock(
    app_client_factory, monkeypatch
):
    client, _ = app_client_factory("product-catalog")
    calls = []

    def fake_mock(context, *, mode, evaluated_at):
        calls.append((context, mode, evaluated_at))
        return {"result": "PASS"}

    monkeypatch.setattr(app_module, "run_standard_qa4_application_mock", fake_mock)
    validated = client.post("/api/product-tests/create-customer-basic/validate")
    executed = client.post("/api/product-tests/create-customer-basic/execute")

    assert validated.get_json()["result"] == "PASS"
    assert executed.get_json() == {"result": "BLOCKED", "reason": "QA_EXECUTION_INTENT_REQUIRED"}
    assert calls == []


def test_create_customer_product_execute_does_not_expose_local_simulation_data(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog-synthetic-data")
    received_contexts = []

    def fake_mock(context, *, mode, evaluated_at):
        received_contexts.append(context)
        return {"result": "PASS"}

    monkeypatch.setattr(app_module, "run_standard_qa4_application_mock", fake_mock)
    response = client.post("/api/product-tests/create-customer-basic/execute")
    body = response.get_json()

    assert body == {"result": "BLOCKED", "reason": "QA_EXECUTION_INTENT_REQUIRED"}
    assert received_contexts == []


def test_create_customer_local_validator_rejects_an_invalid_synthetic_record():
    invalid_record = {
        "entity": "customer_line",
        "environment": "QA4",
        "lifecycle": "CREATE",
        "synthetic": False,
        "reference": "LOCAL_SIMULATION_CUSTOMER_LINE_V1",
    }

    assert app_module._validate_local_customer_line_simulation(invalid_record, "PASS") == "FAIL"


def test_create_customer_product_execute_blocks_before_local_mock_failure_can_run(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog-local-fail")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: {"result": "FAIL"},
    )

    body = client.post("/api/product-tests/create-customer-basic/execute").get_json()

    assert body == {"result": "BLOCKED", "reason": "QA_EXECUTION_INTENT_REQUIRED"}


def test_create_customer_catalog_truthfully_describes_real_readiness():
    from core.product_test_catalog import get_product_test

    test = get_product_test("create-customer-basic")

    assert test["local_mock_working"] is True
    assert test["real_contract_ready"] is True
    assert test["read_only_validation_ready"] is False
    assert test["real_execution_requires_owner_authorization"] is True
    assert test["missing_capabilities"] == ["Approved read-only customer or line lookup"]
    assert test["future_read_only_validation_prerequisite"] == (
        "Approved operation/scenario-scoped customer or line read-only lookup "
        "identity, hash, destination, and result shape."
    )


def test_recharge_executes_only_a_local_fake_request_plan_and_returns_sanitized_evidence(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("recharge must use FakeSmartOffersAdapter plan")),
    )

    validated = client.post("/api/product-tests/recharge-basic/validate").get_json()
    executed = client.post("/api/product-tests/recharge-basic/execute").get_json()

    assert validated["result"] == "PASS"
    assert validated["display_status"] == "READY_FOR_LOCAL_MOCK"
    assert validated["mode"] == "mock"
    assert executed["result"] == "PASS"
    assert "attempts" not in executed
    assert executed["reason"] == "LOCAL_RECHARGE_SIMULATION_COMPLETED"
    assert executed["validation"] == {
        "result": "PASS",
        "strategy": "LOCAL_RECHARGE_REQUEST_PLAN_SIMULATION",
        "external_read_only_lookup_used": False,
    }
    assert executed["evidence_summary"] == {
        "preflight": "PASS",
        "execution": "PASS",
        "local_verification": "PASS",
        "request_sent": False,
    }
    assert executed["synthetic_data"] == {
        "prepared": True,
        "reference": "LOCAL_SIMULATION_RECHARGE_V1",
    }
    assert "payload" not in executed
    assert "http" not in str(executed).lower()


def test_add_offer_blocks_without_offer_discovery_or_transport(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog-add-offer")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    validated = client.post("/api/product-tests/activate-offer-basic/validate")
    executed = client.post("/api/product-tests/activate-offer-basic/execute")

    assert validated.get_json()["result"] == "BLOCKED"
    assert validated.get_json()["reason"] == "ADD_OFFER_EXTERNAL_INFORMATION_REQUIRED"
    assert executed.get_json()["result"] == "BLOCKED"
    assert executed.get_json()["reason"] == "ADD_OFFER_EXTERNAL_INFORMATION_REQUIRED"
    assert "attempts" not in executed.get_json()


def test_catalog_entries_expose_only_sanitized_existing_mappings():
    from core.product_test_catalog import get_product_test

    recharge = get_product_test("recharge-basic")
    offer = get_product_test("activate-offer-basic")

    assert recharge["operation_mapping"] == "processEvent"
    assert recharge["api_mapping"] == "post-evento-de-recarga-6954ef3458"
    assert offer["availability"] == "BLOCKED_EXTERNAL_INFORMATION"
    assert offer["missing_capabilities"] == [
        "Operation-scoped add-offer contract",
        "Governed offer input or discovery",
        "Approved read-only validation",
    ]
    assert offer["api_mapping"] == "post-o-vivo-next-troca-de-oferta-fedbfb981e"
    assert "host" not in str(recharge).lower()


def test_recharge_mapping_aligns_to_the_tracked_sanitized_catalog():
    from core.product_test_catalog import get_product_test

    for test_id in ("recharge-basic",):
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
    valid = client.post("/api/product-tests/recharge-basic/validate")
    assert valid.get_json()["result"] == "BLOCKED"
    assert valid.get_json()["reason"] == "CONTRACT_MAPPING_INVALID"


def test_add_offer_execute_route_blocks_before_mock_facade(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-catalog-no-contract-execute")
    monkeypatch.setattr(
        app_module,
        "run_standard_qa4_application_mock",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    response = client.post("/api/product-tests/activate-offer-basic/execute")
    assert response.get_json()["result"] == "BLOCKED"
    assert response.get_json()["reason"] == "ADD_OFFER_EXTERNAL_INFORMATION_REQUIRED"


def test_create_customer_qa_execution_uses_a_validation_context_and_delegates_to_existing_controlled_stack(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-run03a-delegation")
    _provision_trusted_product_release(monkeypatch)
    calls = []
    monkeypatch.setattr(
        app_module,
        "_run_standard_qa4_real_controlled_request",
        lambda data: calls.append(data) or ({"result": "BLOCKED", "run_id": "ALPHA_REAL_RUN_03A"}, 200),
    )
    validation = client.post("/api/product-tests/create-customer-basic/validate").get_json()
    response = client.post(
        "/api/product-tests/create-customer-basic/execute",
        json={
            "intent": "EXECUTE_IN_QA",
            "validation_context_ref": validation["validation_context_ref"],
        },
    )
    assert response.get_json()["run_id"] == "ALPHA_REAL_RUN_03A"
    assert calls[0]["mode"] == "real-controlled"
    assert calls[0]["run_id"] == "ALPHA_REAL_RUN_03A"
    assert calls[0]["scenario_id"] == "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4"
    assert calls[0]["owner_authorization"] == "ONE_QA4_CREATE_CUSTOMER_WITH_OFFER_RUN_03A"
    assert "validation_context_ref" not in calls[0]


def test_create_customer_qa_execution_denies_missing_or_reused_validation_context_before_delegate(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-run03a-denied")
    monkeypatch.setattr(app_module, "_run_standard_qa4_real_controlled_request", lambda: (_ for _ in ()).throw(AssertionError("must not delegate")))
    response = client.post(
        "/api/product-tests/create-customer-basic/execute",
        json={"intent": "EXECUTE_IN_QA"},
    )
    assert response.get_json() == {"result": "BLOCKED", "reason": "VALIDATION_CONTEXT_REQUIRED"}


def test_create_customer_product_context_delegates_directly_to_the_existing_atomic_controlled_stack(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-atomic-stack")
    _provision_trusted_product_release(monkeypatch)
    atomic_calls = []
    monkeypatch.setattr(app_module, "_qa4_controlled_contract_from_environ", lambda: {"contract": "trusted"})
    monkeypatch.setattr(app_module, "_atomic_static_preflight_ready", lambda *_args: True)
    monkeypatch.setattr(app_module, "_governed_bda_driver", lambda: object())
    monkeypatch.setattr(
        app_module,
        "run_atomic_qa4_bda_offer_discovery_and_offers_create",
        lambda *args, **kwargs: atomic_calls.append((args, kwargs))
        or {"result": "BLOCKED", "executor_send_attempted": False, "real_call_executed": False},
    )
    validation = client.post("/api/product-tests/create-customer-basic/validate").get_json()

    response = client.post(
        "/api/product-tests/create-customer-basic/execute",
        json={"intent": "EXECUTE_IN_QA", "validation_context_ref": validation["validation_context_ref"]},
    )
    replay = client.post(
        "/api/product-tests/create-customer-basic/execute",
        json={"intent": "EXECUTE_IN_QA", "validation_context_ref": validation["validation_context_ref"]},
    )

    assert response.status_code == 200
    assert response.get_json()["result"] == "BLOCKED"
    assert len(atomic_calls) == 1
    assert atomic_calls[0][0][0]["run_id"] == "ALPHA_REAL_RUN_03A"
    assert atomic_calls[0][0][0]["scenario_id"] == "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4"
    assert replay.get_json() == {"result": "BLOCKED", "reason": "VALIDATION_CONTEXT_INVALID"}


def test_create_customer_validation_reports_qa_execution_and_db_validation_separately(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-qa-readiness")
    _provision_trusted_product_release(monkeypatch)

    response = client.post("/api/product-tests/create-customer-basic/validate")

    payload = response.get_json()
    assert payload["result"] == "PASS"
    assert payload["execution_ready"] is True
    assert payload["post_execution_db_validation_ready"] is False
    assert payload["authorization_state"] == "REQUIRES_AUTHORIZATION"


def test_create_customer_validation_requires_a_trusted_operational_release_before_issuing_context(
    app_client_factory, monkeypatch
):
    client, _ = app_client_factory("product-release-required")
    store = OperationalReleaseStore()
    monkeypatch.setattr(app_module, "_PRODUCT_OPERATIONAL_RELEASES", store)

    response = client.post("/api/product-tests/create-customer-basic/validate")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["result"] == "PASS"
    assert payload["authorization_state"] == "REQUIRES_AUTHORIZATION"
    assert payload["execution_ready"] is False
    assert payload["validation_context_ref"] is None
    assert payload["display_status"] == "AUTHORIZATION_REQUIRED"
    assert store.reserve(
        test_id="create-customer-basic",
        now=app_module._trusted_local_now(),
        ttl=app_module._PRODUCT_VALIDATION_CONTEXT_TTL,
    ) == (None, None)


def test_product_release_provisioning_rejects_wrong_scope_and_browser_auth_injection(app_client_factory, monkeypatch):
    client, _ = app_client_factory("product-release-scope")
    monkeypatch.setattr(app_module, "_PRODUCT_OPERATIONAL_RELEASES", OperationalReleaseStore())
    now = app_module._trusted_local_now()
    assert app_module._provision_product_operational_release(
        "create-customer-basic",
        {
            "release_key": "wrong-scope",
            "request_plan": {
                "environment": "QA4",
                "workflow_profile": app_module._STANDARD_QA4_PROFILE,
                "mode": "real-controlled",
                "run_id": "wrong-run",
                "owner_authorization": "browser-provided",
                "scenario_id": "wrong-scenario",
                "application_confirmation": app_module._APPLICATION_CONFIRMATION,
            },
        },
        now + app_module._PRODUCT_VALIDATION_CONTEXT_TTL,
    ) is False

    injected = client.post(
        "/api/product-tests/create-customer-basic/execute",
        json={
            "intent": "EXECUTE_IN_QA",
            "validation_context_ref": "unknown",
            "owner_authorization": "browser-provided",
        },
    )
    assert injected.get_json() == {"result": "BLOCKED", "reason": "PRODUCT_EXECUTION_INPUT_NOT_ALLOWED"}


def test_primary_ui_hides_legacy_controls_and_resets_validation_on_selection(app_client_factory):
    client, _ = app_client_factory("product-catalog-ui")
    html = client.get("/").get_data(as_text=True)

    assert 'class="app product-active" id="appShell"' in html
    assert "legacy-sidebar-control" in html
    assert 'onchange="resetProductValidation()"' in html
    assert 'id="productExecute"' in html and "disabled>Run QA4 test" in html
    assert 'id="productViewEvidence"' in html
    assert 'id="productTechnicalDetails"' in html
    assert "Current run: no persisted evidence artifact." in html
    assert "Loading evidence availability..." in html
    assert 'list.textContent = "Loading evidence availability..."' in html
    assert "productHumanStatus(test)" in html
    assert '<details id="diagnosticsNav">' in html
    assert '<details id="diagnosticsSidebar">' in html
    assert 'diagnostics.open = name === "generator" || name === "runner"' in html
    assert "LOCAL APP" not in html
    assert "DRY-RUN LOCAL" not in html
    assert "Run QA4 test" in html
    assert 'intent: "EXECUTE_IN_QA"' in html
    assert "validation_context_ref: productValidationContextRef" in html
    assert "owner_authorization" not in html
    assert "Local validation passed" in html
    assert "test.real_operation" not in html
    assert "execution_available === true" in html
    assert "read_only_validation_ready" in html
    assert "QA READY" in html
    assert "REQUIRES AUTHORIZATION" in html
    assert "Execution verification: available" in html
    assert "Database post-condition verification: not configured" in html
    assert "LOCAL DIAGNOSTIC" in html
    assert "Automatic synthetic data" not in html
    assert "current run" in html.lower()
    assert 'id="productCatalogSummary"' in html
    assert "QA4 execution is contract-ready and requires explicit authorization." in html
    assert "NOT AVAILABLE" in html
    assert "data.execution_available !== true" in html
    assert 'const status = isContractValidation ? "Passed"' in html


def test_product_ui_marks_reserved_server_context_as_authorized_for_execution(app_client_factory):
    client, _ = app_client_factory("product-authorized-display")
    html = client.get("/").get_data(as_text=True)

    assert "const authorizationAvailable = !executeButton.disabled" in html
    assert '["Authorization", authorizationAvailable ? "Available" : "Required"' in html
    assert 'executeNote.textContent = executeButton.disabled' in html
    assert '"Ready for QA execution."' in html


def test_product_result_renders_one_dominant_status_before_secondary_metadata(app_client_factory):
    client, _ = app_client_factory("product-result-hierarchy")
    html = client.get("/").get_data(as_text=True)

    assert 'class="product-result-hero' in html
    assert 'class="product-result-meta"' in html
    assert 'class="product-result-detail"' in html
    assert 'id="productResultBody" class="product-result-body"' in html
    assert '.product-result-hero .product-result-status' in html
    assert '.product-result-hero .product-result-status {\n    background: transparent;' in html
    assert 'evidence.textContent = hasEvidenceReference ? "Evidence available for this run."' in html


def test_product_workspace_copy_and_typography_are_product_oriented(app_client_factory):
    client, _ = app_client_factory("product-copy-polish")
    html = client.get("/").get_data(as_text=True)

    assert '#panel-product .card h2' in html
    assert '#panel-product button' in html
    assert 'class="primary" id="productExecute"' in html
    assert 'through the safe local test flow' not in html
    assert 'Static plan - no QA4 request' not in html
    assert 'aria-label="Collapse sidebar"' in html
    assert "QA4 execution is contract-ready and requires explicit authorization." in html
    assert "QA4 readiness is evaluated locally." in html
    assert "Current run only; no external request." not in html
    assert "Select Validate to confirm readiness. Authorization is required to execute in QA." in html
    assert 'data.validation.strategy === "LOCAL_CUSTOMER_LINE_SIMULATION"' in html
    assert 'data.validation.result === "PASS"' in html
    assert "Add Offer needs approved integration details before it can be prepared." in html
    assert "operation-scoped" not in html
    assert "governed offer input" not in html
    assert "Integration details need approval. No request was sent." in html
    assert "product-result-status" in html
    assert 'document.getElementById("productResult").hidden = true' in html
    assert "productEvidenceReference = \"\"" in html
    assert "catch (error)" in html
    assert "LOCAL APP" not in html
    assert "DRY-RUN LOCAL" not in html
    assert 'id="diagnosticsSidebar"' in html
    assert 'diagnosticSidebar.open = name === "generator" || name === "runner"' in html
    assert 'id="panel-history"' in html
    assert 'id="tab-history"' in html
    assert 'id="historicalEvidenceList"' in html
    assert '.app.product-active .legacy-workspace-only' in html
    assert 'class="stats-bar legacy-workspace-only"' in html
    assert "View details" in html
    assert "Historical QA scenario" in html
    assert "Evidence:" not in html
    assert 'id="productCatalogSummary"' in html
    assert "QA READY / REQUIRES AUTHORIZATION" in html
    assert "Add Offer needs an approved integration contract before it can run." in html
    assert "Date unavailable" in html
    assert "consistency_reason" in html
    assert "json.hidden = false" in html
    assert "LOCAL DIAGNOSTIC" in html
    assert "UNAVAILABLE" in html
    assert "Unavailable until the required integration contract is approved." in html
    assert "productHumanStatus" in html
    assert ".product-status-badge.diagnostic" in html
    assert ".product-status-badge.unavailable" in html
    assert "const statusKind = test.id === \"recharge-basic\"" in html
    assert 'const showEvidence = Boolean(data.evidence_reference) || data.result !== "BLOCKED"' in html
    assert "productReason(data)" in html
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
    assert "Historical runs" in html
    assert "Separate from the current run" in html


def test_historical_run_ui_prioritizes_summary_and_keeps_metadata_in_details(app_client_factory):
    """A history list must not regress to a single technical evidence line."""
    client, _ = app_client_factory("product-history-summary")
    html = client.get("/").get_data(as_text=True)

    assert "historical-run-card" in html
    assert "historicalRunLabel(record)" in html
    assert "formatHistoricalTimestamp(record.timestamp)" in html
    assert "View details" in html
    assert "historical-run-technical" in html
    assert "Evidence: ${record.result}" not in html
