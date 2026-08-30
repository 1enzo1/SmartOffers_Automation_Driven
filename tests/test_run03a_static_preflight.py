import pytest

from core.real_execution.run03a_static_preflight import build_run03a_static_preflight


READY = {key: True for key in (
    "product_real_binding_complete", "server_context_ready", "context_single_use_ready",
    "standard_runner_mapping_ready", "real_controlled_bridge_ready", "adapter_ready",
    "destination_attestation_contract_ready", "synthetic_data_ready", "one_shot_ledger_ready",
    "evidence_capture_ready", "active_run_evidence_view_ready", "pass_fail_blocked_mapping_ready",
)} | {"attempts_used": "0/1", "production": False}


def test_run03a_static_preflight_ready_without_synthesizing_live_gates():
    report = build_run03a_static_preflight(READY)
    assert report["status"] == "READY_EXCEPT_OWNER_AUTHORIZATION_AND_LIVE_RUNTIME"
    assert report["db_postcondition_validation_ready"] is False


def test_run03a_static_preflight_blocks_missing_gate_and_malformed_input():
    missing = dict(READY, adapter_ready=False)
    assert build_run03a_static_preflight(missing)["status"] == "BLOCKED"
    assert build_run03a_static_preflight([])["reason"] == "MALFORMED_PREFLIGHT_INPUT"


def test_run03a_static_preflight_blocks_production_and_nonzero_attempts():
    assert build_run03a_static_preflight(dict(READY, production=True))["status"] == "BLOCKED"
    assert build_run03a_static_preflight(dict(READY, attempts_used="1/1"))["status"] == "BLOCKED"


@pytest.mark.parametrize("value", ["false", "False", None, 0, 1, True])
def test_run03a_static_preflight_rejects_non_false_production_values(value):
    report = build_run03a_static_preflight(dict(READY, production=value))
    assert report["status"] == "BLOCKED"


def test_run03a_static_preflight_rejects_missing_production_and_unknown_fields():
    missing = dict(READY)
    del missing["production"]
    assert build_run03a_static_preflight(missing)["status"] == "BLOCKED"
    assert build_run03a_static_preflight(dict(READY, unexpected=True))["status"] == "BLOCKED"


def test_run03a_static_preflight_exposes_each_gate():
    report = build_run03a_static_preflight(READY)
    assert report["gates"]["product_real_binding_complete"] is True
    assert report["gates"]["production"] is True
