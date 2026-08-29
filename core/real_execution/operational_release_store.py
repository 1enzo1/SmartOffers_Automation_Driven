"""Short-lived, server-owned operational releases for product execution.

The browser receives only an opaque validation-context reference.  Approval,
run identity, scenario, and runtime plan remain private until the application
claims the release exactly once immediately before it invokes the governed
controlled stack.
"""

from __future__ import annotations

import secrets
import threading
from datetime import datetime, timedelta
from typing import Any, Callable, Mapping


class OperationalReleaseStore:
    """Issue and atomically claim one-use releases from trusted server input."""

    def __init__(self, token_factory: Callable[[int], str] | None = None):
        self._token_factory = token_factory or secrets.token_urlsafe
        self._contexts: dict[str, dict[str, Any]] = {}
        self._releases: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def provision(
        self,
        *,
        test_id: str,
        trusted_release: Mapping[str, Any] | None,
        now: datetime,
        expires_at: datetime,
    ) -> bool:
        """Register an owner-provisioned release inside this process.

        Provisioning is intentionally not coupled to browser validation.  A
        process has no release by default; a trusted runtime owner must place
        one here before Validate can reserve it.
        """
        if not isinstance(trusted_release, Mapping):
            return False
        release_key = trusted_release.get("release_key")
        request_plan = trusted_release.get("request_plan")
        if (
            not isinstance(test_id, str)
            or not test_id
            or not isinstance(release_key, str)
            or not release_key
            or not isinstance(request_plan, Mapping)
            or not isinstance(now, datetime)
            or not isinstance(expires_at, datetime)
            or expires_at <= now
        ):
            return False

        with self._lock:
            if release_key in self._releases:
                return False
            self._releases[release_key] = {
                "test_id": test_id,
                "request_plan": dict(request_plan),
                "expires_at": expires_at,
                "state": "AVAILABLE",
            }
        return True

    def reserve(
        self, *, test_id: str, now: datetime, ttl: timedelta
    ) -> tuple[str | None, datetime | None]:
        """Match one exact pre-provisioned release to product validation.

        Reservation yields only an opaque reference.  It never constructs a
        request plan and it never accepts one from the caller.
        """
        if (
            not isinstance(test_id, str)
            or not test_id
            or not isinstance(now, datetime)
            or not isinstance(ttl, timedelta)
            or ttl.total_seconds() <= 0
        ):
            return None, None
        with self._lock:
            for release_key, release in self._releases.items():
                if release.get("test_id") != test_id or release.get("state") != "AVAILABLE":
                    continue
                if now >= release.get("expires_at"):
                    release["state"] = "EXPIRED"
                    continue
                reference = self._token_factory(24)
                context_expiry = min(now + ttl, release["expires_at"])
                release["state"] = "RESERVED"
                self._contexts[reference] = {
                    "test_id": test_id,
                    "release_key": release_key,
                    "expires_at": context_expiry,
                }
                return reference, context_expiry
        return None, None

    def claim(
        self, *, test_id: str, reference: str | None, now: datetime
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Consume a context and its release before delegating to the bridge."""
        if not isinstance(reference, str) or not reference:
            return None, "VALIDATION_CONTEXT_REQUIRED"
        if not isinstance(now, datetime):
            return None, "VALIDATION_CONTEXT_INVALID"
        with self._lock:
            context = self._contexts.pop(reference, None)
            if not isinstance(context, dict) or context.get("test_id") != test_id:
                return None, "VALIDATION_CONTEXT_INVALID"
            release = self._releases.get(context.get("release_key"))
            if not isinstance(release, dict) or release.get("state") != "RESERVED":
                return None, "VALIDATION_CONTEXT_INVALID"
            if now >= context.get("expires_at"):
                release["state"] = "EXPIRED"
                return None, "VALIDATION_CONTEXT_EXPIRED"
            release["state"] = "CLAIMED"
            return dict(release["request_plan"]), None
