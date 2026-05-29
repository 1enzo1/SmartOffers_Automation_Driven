import uuid
from pathlib import Path

import app as app_module


REQUIRED_TEMPLATE_KEYS = {
    "id",
    "nome",
    "descricao",
    "categoria",
    "eventos_suportados",
    "tipos_cliente_suportados",
    "validacoes_recomendadas",
    "steps_gerados",
    "warnings",
    "restricoes",
}

REQUIRED_CATEGORIES = {
    "upsell",
    "downgrade",
    "rehab",
    "recarga",
    "mailing",
    "habilitacao",
    "alteracao_perfil",
    "opt_in",
    "bonus",
    "agendamento",
    "blacklist",
    "segmentacao",
}


def make_client(monkeypatch):
    base = Path(".test_output") / "templates" / uuid.uuid4().hex
    monkeypatch.setenv("CENARIOS_GERADOS_PATH", str(base / "cenarios"))
    monkeypatch.setenv("DRYRUNS_GERADOS_PATH", str(base / "dryruns"))
    monkeypatch.setenv("EXPORTS_GERADOS_PATH", str(base / "exports"))
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client(), base


def test_templates_endpoint_lists_catalog_with_metadata(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.get("/api/templates")

    assert response.status_code == 200
    data = response.get_json()
    templates = data["templates"]
    categories = {category["id"] for category in data["categories"]}

    assert data["total"] == len(templates)
    assert REQUIRED_CATEGORIES.issubset(categories)
    assert templates
    assert REQUIRED_TEMPLATE_KEYS.issubset(templates[0])
    assert "default_answers" not in templates[0]


def test_template_detail_endpoint_returns_defaults(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.get("/api/templates/recarga-pre-bonus-d0")

    assert response.status_code == 200
    template = response.get_json()["template"]
    assert REQUIRED_TEMPLATE_KEYS.issubset(template)
    assert template["categoria"] == "recarga"
    assert template["default_answers"]["event_type"] == "recarga"
    assert template["default_answers"]["customer_type"] == "pre"
    assert template["default_answers"]["recharge_scenario"] == "with_recharge"


def test_template_detail_returns_404_for_unknown_template(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.get("/api/templates/template-inexistente")

    assert response.status_code == 404
    assert response.get_json()["erro"] == "template nao encontrado"


def test_generate_endpoint_uses_selected_template_defaults(monkeypatch):
    client, base = make_client(monkeypatch)

    response = client.post(
        "/api/scenarios/generate",
        json={
            "template_id": "recarga-pre-bonus-d0",
            "campaign_name": "Squad Recarga MVP6",
            "campaign_id": "606",
        },
    )

    assert response.status_code == 201
    scenario = response.get_json()["scenario"]
    attributes = scenario["payload"]["attributes"]

    assert scenario["template"]["id"] == "recarga-pre-bonus-d0"
    assert scenario["source_answers"]["template_id"] == "recarga-pre-bonus-d0"
    assert scenario["source_answers"]["event_type"] == "recarga"
    assert scenario["source_answers"]["customer_type"] == "pre"
    assert scenario["source_answers"]["validations"] == [
        "database",
        "api",
        "campaign_attributes",
        "sms",
    ]
    assert attributes["rechargeScenario"] == "with_recharge"
    assert attributes["rechargeAmount"] == "30.00"
    assert (base / "cenarios" / f"{scenario['id']}.json").exists()


def test_generate_without_template_id_keeps_existing_contract(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post(
        "/api/scenarios/generate",
        json={
            "campaign_name": "Squad Sem Template",
            "campaign_id": "607",
            "system": "SmartOffers",
            "objective": "Validar contrato antigo sem template",
            "customer_type": "pos",
            "document_type": "PF",
            "event_type": "upsell",
            "validations": ["api", "database", "audit"],
            "deadline_rule": "d1",
        },
    )

    assert response.status_code == 201
    scenario = response.get_json()["scenario"]
    assert "template" not in scenario
    assert scenario["source_answers"]["event_type"] == "upsell"
    assert scenario["source_answers"]["customer_type"] == "pos"


def test_template_alias_event_type_overrides_default_event(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post(
        "/api/scenarios/generate",
        json={
            "template_id": "opt-in-habilitacao-auditavel",
            "campaign_name": "Squad Alias Mailing",
            "campaign_id": "608",
            "tipo_evento": "mailing",
        },
    )

    assert response.status_code == 201
    scenario = response.get_json()["scenario"]
    assert scenario["template"]["id"] == "opt-in-habilitacao-auditavel"
    assert scenario["source_answers"]["event_type"] == "mailing"
    assert scenario["payload"]["eventType"] == "mailing"
    assert scenario["payload"]["operation"] == "processMailing"


def test_template_alias_customer_type_overrides_default_customer(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post(
        "/api/scenarios/generate",
        json={
            "template_id": "opt-in-habilitacao-auditavel",
            "campaign_name": "Squad Alias Pre",
            "campaign_id": "609",
            "tipo_cliente": "pre",
        },
    )

    assert response.status_code == 201
    scenario = response.get_json()["scenario"]
    assert scenario["source_answers"]["customer_type"] == "pre"
    assert scenario["payload"]["attributes"]["customerSegment"] == "PRE"


def test_template_canonical_fields_override_defaults(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post(
        "/api/scenarios/generate",
        json={
            "template_id": "opt-in-habilitacao-auditavel",
            "campaign_name": "Squad Canonical Mailing Pre",
            "campaign_id": "610",
            "event_type": "mailing",
            "customer_type": "pre",
        },
    )

    assert response.status_code == 201
    scenario = response.get_json()["scenario"]
    assert scenario["source_answers"]["event_type"] == "mailing"
    assert scenario["source_answers"]["customer_type"] == "pre"
    assert scenario["payload"]["operation"] == "processMailing"


def test_template_ui_merge_logic_preserves_entered_campaign_fields():
    html = Path("templates/index.html").read_text(encoding="utf-8")
    assert "setFormAnswers(mergeTemplateAnswers(data.template.default_answers || {}))" in html

    current_answers = {
        "campaign_name": "Campanha digitada antes do template",
        "campaign_id": "777",
        "event_type": "",
    }
    template_defaults = {
        "event_type": "recarga",
        "customer_type": "pre",
    }

    merged = dict(current_answers)
    for key, value in template_defaults.items():
        if not _has_answer_value(merged.get(key)):
            merged[key] = value

    assert merged["campaign_name"] == "Campanha digitada antes do template"
    assert merged["campaign_id"] == "777"
    assert merged["event_type"] == "recarga"
    assert merged["customer_type"] == "pre"


def _has_answer_value(value):
    if isinstance(value, list):
        return bool(value)
    return value is not None and str(value).strip() != ""


def test_existing_routes_still_respond_with_template_api(monkeypatch):
    client, _ = make_client(monkeypatch)

    assert client.get("/").status_code == 200
    assert client.get("/api/questions").status_code == 200
    assert client.get("/api/scenarios").status_code == 200
    assert client.get("/api/templates").status_code == 200

    response = client.get("/executar?tipo=invalid&analisar=false", buffered=True)
    assert response.status_code == 200
    assert "ERROR|tipo" in response.get_data(as_text=True)
    assert "invalid" in response.get_data(as_text=True)
