import uuid
from pathlib import Path

import pytest

import app as app_module


# Each test module has one primary routing tier.  The mapping is intentionally
# explicit so a new module cannot silently enter the fast local loop.
TIER_FILE_MAP = {
    "test_generation.py": "tier0", "test_scenario_intelligence.py": "tier0",
    "test_simulation.py": "tier0", "test_template_library.py": "tier0",
    "test_adapters.py": "tier0", "test_adapter_risk_classifier.py": "tier0",
    "test_adapter_ui.py": "tier0", "test_api_catalog.py": "tier0",
    "test_app_generation_api.py": "tier0", "test_execution_mode_selector.py": "tier0",
    "test_export_artifacts_api.py": "tier0", "test_product_test_catalog_api.py": "tier0",
    "test_evidence_payload_builders.py": "tier0", "test_evidence_payload_contract.py": "tier0",
    "test_legacy_execution_result_semantics.py": "tier0", "test_gate_dag.py": "tier0",
    "test_qa4_standard_mock_api.py": "tier0", "test_qa4_standard_mock_facade.py": "tier0",
    "test_qa4_standard_mock_runner.py": "tier0", "test_qa4_standard_mock_ui.py": "tier0",
    "test_qa4_bda_mock_executor.py": "tier0", "test_smoke_consolidation.py": "tier0",
    "test_test_tier_contract.py": "tier0",
    "test_sanitized_evidence.py": "tier1", "test_operational_release_store.py": "tier1",
    "test_acm_local_runtime_preflight.py": "tier1", "test_bda_local_runtime_preflight.py": "tier1",
    "test_qa4_bda_offer_discovery.py": "tier1", "test_qa4_offers_customer_adapter.py": "tier1",
    "test_qa4_real_controlled_bridge.py": "tier1", "test_qa4_scoped_destination_attestation.py": "tier1",
    "test_first_qa4_call_executor.py": "tier1", "test_real_execution_hardening.py": "tier1",
    "test_real_execution_readiness.py": "tier1", "test_real_execution_runtime_contract.py": "tier1",
    "test_qa4_api_health_checkpoint.py": "tier1",
    "test_documentation_guardrails.py": "tier2", "test_runtime_local_template.py": "tier2",
    "test_manual_qa4_readiness_package.py": "tier2", "test_manual_smoke_plan.py": "tier2",
    "test_legacy_real_script_safety.py": "tier2",
    "test_qa4_acm_manual_smoke.py": "tier3", "test_qa4_bda_manual_smoke.py": "tier3",
    "test_qa4_manual_smoke.py": "tier3", "test_first_qa4_real_call_manual_gate.py": "tier3",
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        filename = Path(str(item.fspath)).name
        tier = TIER_FILE_MAP.get(filename)
        if tier:
            item.add_marker(tier)
            if tier == "tier3":
                item.add_marker("manual_external")


@pytest.fixture
def app_client_factory(monkeypatch):
    def make_client(area="api"):
        base = Path(".test_output") / area / uuid.uuid4().hex
        monkeypatch.setenv("CENARIOS_GERADOS_PATH", str(base / "cenarios"))
        monkeypatch.setenv("DRYRUNS_GERADOS_PATH", str(base / "dryruns"))
        monkeypatch.setenv("EXPORTS_GERADOS_PATH", str(base / "exports"))
        app_module.app.config.update(TESTING=True)
        return app_module.app.test_client(), base

    return make_client


@pytest.fixture
def valid_payload():
    def make_payload(**overrides):
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

    return make_payload


@pytest.fixture
def generation_answers(valid_payload):
    def make_answers(**overrides):
        payload = valid_payload(validations=["api", "database", "audit", "campaign_attributes"])
        payload.update(overrides)
        return payload

    return make_answers
