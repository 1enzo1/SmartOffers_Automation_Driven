import ast
from pathlib import Path

from core.utils.evidence_payload_builders import (
    build_postpaid_payload,
    build_prepaid_payload,
)
from core.utils.evidence_payload_contract import (
    analyze_payload_contract,
    compare_payload_contracts,
)


SAMPLE_MSISDN = "LIN00000000"
SAMPLE_OFFER = "OFFER_REF"
SAMPLE_EVENT_TIME = "12-06-2026 09:19:02"
SAMPLE_ATTRIBUTE_TIME = "2026-06-12 09:19:02"
ROOT = Path(__file__).resolve().parents[1]


def test_standard_postpaid_payload_remains_complete():
    payload, external_id = build_postpaid_payload(
        SAMPLE_MSISDN,
        SAMPLE_OFFER,
        event_time=SAMPLE_EVENT_TIME,
    )

    result = analyze_payload_contract(payload)

    assert external_id == "NEXT_00000000"
    assert result["status"] == "complete"
    assert result["attributes_count"] == 14
    assert result["attribute_details_count"] == 14
    assert result["missing_attribute_details"] == []


def test_variant_payloads_include_attribute_details_for_each_attribute():
    pos_payload, _ = build_postpaid_payload(
        SAMPLE_MSISDN,
        SAMPLE_OFFER,
        event_time=SAMPLE_EVENT_TIME,
    )
    pre_payload, _ = build_prepaid_payload(
        SAMPLE_MSISDN,
        event_time=SAMPLE_EVENT_TIME,
        attribute_time=SAMPLE_ATTRIBUTE_TIME,
    )

    for payload in (pos_payload, pre_payload):
        result = analyze_payload_contract(payload)
        assert result["status"] == "complete"
        assert set(payload["attributes"]) == set(payload["attributeDetails"])


def test_copy_pre_payload_is_not_reduced_and_keeps_metadata():
    payload, external_id = build_prepaid_payload(
        SAMPLE_MSISDN,
        event_time=SAMPLE_EVENT_TIME,
        attribute_time=SAMPLE_ATTRIBUTE_TIME,
        profile="559",
        account_state="2",
    )

    result = analyze_payload_contract(payload)

    assert external_id == "NGIN_00000000"
    assert result["status"] == "complete"
    assert result["attributes_count"] == 20
    assert result["attribute_details_count"] == 20
    assert payload["attributes"]["908881601"] == "2"
    assert payload["attributes"]["1190622368"] == "559"


def test_corrected_variant_and_copy_payloads_are_not_regressions():
    reference, _ = build_postpaid_payload(
        SAMPLE_MSISDN,
        SAMPLE_OFFER,
        event_time=SAMPLE_EVENT_TIME,
    )
    corrected_variant, _ = build_postpaid_payload(
        SAMPLE_MSISDN,
        SAMPLE_OFFER,
        event_time=SAMPLE_EVENT_TIME,
    )
    corrected_copy_pre, _ = build_prepaid_payload(
        SAMPLE_MSISDN,
        event_time=SAMPLE_EVENT_TIME,
        attribute_time=SAMPLE_ATTRIBUTE_TIME,
    )

    assert compare_payload_contracts(reference, corrected_variant)[
        "candidate_is_regression"
    ] is False
    assert compare_payload_contracts(reference, corrected_copy_pre)[
        "candidate_is_regression"
    ] is False


def test_variant_and_copy_scripts_use_pure_payload_builders_without_importing_them():
    for script_name in ("test_campaign_api_variante.py", "test_campaign_api_variante_copy.py"):
        tree = ast.parse((ROOT / script_name).read_text(encoding="utf-8"))
        call_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

        assert "build_postpaid_payload" in call_names
        assert "build_prepaid_payload" in call_names
