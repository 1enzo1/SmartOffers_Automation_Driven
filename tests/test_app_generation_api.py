import app as app_module

import uuid
from pathlib import Path


GENERATED_TEST_DIR = Path(".test_output") / "cenarios"


def valid_payload(**overrides):
    payload = {
        "campaign_name": "Squad162 Upsell",
        "campaign_id": "162",
        "system": "SmartOffers",
        "objective": "Validar bonificacao apenas para upgrade",
        "customer_type": "pos",
        "document_type": "PF",
        "event_type": "upsell",
        "validations": ["api", "database", "audit"],
        "deadline_rule": "d1",
    }
    payload.update(overrides)
    return payload


def make_client(monkeypatch):
    test_dir = GENERATED_TEST_DIR / uuid.uuid4().hex
    dryrun_dir = Path(".test_output") / "dryruns" / uuid.uuid4().hex
    monkeypatch.setenv("CENARIOS_GERADOS_PATH", str(test_dir))
    monkeypatch.setenv("DRYRUNS_GERADOS_PATH", str(dryrun_dir))
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client(), test_dir


def test_questions_endpoint_returns_guided_flow(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.get("/api/questions")

    assert response.status_code == 200
    data = response.get_json()
    assert data["questions"][0]["step"] == "campanha"
    assert any(step["step"] == "validacoes" for step in data["questions"])

    event_step = next(step for step in data["questions"] if step["step"] == "evento")
    event_options = event_step["fields"][0]["options"]
    recharge_option = next(option for option in event_options if option["value"] == "recarga")
    assert recharge_option["visible_when"] == {"customer_type": "pre"}

    deadline_step = next(step for step in data["questions"] if step["step"] == "prazo")
    deadline_values = {option["value"] for option in deadline_step["fields"][0]["options"]}
    assert {"d1", "d3", "d5", "d7"}.issubset(deadline_values)


def test_generate_endpoint_saves_and_reads_scenario(monkeypatch):
    client, test_dir = make_client(monkeypatch)

    response = client.post("/api/scenarios/generate", json=valid_payload())

    assert response.status_code == 201
    data = response.get_json()
    scenario = data["scenario"]
    saved_file = test_dir / f"{scenario['id']}.json"
    assert saved_file.exists()

    read_response = client.get(f"/api/scenarios/{scenario['id']}")

    assert read_response.status_code == 200
    assert read_response.get_json()["scenario"]["id"] == scenario["id"]


def test_list_scenarios_endpoint_returns_saved_summaries(monkeypatch):
    client, _ = make_client(monkeypatch)

    first = client.post("/api/scenarios/generate", json=valid_payload())
    second = client.post(
        "/api/scenarios/generate",
        json=valid_payload(
            campaign_name="Squad162 Mailing",
            event_type="mailing",
            customer_type="pre",
            validations=["api", "database"],
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get("/api/scenarios")

    assert response.status_code == 200
    scenarios = response.get_json()["scenarios"]
    scenario_ids = {scenario["id"] for scenario in scenarios}
    assert first.get_json()["scenario"]["id"] in scenario_ids
    assert second.get_json()["scenario"]["id"] in scenario_ids
    assert all("validation_count" in scenario for scenario in scenarios)


def test_generate_endpoint_returns_validation_errors(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post("/api/scenarios/generate", json={"campaign_name": "Falho"})

    assert response.status_code == 400
    data = response.get_json()
    assert "details" in data
    assert "campaign_id" in data["details"]


def test_dry_run_endpoint_simulates_saved_scenario(monkeypatch):
    client, _ = make_client(monkeypatch)
    generate_response = client.post("/api/scenarios/generate", json=valid_payload())
    scenario = generate_response.get_json()["scenario"]

    response = client.post(f"/api/scenarios/{scenario['id']}/dry-run")

    assert response.status_code == 201
    data = response.get_json()
    report = data["report"]
    assert {
        "id",
        "scenario_id",
        "status",
        "started_at",
        "finished_at",
        "duration_ms",
        "steps",
        "summary",
        "logs",
        "warnings",
    }.issubset(report)
    assert report["scenario_id"] == scenario["id"]
    assert report["status"] == "passed"
    assert report["summary"]["total"] == len(scenario["execution_steps"]) + len(
        scenario["validation_steps"]
    )
    assert report["steps"][0]["type"] == "execution"
    assert report["steps"][0]["status"] == "passed"
    assert Path(data["saved_path"]).exists()
    assert any("LOCAL_ONLY" in log for log in report["logs"])


def test_dry_run_endpoint_returns_error_when_scenario_does_not_exist(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post("/api/scenarios/cenario-inexistente/dry-run")

    assert response.status_code == 404
    assert response.get_json()["erro"] == "cenario nao encontrado"


def test_existing_routes_still_respond(monkeypatch):
    client, _ = make_client(monkeypatch)

    assert client.get("/").status_code == 200
    assert client.get("/listar_testes").status_code == 200

    response = client.get("/executar?tipo=invalid&analisar=false", buffered=True)
    assert response.status_code == 200
    assert "ERROR|tipo inválido" in response.get_data(as_text=True)
