from pathlib import Path

from core.utils.evidence_payload_contract import (
    analyze_payload_contract,
    clone_payload,
    compare_payload_contracts,
)


ROOT = Path(__file__).resolve().parents[1]
IGNORED_ZIP_SCAN_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".pytest_tmp",
    ".test_output",
    ".test_smoke",
    "evidencias",
    "evidencias_variante",
    "evidencias_teste_auto",
    "cenarios_gerados",
    "dryruns_gerados",
    "exports_gerados",
}


def _complete_payload():
    return {
        "operation": "processEvent",
        "extEventId": 1001,
        "eventTime": "12-06-2026 09:19:02",
        "attributes": {
            "ATTR_ACCOUNT": "<ACCOUNT_REF>",
            "ATTR_OFFER": "<OFFER_REF>",
        },
        "attributeDetails": {
            "ATTR_ACCOUNT": {"type": "String", "name": "ACCOUNT"},
            "ATTR_OFFER": {"type": "String", "name": "OFFER"},
        },
    }


def test_functional_payload_contains_attribute_details():
    result = analyze_payload_contract(_complete_payload())

    assert result["status"] == "complete"
    assert result["classification"] == "complete_payload"
    assert result["attributes_count"] == 2
    assert result["attribute_details_count"] == 2
    assert result["missing_attribute_details"] == []
    assert result["event_time_shape"] == "dd-mm-yyyy HH:MM:SS"


def test_each_sent_attribute_requires_matching_metadata():
    payload = _complete_payload()
    payload["attributeDetails"].pop("ATTR_OFFER")

    result = analyze_payload_contract(payload)

    assert result["status"] == "incomplete"
    assert result["classification"] == "incomplete_attribute_metadata_gap"
    assert result["missing_attribute_details"] == ["ATTR_OFFER"]
    assert "attribute_metadata_missing" in result["issues"]


def test_variant_or_copy_payload_without_attribute_details_is_incomplete():
    payload = _complete_payload()
    payload.pop("attributeDetails")

    result = analyze_payload_contract(payload)

    assert result["status"] == "incomplete"
    assert result["classification"] == "incomplete_missing_attribute_details"
    assert result["attribute_details_count"] == 0
    assert sorted(result["missing_attribute_details"]) == ["ATTR_ACCOUNT", "ATTR_OFFER"]


def test_payload_contract_comparison_is_pure_and_local():
    reference = _complete_payload()
    candidate = clone_payload(reference)
    candidate.pop("attributeDetails")

    comparison = compare_payload_contracts(reference, candidate)

    assert comparison["candidate_is_regression"] is True
    assert comparison["attribute_details_delta"] == -2
    assert comparison["attributes_delta"] == 0
    assert comparison["event_time_shape_changed"] is False
    assert "attributeDetails" in reference


def test_raw_evidence_zips_are_not_versioned_and_remain_ignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "evidencias/" in gitignore
    assert "evidencias_variante/" in gitignore
    assert "*.zip" in gitignore

    gitignore_rules = set(gitignore.splitlines())
    zip_files = [
        path
        for path in ROOT.rglob("*.zip")
        if not set(path.relative_to(ROOT).parts) & {".git", ".venv", "venv", "__pycache__"}
    ]

    assert all(_is_zip_covered_by_gitignore(path, gitignore_rules) for path in zip_files)


def _is_zip_covered_by_gitignore(path, gitignore_rules):
    relative_parts = path.relative_to(ROOT).parts
    ignored_dir_rules = {f"{part}/" for part in relative_parts}
    return ("*.zip" in gitignore_rules and path.suffix == ".zip") or bool(
        ignored_dir_rules & gitignore_rules & {f"{name}/" for name in IGNORED_ZIP_SCAN_DIRS}
    )
