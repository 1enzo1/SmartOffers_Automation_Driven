import json

import pytest

from core.generation import ScenarioValidationError, generate_scenario


def base_answers(**overrides):
    answers = {
        "campaign_name": "Squad162 Upsell",
        "campaign_id": "162",
        "system": "SmartOffers",
        "objective": "Validar bonificacao apenas para upgrade",
        "customer_type": "pos",
        "document_type": "PF",
        "event_type": "upsell",
        "validations": ["api", "database", "audit", "campaign_attributes"],
        "deadline_rule": "d1",
    }
    answers.update(overrides)
    return answers


@pytest.mark.parametrize(
    ("customer_type", "event_type", "ext_event_id", "operation"),
    [
        ("pos", "upsell", 986557550, "processEvent"),
        ("pre", "rehab", 866231225, "processEvent"),
        ("pos", "downgrade", 986557550, "processEvent"),
        ("pre", "mailing", 866231225, "processMailing"),
    ],
)
def test_generates_expected_payload_by_customer_and_event(
    customer_type, event_type, ext_event_id, operation
):
    scenario = generate_scenario(
        base_answers(customer_type=customer_type, event_type=event_type)
    )

    assert scenario["payload"]["extEventId"] == ext_event_id
    assert scenario["payload"]["operation"] == operation
    assert scenario["payload"]["eventType"] == event_type
    assert scenario["source_answers"]["customer_type"] == customer_type
    assert scenario["execution_steps"]
    assert scenario["validation_steps"]


def test_prepaid_recharge_generates_recharge_plan():
    scenario = generate_scenario(
        base_answers(
            campaign_name="Squad Pre Recarga",
            customer_type="pre",
            event_type="recarga",
            recharge_scenario="with_recharge",
            recharge_amount="30.00",
            recharge_channel="APP",
            validations=["api", "database", "campaign_attributes", "sms"],
            deadline_rule="d0",
        )
    )

    attributes = scenario["payload"]["attributes"]
    actions = [step["action"] for step in scenario["execution_steps"]]
    validations = [step["validation"] for step in scenario["validation_steps"]]

    assert scenario["payload"]["operation"] == "processRecharge"
    assert scenario["payload"]["eventType"] == "recarga"
    assert attributes["rechargeAmount"] == "30.00"
    assert attributes["rechargeChannel"] == "APP"
    assert any("recarga" in action.lower() for action in actions)
    assert "Validar SMS/mensagem" in validations


@pytest.mark.parametrize(
    ("event_type", "initial_offer", "target_offer", "expected_text"),
    [
        ("upsell", "122429157", "104376082", "upgrade"),
        ("downgrade", "104376082", "122429157", "downgrade"),
    ],
)
def test_postpaid_offer_change_templates(event_type, initial_offer, target_offer, expected_text):
    scenario = generate_scenario(
        base_answers(
            customer_type="pos",
            event_type=event_type,
            validations=["api", "database", "campaign_attributes", "audit"],
            deadline_rule="d0",
        )
    )

    attributes = scenario["payload"]["attributes"]
    execution_text = " ".join(step["action"] for step in scenario["execution_steps"]).lower()

    assert attributes["initialOffer"] == initial_offer
    assert attributes["targetOffer"] == target_offer
    assert attributes["profileBeforeOffer"] == initial_offer
    assert attributes["profileAfterOffer"] == target_offer
    assert expected_text in execution_text


def test_mailing_generates_import_blocks_payload_and_queries():
    scenario = generate_scenario(
        base_answers(
            campaign_name="Squad Mailing",
            customer_type="pre",
            event_type="mailing",
            mailing_source="base_segmentada",
            validations=["api", "database"],
            deadline_rule="d0",
        )
    )

    actions = [step["action"] for step in scenario["execution_steps"]]
    query_names = {query["name"] for query in scenario["queries"]}

    assert scenario["payload"]["operation"] == "processMailing"
    assert scenario["payload"]["attributes"]["mailingSource"] == "base_segmentada"
    assert "Preparar arquivo/lista de mailing" in actions
    assert "campaign_contract" in query_names


@pytest.mark.parametrize("deadline_rule", ["d1", "d3"])
def test_scheduled_deadlines_add_schedule_checkpoint(deadline_rule):
    scenario = generate_scenario(base_answers(deadline_rule=deadline_rule))

    query_names = {query["name"] for query in scenario["queries"]}
    validations = [step["validation"] for step in scenario["validation_steps"]]

    assert any("Checkpoint de agendamento" in item for item in scenario["checkpoints"])
    assert "Validar agendamento futuro" in validations
    assert "schedule_checkpoint" in query_names
    assert "11_schedule_checkpoint.json" in scenario["evidence_files"]


def test_generation_is_deterministic_for_same_answers():
    first = generate_scenario(base_answers(validations=["database", "api", "audit"]))
    second = generate_scenario(base_answers(validations=["audit", "api", "database"]))

    assert first["id"] == second["id"]
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_includes_queries_checkpoints_and_evidence_files():
    scenario = generate_scenario(
        base_answers(
            validations=[
                "api",
                "database",
                "audit",
                "campaign_attributes",
                "kafka",
                "sms",
                "received_events",
            ]
        )
    )

    query_names = {query["name"] for query in scenario["queries"]}

    assert "customer_discovery" in query_names
    assert "campaign_attributes" in query_names
    assert "audit_records" in query_names
    assert "kafka_trace" in query_names
    assert "sms_dispatch" in query_names
    assert "Validacao obrigatoria: API." in scenario["checkpoints"]
    assert "resumo_analise.json" in scenario["evidence_files"]
    assert "12_expected_evidence_manifest.json" in scenario["evidence_files"]


def test_multiple_validations_expand_into_coherent_blocks():
    scenario = generate_scenario(
        base_answers(validations=["database", "campaign_attributes", "audit", "sms"])
    )

    validations = [step["validation"] for step in scenario["validation_steps"]]

    assert validations[:2] == [
        "Validar discovery do cliente",
        "Validar contrato da campanha",
    ]
    assert "Validar Campaign Attributes obrigatorios" in validations
    assert "Validar auditoria" in validations
    assert "Validar SMS/mensagem" in validations
    assert "Validar evidencias esperadas" in validations


def test_invalid_answers_raise_structured_error():
    with pytest.raises(ScenarioValidationError) as exc:
        generate_scenario({"campaign_name": "Incompleto"})

    assert "campaign_id" in exc.value.errors
    assert "validations" in exc.value.errors


def test_recharge_requires_prepaid_customer():
    with pytest.raises(ScenarioValidationError) as exc:
        generate_scenario(base_answers(customer_type="pos", event_type="recarga"))

    assert "event_type" in exc.value.errors
