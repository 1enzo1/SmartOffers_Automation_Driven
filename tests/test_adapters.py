import json
import re

from core.adapters.fake import FakeSmartOffersAdapter
from core.api_catalog.catalog import load_api_catalog
from core.api_catalog.policy import list_mock_plannable_api_ids
from core.execution.service import run_adapter_scenario
from core.generation import generate_scenario
from core.generation.storage import save_scenario


MOCK_ONLY_API_IDS = [
    "post-vivo-next-habilitacao-de-cliente-ade0841563",
    "post-vivo-next-habilitacao-de-linha-a79ab2e31c",
    "post-o-vivo-next-troca-de-oferta-fedbfb981e",
    "post-sincronismo-e8537bd912",
    "post-ativacao-de-campanha-por-api-2e656ee31c",
    "post-evento-de-recarga-6954ef3458",
    "post-consulta-de-saldo-f3317b27b3",
    "post-evento-vivo-turbo-e124494049",
    "post-transicao-de-estado-de-servico-aceite-3751798e76",
    "post-retorno-la-xml-e73a7721f4",
]

BLOCKED_API_ID = "post-transicao-de-campanha-e56d89817e"
SAFE_HOST_PLACEHOLDERS = {"<QA4_HOST>", "<QA4_SMART_OFFERS_INT_HOST>"}


def first_http_plan_result(report):
    return next(result for result in report["adapter_results"] if result["step_type"] == "smartoffers.http_plan")


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


def test_smartoffers_request_plan_is_generated_for_mock_only_policy_apis():
    scenario = {
        "id": "smartoffers-plan-all",
        "queries": [
            {
                "name": f"plan_{index}",
                "kind": "http_plan",
                "api_id": api_id,
            }
            for index, api_id in enumerate(MOCK_ONLY_API_IDS, start=1)
        ],
    }

    report = run_adapter_scenario(scenario, mode="mock")

    assert report["status"] == "passed"
    assert report["summary"]["passed"] == len(MOCK_ONLY_API_IDS)
    plans = [result["metadata"]["request_plan"] for result in report["adapter_results"]]
    assert [plan["api_id"] for plan in plans] == MOCK_ONLY_API_IDS

    for plan in plans:
        assert {
            "api_id",
            "name",
            "category",
            "method",
            "path",
            "environment",
            "environment_variables",
            "host_placeholder",
            "host_placeholders",
            "payload_base",
            "headers_expected",
            "execution_status",
            "safe_for_real_execution",
            "source",
            "planning_mode",
        }.issubset(plan)
        assert plan["source"] == "api-catalog"
        assert plan["planning_mode"] == "mock_only"
        assert plan["environment"] == "QA4"
        assert plan["host_placeholder"] in SAFE_HOST_PLACEHOLDERS
        assert set(plan["host_placeholders"]).issubset(SAFE_HOST_PLACEHOLDERS)
        assert plan["host_placeholders"]
        assert plan["execution_status"] == "blocked"
        assert plan["safe_for_real_execution"] is False
        assert "PROD_REFERENCE_ONLY" not in json.dumps(plan, ensure_ascii=False)


def test_smartoffers_request_plan_does_not_expose_real_network_values():
    scenario = {
        "id": "smartoffers-plan-safe",
        "queries": [
            {
                "name": f"plan_safe_api_{index}",
                "kind": "http_plan",
                "api_id": api_id,
            }
            for index, api_id in enumerate(MOCK_ONLY_API_IDS, start=1)
        ],
    }

    report = run_adapter_scenario(scenario, mode="mock")
    serialized = json.dumps(
        [result["metadata"]["request_plan"] for result in report["adapter_results"]],
        ensure_ascii=False,
    )

    assert not re.search(r"https?://", serialized)
    assert not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", serialized)
    assert not re.search(r"(?i)(token|secret|password|authorization|bearer)", serialized)
    assert "QA4_Copy.json" not in serialized
    assert "APIsUtilizaveis.zip" not in serialized
    assert any(placeholder in serialized for placeholder in SAFE_HOST_PLACEHOLDERS)


def test_generated_recarga_api_validation_uses_default_catalog_request_plan(valid_payload):
    scenario = generate_scenario(
        valid_payload(
            customer_type="pre",
            event_type="recarga",
            validations=["api"],
            deadline_rule="d0",
        )
    )

    report = run_adapter_scenario(scenario, mode="mock")
    result = first_http_plan_result(report)
    plan = result["metadata"]["request_plan"]

    assert report["status"] == "passed"
    assert result["status"] == "passed"
    assert plan["api_id"] == "post-evento-de-recarga-6954ef3458"
    assert plan["category"] == "recarga"
    assert result["metadata"]["resolved_by"] == "default_http_plan_policy"


def test_generated_upsell_api_validation_uses_default_catalog_request_plan(valid_payload):
    scenario = generate_scenario(valid_payload(event_type="upsell", validations=["api"]))

    report = run_adapter_scenario(scenario, mode="mock")
    result = first_http_plan_result(report)
    plan = result["metadata"]["request_plan"]

    assert report["status"] == "passed"
    assert result["status"] == "passed"
    assert plan["api_id"] == "post-ativacao-de-campanha-por-api-2e656ee31c"
    assert plan["category"] == "campanha"
    assert result["metadata"]["resolved_by"] == "default_http_plan_policy"


def test_http_plan_without_api_id_and_unknown_event_type_is_blocked_controlled():
    scenario = {
        "id": "smartoffers-plan-unknown-default",
        "source_answers": {"event_type": "evento_desconhecido"},
        "queries": [
            {
                "name": "api_contract",
                "kind": "http_plan",
                "request": "POST /smartoffers/{{operation}}",
            }
        ],
    }

    report = run_adapter_scenario(scenario, mode="mock")
    result = report["adapter_results"][0]

    assert report["status"] == "blocked"
    assert result["status"] == "blocked"
    assert result["metadata"]["blocked"] is True
    assert result["metadata"]["block_reason"] == "api_id nao resolvido para http_plan"
    assert "request_plan" not in result["metadata"]


def test_explicit_api_id_has_priority_over_default_event_type_mapping(valid_payload):
    scenario = generate_scenario(
        valid_payload(
            customer_type="pre",
            event_type="recarga",
            validations=["api"],
            deadline_rule="d0",
        )
    )
    scenario["queries"][0]["api_id"] = "post-ativacao-de-campanha-por-api-2e656ee31c"

    report = run_adapter_scenario(scenario, mode="mock")
    result = first_http_plan_result(report)
    plan = result["metadata"]["request_plan"]

    assert report["status"] == "passed"
    assert result["status"] == "passed"
    assert plan["api_id"] == "post-ativacao-de-campanha-por-api-2e656ee31c"
    assert "resolved_by" not in result["metadata"]


def test_smartoffers_api_outside_policy_is_blocked_controlled():
    scenario = {
        "id": "smartoffers-plan-blocked",
        "queries": [
            {
                "name": "plan_blocked_api",
                "kind": "http_plan",
                "api_id": BLOCKED_API_ID,
            }
        ],
    }

    report = run_adapter_scenario(scenario, mode="mock")
    result = report["adapter_results"][0]

    assert report["status"] == "blocked"
    assert report["summary"]["blocked"] == 1
    assert result["status"] == "blocked"
    assert result["metadata"]["blocked"] is True
    assert result["metadata"]["block_reason"] == "api_id fora da policy mock_only"
    assert "request_plan" not in result["metadata"]
    assert any(BLOCKED_API_ID in warning for warning in report["warnings"])


def test_smartoffers_missing_api_id_is_blocked_controlled():
    scenario = {
        "id": "smartoffers-plan-missing",
        "queries": [
            {
                "name": "plan_missing_api",
                "kind": "http_plan",
                "api_id": "api-inexistente",
            }
        ],
    }

    report = run_adapter_scenario(scenario, mode="mock")
    result = report["adapter_results"][0]

    assert report["status"] == "blocked"
    assert report["summary"]["blocked"] == 1
    assert result["status"] == "blocked"
    assert result["metadata"]["blocked"] is True
    assert result["metadata"]["block_reason"] == "api_id inexistente no catalogo"
    assert "request_plan" not in result["metadata"]
    assert any("api-inexistente" in warning for warning in report["warnings"])


def test_smartoffers_mixed_allowed_and_outside_policy_is_blocked():
    scenario = {
        "id": "smartoffers-plan-mixed-blocked",
        "queries": [
            {
                "name": "plan_allowed_api",
                "kind": "http_plan",
                "api_id": MOCK_ONLY_API_IDS[0],
            },
            {
                "name": "plan_blocked_api",
                "kind": "http_plan",
                "api_id": BLOCKED_API_ID,
            },
        ],
    }

    report = run_adapter_scenario(scenario, mode="mock")

    assert report["status"] == "blocked"
    assert report["summary"]["passed"] == 1
    assert report["summary"]["blocked"] == 1
    assert [result["status"] for result in report["adapter_results"]] == ["passed", "blocked"]


def test_smartoffers_mixed_allowed_and_missing_api_id_is_blocked():
    scenario = {
        "id": "smartoffers-plan-mixed-missing",
        "queries": [
            {
                "name": "plan_allowed_api",
                "kind": "http_plan",
                "api_id": MOCK_ONLY_API_IDS[0],
            },
            {
                "name": "plan_missing_api",
                "kind": "http_plan",
                "api_id": "api-inexistente",
            },
        ],
    }

    report = run_adapter_scenario(scenario, mode="mock")

    assert report["status"] == "blocked"
    assert report["summary"]["passed"] == 1
    assert report["summary"]["blocked"] == 1
    assert [result["status"] for result in report["adapter_results"]] == ["passed", "blocked"]


def test_adapter_run_endpoint_accepts_smartoffers_api_id_in_http_plan(app_client_factory):
    client, _ = app_client_factory("adapters-api-id")
    scenario = {
        "id": "endpoint-smartoffers-plan",
        "titulo": "Endpoint SmartOffers Plan",
        "queries": [
            {
                "name": "api_contract",
                "kind": "http_plan",
                "api_id": MOCK_ONLY_API_IDS[0],
            }
        ],
    }
    save_scenario(scenario)

    response = client.post(f"/api/scenarios/{scenario['id']}/adapter-run", json={"mode": "mock"})

    assert response.status_code == 201
    report = response.get_json()["report"]
    result = report["adapter_results"][0]
    assert result["status"] == "passed"
    assert result["metadata"]["request_plan"]["api_id"] == MOCK_ONLY_API_IDS[0]


def test_adapter_run_endpoint_blocks_smartoffers_api_id_outside_policy(app_client_factory):
    client, _ = app_client_factory("adapters-api-id-blocked")
    scenario = {
        "id": "endpoint-smartoffers-plan-blocked",
        "titulo": "Endpoint SmartOffers Plan Blocked",
        "queries": [
            {
                "name": "api_contract",
                "kind": "http_plan",
                "api_id": BLOCKED_API_ID,
            }
        ],
    }
    save_scenario(scenario)

    response = client.post(f"/api/scenarios/{scenario['id']}/adapter-run", json={"mode": "mock"})

    assert response.status_code == 201
    report = response.get_json()["report"]
    result = report["adapter_results"][0]
    assert report["status"] == "blocked"
    assert report["summary"]["blocked"] == 1
    assert result["status"] == "blocked"
    assert result["metadata"]["blocked"] is True
    assert result["metadata"]["block_reason"] == "api_id fora da policy mock_only"


def test_adapter_run_endpoint_blocks_missing_smartoffers_api_id(app_client_factory):
    client, _ = app_client_factory("adapters-api-id-missing")
    scenario = {
        "id": "endpoint-smartoffers-plan-missing",
        "titulo": "Endpoint SmartOffers Plan Missing",
        "queries": [
            {
                "name": "api_contract",
                "kind": "http_plan",
                "api_id": "api-inexistente",
            }
        ],
    }
    save_scenario(scenario)

    response = client.post(f"/api/scenarios/{scenario['id']}/adapter-run", json={"mode": "mock"})

    assert response.status_code == 201
    report = response.get_json()["report"]
    result = report["adapter_results"][0]
    assert report["status"] == "blocked"
    assert report["summary"]["blocked"] == 1
    assert result["status"] == "blocked"
    assert result["metadata"]["blocked"] is True
    assert result["metadata"]["block_reason"] == "api_id inexistente no catalogo"


def test_api_catalog_policy_is_separate_from_versioned_catalog():
    catalog = load_api_catalog()
    catalog_by_id = {api["api_id"]: api for api in catalog}

    assert list_mock_plannable_api_ids() == sorted(MOCK_ONLY_API_IDS)
    assert all(api["execution_status"] == "blocked" for api in catalog)
    assert all(api["safe_for_real_execution"] is False for api in catalog)
    assert BLOCKED_API_ID not in list_mock_plannable_api_ids()
    assert catalog_by_id[BLOCKED_API_ID]["host_placeholder"] == "<HOST>"

    for api_id in MOCK_ONLY_API_IDS:
        entry = catalog_by_id[api_id]
        assert "QA4" in entry["environment_refs"]
        assert "PROD_REFERENCE_ONLY" not in entry["environment_refs"]
        assert entry["host_placeholder"] in SAFE_HOST_PLACEHOLDERS
        assert set(entry["host_placeholders"]).issubset(SAFE_HOST_PLACEHOLDERS)
        assert entry["host_placeholders"]


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
