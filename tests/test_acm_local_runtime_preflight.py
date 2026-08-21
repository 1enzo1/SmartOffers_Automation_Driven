import hashlib
import inspect

import pytest

from core.real_execution import acm_local_runtime_preflight
from core.real_execution.acm_local_runtime_preflight import (
    ACM_CHECKPOINT,
    ACM_REQUIRED_REFS,
    ACM_RESOURCE_ID,
    ACM_RUNTIME_BLOCKED,
    ACM_RUNTIME_READY,
    ACM_ENVIRONMENT,
    ACM_PROFILE,
    preflight_acm_local_runtime,
)


def _sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _request(**overrides):
    request = {
        "checkpoint": ACM_CHECKPOINT,
        "environment": ACM_ENVIRONMENT,
        "profile": ACM_PROFILE,
        "resource_id": ACM_RESOURCE_ID,
    }
    request.update(overrides)
    return request


def _fake_runtime():
    sql = "SELECT fake_technical_check FROM fake_dual"
    dsn = "fake-acm-dsn"
    return {
        "SMARTOFFERS_QA4_ACM_DB_DSN": dsn,
        "SMARTOFFERS_QA4_ACM_DB_USER": "fake-acm-user",
        "SMARTOFFERS_QA4_ACM_DB_PASSWORD": "fake-acm-password",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-oracle-client-dir",
        "SMARTOFFERS_QA4_ACM_SMOKE_SQL": sql,
        "SMARTOFFERS_QA4_ACM_SMOKE_SQL_SHA256": _sha256(sql),
        "SMARTOFFERS_QA4_ACM_DESTINATION_FINGERPRINT": _sha256(dsn),
    }


def test_acm_preflight_returns_ready_only_for_complete_matching_runtime():
    result = preflight_acm_local_runtime(_request(), _fake_runtime())

    assert result == {
        "status": ACM_RUNTIME_READY,
        "checkpoint": ACM_CHECKPOINT,
        "environment": ACM_ENVIRONMENT,
        "profile": ACM_PROFILE,
        "resource_id": ACM_RESOURCE_ID,
        "allowlist_validation": "MATCH",
        "refs_validation": "READY",
        "sql_hash_validation": "MATCH",
        "fingerprint_validation": "MATCH",
        "checked_refs": list(ACM_REQUIRED_REFS),
        "missing_refs": [],
    }


@pytest.mark.parametrize("missing_ref", ACM_REQUIRED_REFS)
def test_acm_preflight_blocks_each_missing_required_ref(missing_ref):
    runtime = _fake_runtime()
    runtime.pop(missing_ref)

    result = preflight_acm_local_runtime(_request(), runtime)

    assert result["status"] == ACM_RUNTIME_BLOCKED
    assert result["refs_validation"] == "BLOCKED"
    assert result["missing_refs"] == [missing_ref]


def test_acm_preflight_blocks_sql_hash_mismatch():
    runtime = _fake_runtime()
    runtime["SMARTOFFERS_QA4_ACM_SMOKE_SQL_SHA256"] = "different-fake-hash"

    result = preflight_acm_local_runtime(_request(), runtime)

    assert result["status"] == ACM_RUNTIME_BLOCKED
    assert result["sql_hash_validation"] == "DENIED"
    assert result["fingerprint_validation"] == "MATCH"


def test_acm_preflight_blocks_destination_fingerprint_mismatch():
    runtime = _fake_runtime()
    runtime["SMARTOFFERS_QA4_ACM_DESTINATION_FINGERPRINT"] = "different-fake-fingerprint"

    result = preflight_acm_local_runtime(_request(), runtime)

    assert result["status"] == ACM_RUNTIME_BLOCKED
    assert result["sql_hash_validation"] == "MATCH"
    assert result["fingerprint_validation"] == "DENIED"


def test_acm_preflight_does_not_accept_acm_custom_refs():
    runtime = {
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN": "fake-custom-dsn",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER": "fake-custom-user",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD": "fake-custom-password",
        "SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL": "fake-custom-sql",
        "SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256": "fake-custom-hash",
        "SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT": "fake-custom-fingerprint",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-oracle-client-dir",
    }

    result = preflight_acm_local_runtime(_request(), runtime)

    assert result["status"] == ACM_RUNTIME_BLOCKED
    assert result["missing_refs"] == [
        ref for ref in ACM_REQUIRED_REFS if ref != "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR"
    ]
    assert all("ACM_CUSTOM" not in ref for ref in result["checked_refs"])


@pytest.mark.parametrize(
    "overrides",
    [
        {"checkpoint": "ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01"},
        {"resource_id": "acm_custom_db"},
        {"environment": "qa3"},
        {"profile": "smartoffers_basic_smoke"},
    ],
)
def test_acm_preflight_blocks_any_allowlist_mismatch(overrides):
    result = preflight_acm_local_runtime(_request(**overrides), _fake_runtime())

    assert result["status"] == ACM_RUNTIME_BLOCKED
    assert result["allowlist_validation"] == "DENIED"


def test_acm_preflight_output_never_contains_fake_runtime_values():
    runtime = _fake_runtime()
    rendered = repr(preflight_acm_local_runtime(_request(), runtime))

    assert all(value not in rendered for value in runtime.values())


def test_acm_preflight_module_has_no_oracle_or_network_dependency():
    source = inspect.getsource(acm_local_runtime_preflight)

    assert "oracledb" not in source
    assert "socket" not in source
    assert "subprocess" not in source
    assert "requests" not in source
    assert "http" not in source
