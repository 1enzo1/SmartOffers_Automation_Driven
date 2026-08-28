import hashlib

from core.real_execution.api_health_local_runtime_preflight import (
    API_RUNTIME_BLOCKED,
    preflight_api_health_local_runtime,
    preflight_scoped_qa4_offers_destination_attestation,
)


_URL = "https://qa4.example.invalid/smartoffers"
_REQUEST = {
    "operation": "CREATE_OFFERS_CUSTOMER",
    "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
    "environment": "QA4",
    "api_id": "post-vivo-next-habilitacao-de-cliente-ade0841563",
}


def _environment():
    return {
        "SMARTOFFERS_QA4_API_URL": _URL,
        "SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT": hashlib.sha256(
            _URL.encode("utf-8")
        ).hexdigest(),
    }


def test_scoped_create_attestation_does_not_require_generic_health_path_or_hash():
    result = preflight_scoped_qa4_offers_destination_attestation(
        _REQUEST, environ=_environment()
    )

    assert result["status"] == "QA4_SCOPED_DESTINATION_ATTESTATION_READY"
    assert result["attestation"] == {
        "source": "derived_qa4_api_url",
        "environment": "QA4",
        "operation": "CREATE_OFFERS_CUSTOMER",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "api_id": "post-vivo-next-habilitacao-de-cliente-ade0841563",
        "allowlist_match": True,
        "status": "MATCH",
    }
    assert "API_URL" not in str(result)
    assert "fingerprint" not in str(result).lower()


def test_generic_api_health_preflight_stays_fail_closed_without_path_or_hash():
    result = preflight_api_health_local_runtime(
        {
            "checkpoint": "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01",
            "api_operation_id": "smartoffers_api_health_readiness_01",
            "environment": "qa4",
            "profile": "smartoffers_qa4_full_smoke",
            "resource_id": "smartoffers_api",
        },
        environ=_environment(),
    )

    assert result["status"] == API_RUNTIME_BLOCKED
    assert "SMARTOFFERS_QA4_API_HEALTH_PATH" in result["missing_refs"]


def test_scoped_attestation_blocks_missing_url_ref_or_binding_mismatch_without_leaking_it():
    mismatched = _environment() | {
        "SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT": "not-a-match"
    }
    mismatch = preflight_scoped_qa4_offers_destination_attestation(
        _REQUEST, environ=mismatched
    )
    missing = preflight_scoped_qa4_offers_destination_attestation(
        _REQUEST, environ={}
    )

    assert mismatch["status"] == "QA4_SCOPED_DESTINATION_ATTESTATION_BLOCKED"
    assert missing["status"] == "QA4_SCOPED_DESTINATION_ATTESTATION_BLOCKED"
    assert mismatch["attestation"] == {}
    assert missing["attestation"] == {}


def test_scoped_attestation_rejects_wrong_operation_or_scenario():
    for request in (
        _REQUEST | {"operation": "OTHER_OPERATION"},
        _REQUEST | {"scenario_id": "OTHER_SCENARIO"},
        _REQUEST | {"environment": "PRODUCTION"},
        _REQUEST | {"api_id": "other-api"},
    ):
        result = preflight_scoped_qa4_offers_destination_attestation(
            request, environ=_environment()
        )
        assert result["status"] == "QA4_SCOPED_DESTINATION_ATTESTATION_BLOCKED"
        assert result["attestation"] == {}
import hashlib
