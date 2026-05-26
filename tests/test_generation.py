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


def test_invalid_answers_raise_structured_error():
    with pytest.raises(ScenarioValidationError) as exc:
        generate_scenario({"campaign_name": "Incompleto"})

    assert "campaign_id" in exc.value.errors
    assert "validations" in exc.value.errors
