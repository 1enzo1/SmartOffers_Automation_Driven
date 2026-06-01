from core.adapters.fake import FakeSmartOffersAdapter
from core.execution.service import run_adapter_scenario
from core.generation import generate_scenario


def test_list_adapters_endpoint_returns_fake_adapters(app_client_factory):
    client, _ = app_client_factory("adapters")

    response = client.get("/api/adapters")

    assert response.status_code == 200
    data = response.get_json()
    adapter_ids = {adapter["adapter_id"] for adapter in data["adapters"]}
    assert data["total"] == 5
    assert {
        "fake-smartoffers",
        "fake-oracle",
        "fake-kafka",
        "fake-jenkins",
        "fake-evidence",
    }.issubset(adapter_ids)
    assert all("supported_step_types" in adapter for adapter in data["adapters"])


def test_adapters_health_endpoint_is_mocked_and_local(app_client_factory):
    client, _ = app_client_factory("adapters")

    response = client.get("/api/adapters/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "passed"
    assert all(adapter["status"] == "passed" for adapter in data["adapters"])
    assert all(adapter["details"]["external_calls"] is False for adapter in data["adapters"])


def test_adapter_run_endpoint_runs_saved_scenario_in_mock_mode(app_client_factory, valid_payload):
    client, _ = app_client_factory("adapters")
    generated = client.post(
        "/api/scenarios/generate",
        json=valid_payload(validations=["api", "database", "audit", "kafka"]),
    )
    scenario = generated.get_json()["scenario"]

    response = client.post(f"/api/scenarios/{scenario['id']}/adapter-run", json={"mode": "mock"})

    assert response.status_code == 201
    report = response.get_json()["report"]
    assert {
        "scenario_id",
        "run_id",
        "mode",
        "status",
        "adapter_results",
        "logs",
        "warnings",
        "started_at",
        "finished_at",
        "source",
    }.issubset(report)
    assert report["scenario_id"] == scenario["id"]
    assert report["mode"] == "mock"
    assert report["status"] == "passed"
    assert report["source"] == "adapter-run"
    assert report["summary"]["total"] == len(report["adapter_results"])
    assert {result["adapter_id"] for result in report["adapter_results"]}.issuperset(
        {"fake-smartoffers", "fake-oracle", "fake-kafka", "fake-evidence"}
    )
    assert any("LOCAL_ONLY" in log for log in report["logs"])


def test_adapter_run_endpoint_returns_404_for_missing_scenario(app_client_factory):
    client, _ = app_client_factory("adapters")

    response = client.post("/api/scenarios/cenario-inexistente/adapter-run", json={"mode": "mock"})

    assert response.status_code == 404
    assert response.get_json()["erro"] == "cenario nao encontrado"


def test_adapter_run_endpoint_blocks_real_mode(app_client_factory, valid_payload):
    client, _ = app_client_factory("adapters")
    generated = client.post("/api/scenarios/generate", json=valid_payload())
    scenario = generated.get_json()["scenario"]

    response = client.post(f"/api/scenarios/{scenario['id']}/adapter-run", json={"mode": "real"})

    assert response.status_code == 400
    data = response.get_json()
    assert "mode real bloqueado" in data["erro"]
    assert data["details"]["allowed_modes"] == ["mock"]


def test_adapter_run_endpoint_rejects_non_string_mode(app_client_factory, valid_payload):
    client, _ = app_client_factory("adapters")
    generated = client.post("/api/scenarios/generate", json=valid_payload())
    scenario = generated.get_json()["scenario"]

    response = client.post(f"/api/scenarios/{scenario['id']}/adapter-run", json={"mode": 1})

    assert response.status_code == 400
    data = response.get_json()
    assert "mode invalido" in data["erro"]
    assert data["details"]["allowed_modes"] == ["mock"]


def test_fake_adapter_returns_standardized_status():
    adapter = FakeSmartOffersAdapter()
    result = adapter.execute(
        {
            "id": "execution_steps-1",
            "name": "Executar evento",
            "type": "smartoffers.execution",
            "source_section": "execution_steps",
            "payload_kind": "execution",
            "controls": {"status": "failed", "message": "Falha mockada."},
            "duration_ms": 27,
        },
        {"mode": "mock", "scenario_id": "cenario"},
    )

    assert result["adapter_id"] == "fake-smartoffers"
    assert result["adapter_name"] == "Fake SmartOffers Adapter"
    assert result["status"] == "failed"
    assert result["message"] == "Falha mockada."
    assert result["metadata"]["external_calls"] is False


def test_adapter_run_service_marks_report_failed_when_step_fails(valid_payload):
    scenario = generate_scenario(valid_payload())
    scenario["execution_steps"][0]["adapter_run"] = {
        "status": "failed",
        "message": "Falha planejada no adapter.",
    }

    report = run_adapter_scenario(scenario, mode="mock")

    assert report["status"] == "failed"
    assert report["summary"]["failed"] == 1
    assert report["adapter_results"][0]["message"] == "Falha planejada no adapter."


def test_adapter_run_service_preserves_dry_run_status_and_message(valid_payload):
    scenario = generate_scenario(valid_payload())
    scenario["execution_steps"] = [scenario["execution_steps"][0]]
    scenario["validation_steps"] = []
    scenario["queries"] = []
    scenario["checkpoints"] = []
    scenario["evidence_files"] = []
    scenario["execution_steps"][0]["dry_run_status"] = "failed"
    scenario["execution_steps"][0]["dry_run_message"] = "Falha herdada do dry-run."

    report = run_adapter_scenario(scenario, mode="mock")

    assert report["status"] == "failed"
    assert report["summary"]["failed"] == 1
    assert report["adapter_results"][0]["status"] == "failed"
    assert report["adapter_results"][0]["message"] == "Falha herdada do dry-run."


def test_adapter_run_service_preserves_mock_status_and_custom_message(valid_payload):
    scenario = generate_scenario(valid_payload())
    scenario["execution_steps"] = [scenario["execution_steps"][0]]
    scenario["validation_steps"] = []
    scenario["queries"] = []
    scenario["checkpoints"] = []
    scenario["evidence_files"] = []
    scenario["execution_steps"][0]["mock_status"] = "skipped"
    scenario["execution_steps"][0]["mock_message"] = "Skip herdado do mock_status."

    report = run_adapter_scenario(scenario, mode="mock")

    assert report["status"] == "skipped"
    assert report["summary"]["skipped"] == 1
    assert report["adapter_results"][0]["status"] == "skipped"
    assert report["adapter_results"][0]["message"] == "Skip herdado do mock_status."


def test_existing_dry_run_endpoint_continues_working(app_client_factory, valid_payload):
    client, _ = app_client_factory("adapters")
    generated = client.post("/api/scenarios/generate", json=valid_payload())
    scenario = generated.get_json()["scenario"]

    response = client.post(f"/api/scenarios/{scenario['id']}/dry-run")

    assert response.status_code == 201
    report = response.get_json()["report"]
    assert report["scenario_id"] == scenario["id"]
    assert report["status"] == "passed"
    assert any("DRY_RUN|LOCAL_ONLY" in log for log in report["logs"])
