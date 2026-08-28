import hashlib
import importlib
import threading

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
            "bda_operation": "OFFER_DISCOVERY",
            "read_only_discovery_authorized": True,
            "authorization_verified": True,
            "destination_attestation_ready": True,
            "offers_operation": "CREATE_OFFERS_CUSTOMER",
            "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
            "access_mode": "READ_ONLY",
            "attempts_used": 0,
        },
    )

    assert result["status"] == "QA4_BDA_OFFER_DISCOVERY_OK"
    assert result["found_valid_offer"] is True
    assert result["offers_attempts_used"] == 0
    assert result["offers_attempts_available"] == 1
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


def test_offer_discovery_blocks_before_connect_when_scoped_attestation_is_missing():
    module = importlib.import_module("core.real_execution.qa4_bda_offer_discovery")
    driver = FakeDriver()

    result = module.run_qa4_bda_offer_discovery(
        environ=_runtime(),
        driver=driver,
        authorization={
            "operation": "QA4_BDA_OFFER_DISCOVERY",
            "bda_operation": "OFFER_DISCOVERY",
            "read_only_discovery_authorized": True,
            "authorization_verified": True,
            "destination_attestation_ready": False,
            "offers_operation": "CREATE_OFFERS_CUSTOMER",
            "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
            "access_mode": "READ_ONLY",
            "attempts_used": 0,
        },
    )

    assert result["status"] == "QA4_BDA_OFFER_DISCOVERY_BLOCKED"
    assert result["sanitized_error_category"] == "READ_ONLY_DISCOVERY_AUTHORIZATION_REQUIRED"
    assert driver.init_calls == []
    assert driver.connect_calls == []


@pytest.mark.parametrize(
    "alternate_query",
    [
        "SELECT different_read_only_value FROM fake_dual",
        "UPDATE fake_table SET fake_value = 'blocked'",
    ],
)
def test_offer_discovery_blocks_an_unapproved_query_hash_before_driver_initialization(
    monkeypatch, alternate_query
):
    module = importlib.import_module("core.real_execution.qa4_bda_offer_discovery")
    driver = FakeDriver()
    monkeypatch.setattr(module, "_QUERY", alternate_query)

    result = module.run_qa4_bda_offer_discovery(
        environ=_runtime(),
        driver=driver,
        authorization={
            "operation": "QA4_BDA_OFFER_DISCOVERY",
            "bda_operation": "OFFER_DISCOVERY",
            "read_only_discovery_authorized": True,
            "authorization_verified": True,
            "destination_attestation_ready": True,
            "offers_operation": "CREATE_OFFERS_CUSTOMER",
            "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
            "access_mode": "READ_ONLY",
            "attempts_used": 0,
        },
    )

    assert result["status"] == "QA4_BDA_OFFER_DISCOVERY_BLOCKED"
    assert result["sanitized_error_category"] == "QUERY_HASH_MISMATCH"
    assert result["offers_attempts_used"] == 0
    assert driver.init_calls == []
    assert driver.connect_calls == []


def test_offer_discovery_requires_injected_driver_and_uses_its_separate_budget_once():
    module = importlib.import_module("core.real_execution.qa4_bda_offer_discovery")

    class Ledger:
        def __init__(self):
            self.scopes = []

        def consume(self, scope):
            self.scopes.append(scope)
            return len(self.scopes) == 1

    authorization = {
        "operation": "QA4_BDA_OFFER_DISCOVERY",
        "bda_operation": "OFFER_DISCOVERY",
        "read_only_discovery_authorized": True,
        "authorization_verified": True,
        "destination_attestation_ready": True,
        "offers_operation": "CREATE_OFFERS_CUSTOMER",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "access_mode": "READ_ONLY",
        "attempts_used": 0,
    }
    driver = FakeDriver()
    ledger = Ledger()

    first = module.run_qa4_bda_offer_discovery(
        environ=_runtime(), driver=driver, authorization=authorization, attempt_ledger=ledger
    )
    second = module.run_qa4_bda_offer_discovery(
        environ=_runtime(), driver=FakeDriver(), authorization=authorization, attempt_ledger=ledger
    )
    missing_driver = module.run_qa4_bda_offer_discovery(
        environ=_runtime(), authorization=authorization
    )

    assert first["status"] == "QA4_BDA_OFFER_DISCOVERY_OK"
    assert second["status"] == "QA4_BDA_OFFER_DISCOVERY_BLOCKED"
    assert second["sanitized_error_category"] == "BDA_DISCOVERY_BUDGET_EXHAUSTED"
    assert missing_driver["status"] == "QA4_BDA_OFFER_DISCOVERY_BLOCKED"
    assert missing_driver["sanitized_error_category"] == "EXPLICIT_ORACLE_DRIVER_REQUIRED"
    assert ledger.scopes == ["QA4_BDA_OFFER_DISCOVERY", "QA4_BDA_OFFER_DISCOVERY"]


def test_shared_discovery_ledger_blocks_repeat_before_driver_factory_is_called():
    module = importlib.import_module("core.real_execution.qa4_bda_offer_discovery")
    authorization = {
        "operation": "QA4_BDA_OFFER_DISCOVERY",
        "bda_operation": "OFFER_DISCOVERY",
        "read_only_discovery_authorized": True,
        "authorization_verified": True,
        "destination_attestation_ready": True,
        "offers_operation": "CREATE_OFFERS_CUSTOMER",
        "scenario_id": "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "access_mode": "READ_ONLY",
        "attempts_used": 0,
    }
    ledger = module.BdaDiscoveryAttemptLedger()
    created = []

    def driver_factory():
        driver = FakeDriver()
        created.append(driver)
        return driver

    first = module.run_qa4_bda_offer_discovery(
        environ=_runtime(), driver_factory=driver_factory,
        authorization=authorization, attempt_ledger=ledger,
    )
    second = module.run_qa4_bda_offer_discovery(
        environ=_runtime(), driver_factory=driver_factory,
        authorization=authorization, attempt_ledger=ledger,
    )

    assert first["status"] == "QA4_BDA_OFFER_DISCOVERY_OK"
    assert second["sanitized_error_category"] == "BDA_DISCOVERY_BUDGET_EXHAUSTED"
    assert len(created) == 1
    assert len(created[0].connect_calls) == 1


def test_discovery_ledger_allows_only_one_concurrent_reservation():
    module = importlib.import_module("core.real_execution.qa4_bda_offer_discovery")

    class RacingLedger(module.BdaDiscoveryAttemptLedger):
        def __init__(self):
            super().__init__()
            self._barrier = threading.Barrier(2)

        def __getattribute__(self, name):
            current = object.__getattribute__(self, name)
            if name == "_consumed" and not current:
                try:
                    object.__getattribute__(self, "_barrier").wait(timeout=0.2)
                except threading.BrokenBarrierError:
                    pass
            return current

    ledger = RacingLedger()
    results = []
    workers = [
        threading.Thread(target=lambda: results.append(ledger.consume("QA4_BDA_OFFER_DISCOVERY")))
        for _ in range(2)
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    assert results.count(True) == 1
    assert results.count(False) == 1
