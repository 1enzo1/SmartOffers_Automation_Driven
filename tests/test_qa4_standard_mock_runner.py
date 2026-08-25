from core.real_execution import run_standard_qa4_mock


EVALUATED_AT = "2026-08-22T12:10:00+00:00"


def _context():
    return {
        "orchestration_id": "alpha-run-ref",
        "operational_window_ref": "qa4-window-ref",
        "window_started_at": "2026-08-22T12:00:00+00:00",
        "window_expires_at": "2026-08-22T12:15:00+00:00",
        "environment": "qa4",
        "workflow_profile": "smartoffers_qa4_full_smoke",
    }


def _db_result(checkpoint, resource_id, *, profile, status):
    return {
        "execution_id": f"{resource_id}-execution", "timestamp": "2026-08-22T12:05:00+00:00",
        "environment": "qa4", "profile": profile, "checkpoint": checkpoint,
        "resource_id": resource_id, "status": status, "attempts_used": 1, "retry_count": 0,
        "sensitive_values_logged": False, "sanitized_error_category": "NONE",
        "stop_reason": "CHECKPOINT_COMPLETED", "environment_allowlist": "MATCH",
        "resource_allowlist": "MATCH", "destination_allowlist": "MATCH",
        "query_hash_validation": "MATCH", "read_only_validation": "PASS",
        "result_shape_validation": "MATCH", "fingerprint_validation": "MATCH",
        "preflight_validation": "MATCH",
    }


def _api_result():
    return {
        "execution_id": "api-execution", "timestamp": "2026-08-22T12:06:00+00:00",
        "environment": "qa4", "profile": "smartoffers_qa4_full_smoke",
        "checkpoint": "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01", "resource_id": "smartoffers_api",
        "status": "SMARTOFFERS_API_QA4_CHECKPOINT_OK", "attempts_used": 1, "retry_count": 0,
        "sensitive_values_logged": False, "sanitized_error_category": "NONE",
        "stop_reason": "CHECKPOINT_COMPLETED", "allowlist_validation": "MATCH",
        "preflight_validation": "MATCH", "path_validation": "MATCH", "path_hash_validation": "MATCH",
        "fingerprint_validation": "MATCH", "db_gate_bundle_validation": "MATCH",
        "response_body_logged": False, "response_headers_logged": False,
    }


def test_standard_runner_normalizes_db_in_order_then_calls_api_and_consolidates():
    calls = []

    def executor(name, result):
        def run(context):
            calls.append(name)
            assert context == _context()
            return result
        return run

    def api_client(context, db_gate_bundle):
        calls.append("SMARTOFFERS_API")
        assert context == _context()
        assert db_gate_bundle["status"] == "DB_CHECKPOINT_GATES_READY"
        return _api_result()

    result = run_standard_qa4_mock(
        _context(), evaluated_at=EVALUATED_AT,
        acm_custom_executor=executor("ACM_CUSTOM", _db_result("ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01", "acm_custom_db", profile="smartoffers_basic_smoke", status="CONNECT_AND_READ_OK")),
        acm_executor=executor("ACM", _db_result("ORACLE_ACM_TECHNICAL_READ_ONLY_01", "acm_db", profile="smartoffers_qa4_full_smoke", status="CONNECT_AND_READ_OK")),
        bda_executor=executor("BDA", _db_result("ORACLE_BDA_TECHNICAL_READ_ONLY_01", "bda_db", profile="smartoffers_qa4_full_smoke", status="BDA_DB_CHECKPOINT_OK")),
        api_client=api_client,
    )

    assert calls == ["ACM_CUSTOM", "ACM", "BDA", "SMARTOFFERS_API"]
    assert [record["component"] for record in result["records"]] == ["ACM_CUSTOM_DB", "ACM_DB", "BDA_DB", "SMARTOFFERS_API"]
    assert result["full"]["status"] == "FULL_SMOKE_OK"
    assert result["authoritative"] is False
    assert result["operational_readiness"] is False


def test_standard_runner_never_passes_unsanitized_context_to_collaborators():
    context = _context() | {"db_dsn": "must-not-leave-runner"}
    seen_contexts = []

    def db_executor(result):
        def run(received_context):
            seen_contexts.append(received_context)
            return result
        return run

    def api_client(received_context, db_gate_bundle):
        seen_contexts.append(received_context)
        return _api_result()

    run_standard_qa4_mock(
        context, evaluated_at=EVALUATED_AT,
        acm_custom_executor=db_executor(_db_result("ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01", "acm_custom_db", profile="smartoffers_basic_smoke", status="CONNECT_AND_READ_OK")),
        acm_executor=db_executor(_db_result("ORACLE_ACM_TECHNICAL_READ_ONLY_01", "acm_db", profile="smartoffers_qa4_full_smoke", status="CONNECT_AND_READ_OK")),
        bda_executor=db_executor(_db_result("ORACLE_BDA_TECHNICAL_READ_ONLY_01", "bda_db", profile="smartoffers_qa4_full_smoke", status="BDA_DB_CHECKPOINT_OK")),
        api_client=api_client,
    )

    assert len(seen_contexts) == 4
    assert all("db_dsn" not in item for item in seen_contexts)
    assert all(item == _context() for item in seen_contexts)


def test_standard_runner_blocks_api_for_raw_legacy_db_evidence():
    api_calls = []

    def api_client(*args):
        api_calls.append(args)
        return _api_result()

    result = run_standard_qa4_mock(
        _context(), evaluated_at=EVALUATED_AT,
        acm_custom_executor=lambda context: {"status": "passed"},
        acm_executor=lambda context: _db_result("ORACLE_ACM_TECHNICAL_READ_ONLY_01", "acm_db", profile="smartoffers_qa4_full_smoke", status="CONNECT_AND_READ_OK"),
        bda_executor=lambda context: _db_result("ORACLE_BDA_TECHNICAL_READ_ONLY_01", "bda_db", profile="smartoffers_qa4_full_smoke", status="BDA_DB_CHECKPOINT_OK"),
        api_client=api_client,
    )

    assert api_calls == []
    assert result["records"][0]["evidence_status"] == "REJECTED"
    assert result["basic"]["status"] == "BASIC_SMOKE_BLOCKED"
    assert result["authoritative"] is False
    assert result["operational_readiness"] is False


def test_standard_runner_blocks_variant_context_before_api_invocation():
    api_calls = []
    context = _context() | {"workflow_profile": "smartoffers_variant_smoke"}

    result = run_standard_qa4_mock(
        context, evaluated_at=EVALUATED_AT,
        acm_custom_executor=lambda context: _db_result("ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01", "acm_custom_db", profile="smartoffers_basic_smoke", status="CONNECT_AND_READ_OK"),
        acm_executor=lambda context: _db_result("ORACLE_ACM_TECHNICAL_READ_ONLY_01", "acm_db", profile="smartoffers_qa4_full_smoke", status="CONNECT_AND_READ_OK"),
        bda_executor=lambda context: _db_result("ORACLE_BDA_TECHNICAL_READ_ONLY_01", "bda_db", profile="smartoffers_qa4_full_smoke", status="BDA_DB_CHECKPOINT_OK"),
        api_client=lambda *args: api_calls.append(args),
    )

    assert api_calls == []
    assert result["full"]["status"] == "FULL_SMOKE_BLOCKED"
