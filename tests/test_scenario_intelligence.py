import copy

from core.generation import generate_scenario
from core.intelligence import analyze_scenario


def _scenario(**overrides):
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
    return generate_scenario(payload)


def test_analyzes_upsell_scenario_with_database_and_audit_evidence():
    scenario = _scenario(validations=["api", "database", "audit", "campaign_attributes"])

    analysis = analyze_scenario(scenario)

    assert analysis["scenario_id"] == scenario["id"]
    assert analysis["domain"] == "smartoffers"
    assert analysis["event_type"] == "upsell"
    assert analysis["main_flow"] == "offer_upgrade"
    assert analysis["overall_status"] == "read-only"
    assert analysis["expected_evidence_layers"] == [
        "customer_discovery",
        "campaign_contract",
        "campaign_attributes",
        "audit_records",
        "schedule_checkpoint",
        "expected_evidence_manifest",
    ]
    assert analysis["suggested_playbooks"] == [
        "benefit-or-offer-not-updated.md",
        "processing-backlog-or-delay.md",
        "evidence-mismatch.md",
    ]
    assert "campaign-supervisor" in analysis["suggested_supervisors"]
    assert "evidence-supervisor" in analysis["suggested_supervisors"]
    assert "catalog-config-supervisor" in analysis["suggested_supervisors"]


def test_recharge_with_sms_suggests_sms_playbook():
    scenario = _scenario(
        campaign_name="Squad Pre Recarga",
        customer_type="pre",
        event_type="recarga",
        recharge_scenario="with_recharge",
        recharge_amount="30.00",
        recharge_channel="APP",
        validations=["api", "database", "campaign_attributes", "sms"],
        deadline_rule="d0",
    )

    analysis = analyze_scenario(scenario)

    assert analysis["main_flow"] == "prepaid_recharge"
    assert "sms_dispatch" in analysis["expected_evidence_layers"]
    assert "sms-not-sent.md" in analysis["suggested_playbooks"]
    assert analysis["overall_status"] == "read-only"


def test_kafka_trace_adds_adapter_supervisor_and_future_controlled_risk():
    scenario = _scenario(validations=["api", "database", "kafka"])

    analysis = analyze_scenario(scenario)

    assert "kafka_trace" in analysis["expected_evidence_layers"]
    assert "callback-not-reflected.md" in analysis["suggested_playbooks"]
    assert "adapter-supervisor" in analysis["suggested_supervisors"]
    assert {
        "code": "future_controlled_kafka_trace",
        "status": "future-controlled",
        "reason": "Kafka trace is conceptual in this MVP and requires future controlled guardrails.",
    } in analysis["risks"]
    assert analysis["overall_status"] == "future-controlled"


def test_minimal_or_incomplete_scenario_returns_safe_defaults():
    analysis = analyze_scenario({"id": "minimal"})

    assert analysis == {
        "scenario_id": "minimal",
        "domain": "smartoffers",
        "main_flow": "unknown",
        "event_type": "",
        "relevant_entities": ["cliente", "campanha"],
        "suggested_playbooks": [],
        "expected_evidence_layers": [],
        "suggested_supervisors": [
            "smartoffers-architect-supervisor",
            "safety-supervisor",
        ],
        "risks": [],
        "overall_status": "mock",
    }


def test_analyze_scenario_does_not_mutate_input_and_is_deterministic():
    scenario = _scenario(validations=["api", "database", "audit"])
    original = copy.deepcopy(scenario)

    first = analyze_scenario(scenario)
    second = analyze_scenario(scenario)

    assert scenario == original
    assert first == second


def test_blocked_status_has_precedence_over_future_and_read_only():
    scenario = _scenario(validations=["api", "database", "kafka"])
    scenario["runtime_hint"] = "mode=real"

    analysis = analyze_scenario(scenario)

    assert analysis["overall_status"] == "blocked"
    assert any(risk["status"] == "blocked" for risk in analysis["risks"])
