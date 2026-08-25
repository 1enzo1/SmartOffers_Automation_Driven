import hashlib
import importlib

import pytest


class FakeCursor:
    def __init__(self):
        self.description = [("PRODUCT_CODE",)]
        self._rows = [("safe-product-code",), None]
        self.executed = []
        self.closed = False

    def execute(self, query):
        self.executed.append(query)

    def fetchone(self):
        return self._rows.pop(0)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.call_timeout = None
        self.rollback_calls = 0
        self.close_calls = 0

    def cursor(self):
        return self.cursor_instance

    def rollback(self):
        self.rollback_calls += 1

    def close(self):
        self.close_calls += 1


class FakeDriver:
    def __init__(self):
        self.connection = FakeConnection()
        self.init_calls = []
        self.connect_calls = []

    def init_oracle_client(self, lib_dir):
        self.init_calls.append(lib_dir)

    def connect(self, **kwargs):
        self.connect_calls.append(kwargs)
        return self.connection


def _runtime():
    dsn = "safe-bda-dsn"
    smoke_sql = "SELECT technical_check FROM safe_dual"
    return {
        "SMARTOFFERS_QA4_BDA_DB_DSN": dsn,
        "SMARTOFFERS_QA4_BDA_DB_USER": "safe-bda-user",
        "SMARTOFFERS_QA4_BDA_DB_PASSWORD": "safe-bda-password",
        "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR": "safe-client-dir",
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL": smoke_sql,
        "SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256": hashlib.sha256(
            smoke_sql.encode("utf-8")
        ).hexdigest(),
        "SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT": hashlib.sha256(
            dsn.encode("utf-8")
        ).hexdigest(),
    }


def test_offer_discovery_returns_sanitized_single_row_and_delivers_code_only_to_local_sink():
    try:
        module = importlib.import_module("core.real_execution.qa4_bda_offer_discovery")
    except ModuleNotFoundError:
        pytest.fail("QA4 BDA offer discovery operation is missing")

    captured = []
    driver = FakeDriver()
    result = module.run_qa4_bda_offer_discovery(
        environ=_runtime(),
        driver=driver,
        offer_sink=captured.append,
        authorization={
            "operation": "QA4_BDA_OFFER_DISCOVERY",
            "read_only_discovery_authorized": True,
        },
    )

    assert result["status"] == "QA4_BDA_OFFER_DISCOVERY_OK"
    assert result["found_valid_offer"] is True
    assert result["sensitive_values_logged"] is False
    assert "safe-product-code" not in repr(result)
    assert captured == ["safe-product-code"]
    assert len(driver.connect_calls) == 1
    assert len(driver.connection.cursor_instance.executed) == 1
    assert "bop_cfg_step_down_map" in driver.connection.cursor_instance.executed[0].lower()
    assert "product_code" in driver.connection.cursor_instance.executed[0].lower()
    assert driver.connection.call_timeout == 5000
    assert driver.connection.rollback_calls == 1
    assert driver.connection.close_calls == 1


def test_offer_discovery_blocks_before_connect_without_explicit_authorization():
    module = importlib.import_module("core.real_execution.qa4_bda_offer_discovery")
    driver = FakeDriver()

    result = module.run_qa4_bda_offer_discovery(
        environ=_runtime(),
        driver=driver,
    )

    assert result["status"] == "QA4_BDA_OFFER_DISCOVERY_BLOCKED"
    assert result["sanitized_error_category"] == "READ_ONLY_DISCOVERY_AUTHORIZATION_REQUIRED"
    assert driver.init_calls == []
    assert driver.connect_calls == []
