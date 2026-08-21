import re
from pathlib import Path

from core.real_execution.manual_smoke_plan import (
    EXECUTION_APPROVED,
    EXECUTION_BLOCKED,
    build_manual_smoke_plan,
)


ROOT = Path(__file__).resolve().parents[1]
PLANNING_DOCS = (
    "mvp7-8-3b-execution-plan.md",
    "mvp7-8-3b-checklist.md",
    "mvp7-8-3b-evidence-template.md",
)


def _request(**overrides):
    request = {
        "environment": "qa4",
        "profile": "smartoffers_basic_smoke",
        "basic_smoke_ok": False,
        "destination_allowlisted": True,
        "redirect_detected": False,
        "execution_mode": "manual",
        "automated_execution": False,
        "requested_integrations": [],
        "attempts_per_checkpoint": 1,
        "retry_count": 0,
        "automatic_fallback": False,
        "credential_guessing": False,
        "alternative_password_attempt": False,
        "stop_on_first_unexpected_error": True,
        "oracle_access": "read_only",
        "api_payload_mode": "none",
        "connect_timeout_seconds": 3,
        "read_timeout_seconds": 5,
        "total_checkpoint_timeout_seconds": 10,
        "execution_approval": EXECUTION_APPROVED,
    }
    request.update(overrides)
    return request


def test_basic_plan_is_ready_for_review_but_execution_remains_blocked():
    result = build_manual_smoke_plan(_request())

    assert result["planning_status"] == "READY_FOR_ARCHITECT_REVIEW"
    assert result["execution_decision"] == EXECUTION_BLOCKED
    assert result["execution_approval_required"] == EXECUTION_APPROVED
    assert result["real_execution_implemented"] is False
    assert result["resources"] == ["smartoffers_api", "acm_custom_db", "oracle_client"]


def test_missing_execution_approval_blocks_the_planning_contract():
    result = build_manual_smoke_plan(_request(execution_approval=None))

    assert result["planning_status"] == "BLOCKED"
    assert "execution_approval_missing" in result["blocked_reasons"]
    assert result["execution_decision"] == EXECUTION_BLOCKED
    assert result["real_execution_implemented"] is False


def test_full_plan_requires_confirmed_basic_smoke():
    result = build_manual_smoke_plan(_request(profile="smartoffers_qa4_full_smoke"))

    assert result["planning_status"] == "BLOCKED"
    assert "basic_smoke_not_confirmed" in result["blocked_reasons"]
    assert result["execution_decision"] == EXECUTION_BLOCKED


def test_full_plan_is_ready_for_review_only_after_basic_smoke_confirmation():
    result = build_manual_smoke_plan(
        _request(profile="smartoffers_qa4_full_smoke", basic_smoke_ok=True)
    )

    assert result["planning_status"] == "READY_FOR_ARCHITECT_REVIEW"
    assert result["resources"] == [
        "smartoffers_api",
        "acm_custom_db",
        "acm_db",
        "bda_db",
        "oracle_client",
    ]
    assert result["execution_decision"] == EXECUTION_BLOCKED


def test_environment_retry_fallback_and_credentials_are_denied():
    result = build_manual_smoke_plan(
        _request(
            environment="production",
            retry_count=1,
            automatic_fallback=True,
            credential_guessing=True,
            alternative_password_attempt=True,
        )
    )

    assert result["planning_status"] == "BLOCKED"
    assert set(result["blocked_reasons"]) >= {
        "environment_not_qa4",
        "retry_must_equal_zero",
        "automatic_fallback_not_disabled",
        "credential_guessing_not_disabled",
        "alternative_password_not_disabled",
    }


def test_destination_outside_allowlist_and_redirect_are_denied():
    result = build_manual_smoke_plan(
        _request(
            environment="production",
            destination_allowlisted=False,
            redirect_detected=True,
        )
    )

    assert result["planning_status"] == "BLOCKED"
    assert set(result["blocked_reasons"]) >= {
        "environment_not_qa4",
        "destination_not_allowlisted",
        "redirect_not_allowed",
    }


def test_resource_allowlist_requires_exact_profile_resources():
    result = build_manual_smoke_plan(
        _request(resource_ids=["smartoffers_api", "unapproved_resource"])
    )

    assert result["planning_status"] == "BLOCKED"
    assert "resource_allowlist_violation" in result["blocked_reasons"]


def test_resource_allowlist_accepts_declared_basic_resources_only():
    result = build_manual_smoke_plan(
        _request(resource_ids=["smartoffers_api", "acm_custom_db", "oracle_client"])
    )

    assert result["planning_status"] == "READY_FOR_ARCHITECT_REVIEW"
    assert result["resources"] == ["smartoffers_api", "acm_custom_db", "oracle_client"]


def test_automated_execution_and_prohibited_integrations_are_denied():
    result = build_manual_smoke_plan(
        _request(
            execution_mode="automated",
            automated_execution=True,
            requested_integrations=["kafka", "jenkins", "ftm_engine"],
        )
    )

    assert result["planning_status"] == "BLOCKED"
    assert set(result["blocked_reasons"]) >= {
        "execution_mode_not_manual",
        "automated_execution_not_disabled",
        "integration_not_allowlisted",
    }


def test_timeouts_and_non_read_only_actions_are_denied():
    result = build_manual_smoke_plan(
        _request(
            connect_timeout_seconds=0,
            read_timeout_seconds=None,
            total_checkpoint_timeout_seconds=True,
            oracle_access="write",
            api_payload_mode="present",
        )
    )

    assert result["planning_status"] == "BLOCKED"
    assert set(result["blocked_reasons"]) >= {
        "invalid_connect_timeout_seconds",
        "invalid_read_timeout_seconds",
        "invalid_total_checkpoint_timeout_seconds",
        "oracle_access_not_read_only",
        "api_payload_not_disabled",
    }


def test_plan_never_records_operator_window_or_fake_sensitive_values():
    result = build_manual_smoke_plan(
        _request(
            operator="fake-operator-secret",
            execution_window="fake-window-secret",
            endpoint="fake-qa4-endpoint",
            password="fake-password",
        )
    )
    rendered = repr(result)

    for value in (
        "fake-operator-secret",
        "fake-window-secret",
        "fake-qa4-endpoint",
        "fake-password",
    ):
        assert value not in rendered
    assert result["evidence"]["status"] == EXECUTION_BLOCKED


def test_planner_has_no_network_or_process_dependencies():
    source = Path(build_manual_smoke_plan.__code__.co_filename).read_text(encoding="utf-8")

    for forbidden in (
        "import requests",
        "import urllib",
        "import socket",
        "import subprocess",
        ".send(",
        "popen(",
    ):
        assert forbidden not in source.lower()


def test_planning_documents_are_sanitized_ascii_templates():
    contents = []
    for name in PLANNING_DOCS:
        path = ROOT / "ai" / "real-execution" / name
        assert path.exists(), name
        contents.append(path.read_text(encoding="ascii"))

    rendered = "\n".join(contents)
    assert "<OPERATOR_REF>" in rendered
    assert "<EXECUTION_WINDOW_REF>" in rendered
    assert "http://" not in rendered.lower()
    assert "https://" not in rendered.lower()
    assert not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", rendered)
