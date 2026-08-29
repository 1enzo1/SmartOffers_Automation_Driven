from datetime import datetime, timedelta, timezone

from core.real_execution.operational_release_store import OperationalReleaseStore


def test_provision_rejects_non_mapping_with_boolean_false():
    store = OperationalReleaseStore()
    now = datetime(2026, 8, 29, tzinfo=timezone.utc)

    assert store.provision(
        test_id="create-customer-basic",
        trusted_release=None,
        now=now,
        expires_at=now + timedelta(minutes=5),
    ) is False


def _release(key="owner-release"):
    return {"release_key": key, "request_plan": {"scope": "trusted"}}


def test_reserve_requires_a_preprovisioned_exact_scope_release():
    store = OperationalReleaseStore(token_factory=lambda _size: "opaque-context")
    now = datetime(2026, 8, 29, tzinfo=timezone.utc)

    assert store.reserve(test_id="create", now=now, ttl=timedelta(minutes=5)) == (None, None)
    assert store.provision(
        test_id="other", trusted_release=_release(), now=now, expires_at=now + timedelta(minutes=10)
    ) is True
    assert store.reserve(test_id="create", now=now, ttl=timedelta(minutes=5)) == (None, None)


def test_expired_and_replayed_releases_cannot_be_claimed():
    store = OperationalReleaseStore(token_factory=lambda _size: "opaque-context")
    now = datetime(2026, 8, 29, tzinfo=timezone.utc)
    assert store.provision(
        test_id="create", trusted_release=_release(), now=now, expires_at=now + timedelta(minutes=2)
    ) is True
    reference, _ = store.reserve(test_id="create", now=now, ttl=timedelta(minutes=5))

    assert store.claim(test_id="create", reference=reference, now=now + timedelta(minutes=3)) == (
        None,
        "VALIDATION_CONTEXT_EXPIRED",
    )
    assert store.claim(test_id="create", reference=reference, now=now + timedelta(minutes=3)) == (
        None,
        "VALIDATION_CONTEXT_INVALID",
    )
