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
    monkeypatch.setenv("CENARIOS_GERADOS_PATH", str(test_dir))
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client(), test_dir


def test_questions_endpoint_returns_guided_flow(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.get("/api/questions")

    assert response.status_code == 200
    data = response.get_json()
    assert data["questions"][0]["step"] == "campanha"
    assert any(step["step"] == "validacoes" for step in data["questions"])


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


def test_existing_routes_still_respond(monkeypatch):
    client, _ = make_client(monkeypatch)

    assert client.get("/").status_code == 200
    assert client.get("/listar_testes").status_code == 200

    response = client.get("/executar?tipo=invalid&analisar=false", buffered=True)
    assert response.status_code == 200
    assert "ERROR|tipo inválido" in response.get_data(as_text=True)
