import copy

from core.risk import classify_adapter_risk


def test_mode_real_blocks():
    result = classify_adapter_risk({"mode": "real"})

    assert result["risk_status"] == "blocked"
    assert result["risk_level"] == "critical"
    assert result["allowed_mode"] == "none"
    assert "mode_real" in result["blocked_reasons"]


def test_safe_for_real_execution_true_blocks():
    result = classify_adapter_risk({"safe_for_real_execution": True})

    assert result["risk_status"] == "blocked"
    assert result["risk_level"] == "critical"
    assert result["allowed_mode"] == "none"
    assert "safe_for_real_execution_true" in result["blocked_reasons"]


def test_real_execution_true_string_blocks():
    result = classify_adapter_risk({"notes": '"real_execution": true'})

    assert result["risk_status"] == "blocked"
    assert "real_execution_true" in result["blocked_reasons"]


def test_host_ip_token_secret_and_credential_block():
    cases = [
        ({"target": "host=qa4.example.local"}, "real_host"),
        ({"target": "10.20.30.40"}, "real_ip"),
        ({"header": "token=abc"}, "token"),
        ({"header": "secret=value"}, "secret"),
        ({"header": "credential=value"}, "credential"),
    ]

    for work_item, reason in cases:
        result = classify_adapter_risk(work_item)

        assert result["risk_status"] == "blocked"
        assert reason in result["blocked_reasons"]


def test_kafka_real_blocks():
    result = classify_adapter_risk({"operation": "Kafka real lookup"})

    assert result["risk_status"] == "blocked"
    assert "kafka_real" in result["blocked_reasons"]


def test_conceptual_kafka_trace_requires_future_controlled():
    result = classify_adapter_risk({"evidence_layer": "kafka_trace"})

    assert result["risk_status"] == "future_controlled_required"
    assert result["risk_level"] == "high"
    assert result["allowed_mode"] == "none"
    assert "kafka_trace_future_controlled" in result["blocked_reasons"]
    assert "keep-action-read-only" in result["required_guardrails"]
    assert "execute" not in result["safe_next_step"].lower()
    assert "real" not in result["safe_next_step"].lower()


def test_request_plan_mock_only_sanitized_returns_mock_allowed():
    result = classify_adapter_risk(
        {
            "request_plan": {
                "api_id": "post-evento-de-recarga-6954ef3458",
                "planning_mode": "mock_only",
                "host_placeholder": "<QA4_HOST>",
                "safe_for_real_execution": False,
            }
        }
    )

    assert result["risk_status"] == "mock_allowed"
    assert result["risk_level"] == "low"
    assert result["allowed_mode"] == "mock"
    assert "request_plan_mock_only" in result["blocked_reasons"]


def test_sanitized_catalog_item_returns_read_only_allowed():
    result = classify_adapter_risk(
        {
            "item_type": "api_catalog_item",
            "api_id": "post-evento-de-recarga-6954ef3458",
            "execution_status": "blocked",
            "safe_for_real_execution": False,
        }
    )

    assert result["risk_status"] == "read_only_allowed"
    assert result["risk_level"] == "medium"
    assert result["allowed_mode"] == "read-only"
    assert "catalog-sanitized" not in result["blocked_reasons"]
    assert "review-sanitized-input-only" in result["required_guardrails"]


def test_scenario_intelligence_blocked_result_returns_blocked():
    result = classify_adapter_risk(
        {
            "domain": "smartoffers",
            "overall_status": "blocked",
            "risks": [{"status": "blocked", "code": "blocked_real_execution_signal"}],
        }
    )

    assert result["risk_status"] == "blocked"
    assert "upstream_blocked_status" in result["blocked_reasons"]


def test_blocked_precedence_over_future_read_only_and_mock():
    result = classify_adapter_risk(
        {
            "mode": "real",
            "evidence_layer": "kafka_trace",
            "planning_mode": "mock_only",
            "query": "read-only evidence",
        }
    )

    assert result["risk_status"] == "blocked"
    assert result["risk_level"] == "critical"
    assert result["allowed_mode"] == "none"
    assert "mode_real" in result["blocked_reasons"]
    assert "kafka_trace_future_controlled" in result["blocked_reasons"]


def test_function_is_deterministic_and_does_not_mutate_input():
    work_item = {
        "planning_mode": "mock_only",
        "nested": {"safe_for_real_execution": False},
        "items": ["request_plan", "request_plan"],
    }
    original = copy.deepcopy(work_item)

    first = classify_adapter_risk(work_item)
    second = classify_adapter_risk(work_item)

    assert work_item == original
    assert first == second


def test_returned_lists_are_ordered_and_deduplicated():
    result = classify_adapter_risk(
        {
            "mode": "real",
            "again": "mode=real",
            "planning_mode": "mock_only",
            "evidence_layer": "kafka_trace",
            "request_plan": "request_plan",
        }
    )

    for key in ("blocked_reasons", "required_guardrails", "related_supervisors"):
        values = result[key]
        assert values == list(dict.fromkeys(values))

    assert result["related_supervisors"][:2] == [
        "adapter-supervisor",
        "safety-supervisor",
    ]


def test_future_controlled_required_uses_none_allowed_mode():
    result = classify_adapter_risk({"status": "future-controlled"})

    assert result["risk_status"] == "future_controlled_required"
    assert result["allowed_mode"] == "none"
    assert result["risk_level"] == "high"
