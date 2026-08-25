import hashlib
import inspect

import pytest

from core.real_execution import bda_local_runtime_preflight
from core.real_execution.bda_local_runtime_preflight import (
    BDA_CHECKPOINT,
    BDA_ENVIRONMENT,
    BDA_PROFILE,
    BDA_REQUIRED_REFS,
    BDA_RESOURCE_ID,
    BDA_RUNTIME_BLOCKED,
    BDA_RUNTIME_READY,
    preflight_bda_local_runtime,
)


def _sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _request(**overrides):
    request = {
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
    }
    request.update(overrides)
    return request


def _fake_runtime():
    sql = "SELECT fake_technical_check FROM fake_dual"
    dsn = "fake-bda-dsn"
    return {
        "SMARTOFFERS_QA4_BDA_DB_DSN": dsn,
        "SMARTOFFERS_QA4_BDA_DB_USER": "fake-bda-user",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD": "fake-bda-password",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-oracle-client-dir",
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL": sql,
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256": _sha256(sql),
        "SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT": _sha256(dsn),
    }


def test_bda_preflight_returns_ready_only_for_complete_matching_runtime():
    result = preflight_bda_local_runtime(_request(), _fake_runtime())

    assert result == {
        "status": BDA_RUNTIME_READY,
        "checkpoint": BDA_CHECKPOINT,
        "environment": BDA_ENVIRONMENT,
        "profile": BDA_PROFILE,
        "resource_id": BDA_RESOURCE_ID,
        "allowlist_validation": "MATCH",
        "refs_validation": "READY",
        "sql_hash_validation": "MATCH",
        "fingerprint_validation": "MATCH",
        "checked_refs": list(BDA_REQUIRED_REFS),
        "missing_refs": [],
        "connection_allowed": False,
        "sql_execution_allowed": False,
    }


def test_bda_preflight_enables_only_the_explicit_offer_discovery_operation():
    result = preflight_bda_local_runtime(
        _request(
            operation="QA4_BDA_OFFER_DISCOVERY",
            read_only_discovery_authorized=True,
        ),
        _fake_runtime(),
    )

    assert result["status"] == BDA_RUNTIME_READY
    assert result["connection_allowed"] is True
    assert result["sql_execution_allowed"] is True


@pytest.mark.parametrize("missing_ref", BDA_REQUIRED_REFS)
def test_bda_preflight_blocks_each_missing_required_ref(missing_ref):
    runtime = _fake_runtime()
    runtime.pop(missing_ref)

    result = preflight_bda_local_runtime(_request(), runtime)

    assert result["status"] == BDA_RUNTIME_BLOCKED
    assert result["refs_validation"] == "BLOCKED"
    assert result["missing_refs"] == [missing_ref]


def test_bda_preflight_blocks_sql_hash_mismatch():
    runtime = _fake_runtime()
    runtime["SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256"] = "different-fake-hash"

    result = preflight_bda_local_runtime(_request(), runtime)

    assert result["status"] == BDA_RUNTIME_BLOCKED
    assert result["sql_hash_validation"] == "DENIED"
    assert result["fingerprint_validation"] == "MATCH"


def test_bda_preflight_blocks_destination_fingerprint_mismatch():
    runtime = _fake_runtime()
    runtime["SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT"] = "different-fake-fingerprint"

    result = preflight_bda_local_runtime(_request(), runtime)

    assert result["status"] == BDA_RUNTIME_BLOCKED
    assert result["sql_hash_validation"] == "MATCH"
    assert result["fingerprint_validation"] == "DENIED"


@pytest.mark.parametrize(
    "overrides",
    [
        {"checkpoint": "ORACLE_ACM_TECHNICAL_READ_ONLY_01"},
        {"environment": "qa3"},
        {"profile": "smartoffers_basic_smoke"},
        {"resource_id": "acm_db"},
    ],
)
def test_bda_preflight_blocks_any_allowlist_mismatch(overrides):
    result = preflight_bda_local_runtime(_request(**overrides), _fake_runtime())

    assert result["status"] == BDA_RUNTIME_BLOCKED
    assert result["allowlist_validation"] == "DENIED"


@pytest.mark.parametrize(
    "foreign_prefix",
    ["SMARTOFFERS_QA4_ACM_", "SMARTOFFERS_QA4_ACM_CUSTOM_"],
)
def test_bda_preflight_explicitly_rejects_acm_and_acm_custom_refs(foreign_prefix):
    runtime = {
        f"{foreign_prefix}DB_DSN": "fake-foreign-dsn",
        f"{foreign_prefix}DB_USER": "fake-foreign-user",
        f"{foreign_prefix}DB_PASSWORD": "fake-foreign-password",
        f"{foreign_prefix}SMOKE_SQL": "SELECT fake_value FROM fake_dual",
        f"{foreign_prefix}SMOKE_SQL_SHA256": "fake-foreign-hash",
        f"{foreign_prefix}DESTINATION_FINGERPRINT": "fake-foreign-fingerprint",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "fake-oracle-client-dir",
    }

    result = preflight_bda_local_runtime(_request(), runtime)

    assert result["status"] == BDA_RUNTIME_BLOCKED
    assert result["refs_validation"] == "BLOCKED"
    assert all("BDA" in ref or ref == "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR" for ref in result["checked_refs"])


def test_bda_preflight_output_never_contains_fake_runtime_values():
    runtime = _fake_runtime()
    rendered = repr(preflight_bda_local_runtime(_request(), runtime))

    assert all(value not in rendered for value in runtime.values())


def test_bda_preflight_module_has_no_oracle_or_network_dependency():
    source = inspect.getsource(bda_local_runtime_preflight)

    for forbidden in ("oracledb", "socket", "subprocess", "requests", "http"):
        assert forbidden not in source
