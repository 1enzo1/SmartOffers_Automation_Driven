import uuid
from pathlib import Path

import pytest

import app as app_module


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
