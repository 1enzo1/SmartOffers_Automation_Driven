import json
import os
import importlib
from datetime import datetime, timedelta

from flask import Flask, Response, jsonify, render_template, request, send_file

from core.api_catalog import get_api_catalog_entry, list_api_catalog_entries
from core.exporters import (
    ExportFormatError,
    ExportSourceNotFoundError,
    export_dry_run_artifact,
    export_scenario_artifact,
    get_export_mimetype,
    load_dry_run_report_by_id,
)
from core.generation import (
    ScenarioValidationError,
    generate_scenario,
    get_questions,
    list_scenarios,
    load_scenario,
    save_scenario,
)
from core.execution.service import (
    AdapterRunModeError,
    adapters_healthcheck,
    list_adapters,
    run_adapter_scenario,
)
from core.legacy_execution import (
    SCRIPTS,
    list_legacy_tests,
    load_legacy_test,
    open_legacy_base_folder,
    stream_legacy_execution,
)
from core.real_execution.environments import list_sanitized_qa_environments
from core.real_execution.runtime_profiles import list_sanitized_runtime_profiles
from core.real_execution import run_standard_qa4_application_mock
from core.real_execution.qa4_real_controlled_bridge import (
    SYNTHETIC_OFFERS_SCENARIO,
    run_atomic_qa4_bda_offer_discovery_and_offers_create,
)
from core.real_execution.qa4_bda_offer_discovery import BdaDiscoveryAttemptLedger
from core.real_execution.operational_release_store import OperationalReleaseStore
from core.real_execution.sanitized_evidence import (
    load_sanitized_real_run_evidence,
    list_sanitized_real_run_evidence,
    persist_sanitized_real_run_evidence,
)
from core.product_test_catalog import (
    get_product_test,
    get_product_test_runtime,
    list_product_tests,
    validate_contract_plan,
)
from core.simulation import run_dry_run, save_dry_run_report
from core.templates import get_template, list_template_categories, list_templates


app = Flask(__name__)


_STANDARD_QA4_PROFILE = "smartoffers_qa4_full_smoke"
_STANDARD_QA4_CONTEXT_FIELDS = (
    "orchestration_id",
    "operational_window_ref",
    "window_started_at",
    "window_expires_at",
)
_APPLICATION_CONFIRMATION = "CONFIRM_QA4_CREATE_OFFERS_CUSTOMER"
_OFFERS_API_ID = "post-vivo-next-habilitacao-de-cliente-ade0841563"
_ALPHA_CONTROLLED_CONTRACT_REF = "SMARTOFFERS_ALPHA_QA4_CONTROLLED_CONTRACT"
_ALPHA_AUTHORIZATION = "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN"
_ATOMIC_BDA_AUTHORIZATION = "ONE_ATOMIC_QA4_BDA_DISCOVERY_AND_OFFERS_CREATE_RUN"
_RUN_02_ID = "ALPHA_REAL_RUN_02"
_RUN_02_AUTHORIZATION = "ONE_QA4_REPEATABILITY_SMOKE_RUN_02"
_RUN_03A_ID = "ALPHA_REAL_RUN_03A"
_RUN_03A_AUTHORIZATION = "ONE_QA4_CREATE_CUSTOMER_WITH_OFFER_RUN_03A"
_RUN_02_BDA_AUTHORIZATION = "ONE_QA4_REPEATABILITY_SMOKE_RUN_02"
_DEFAULT_BDA_DISCOVERY_LEDGER = BdaDiscoveryAttemptLedger()
_PRODUCT_OPERATIONAL_RELEASES = OperationalReleaseStore()
_PRODUCT_VALIDATION_CONTEXT_TTL = timedelta(minutes=5)


class _RuntimeEnvironment(dict):
    """Keep runtime-only configuration out of accidental diagnostic rendering."""

    def __repr__(self):
        return "<runtime-environment>"


class _RuntimeSecrets(dict):
    """Keep endpoint material internal when a local provider is inspected."""

    def __repr__(self):
        return "<runtime-secrets>"


def _run_authorization(context):
    context_data = context if isinstance(context, dict) else {}
    if context_data.get("run_id") == _RUN_02_ID:
        return _RUN_02_AUTHORIZATION
    if context_data.get("run_id") == _RUN_03A_ID:
        return _RUN_03A_AUTHORIZATION
    return _ALPHA_AUTHORIZATION


def _run_bda_authorization(context):
    authorization = _run_authorization(context)
    if authorization == _RUN_02_AUTHORIZATION:
        return _RUN_02_BDA_AUTHORIZATION
    if authorization == _RUN_03A_AUTHORIZATION:
        return _RUN_03A_AUTHORIZATION
    return _ATOMIC_BDA_AUTHORIZATION


def _qa4_owner_execution_inputs(context):
    """Compose only an attested Alpha contract; never resolve transport inputs here."""

    context_data = context if isinstance(context, dict) else {}
    if not _is_exact_alpha_controlled_context(context_data):
        return {}

    contract = _qa4_controlled_contract_from_environ()
    if not _is_exact_alpha_controlled_contract(contract, _run_authorization(context_data)):
        return {}

    from core.real_execution.qa4_offers_customer_adapter import (
        _DEFAULT_ATTEMPT_LEDGER,
        prepare_one_synthetic_qa4_offers_customer_create,
    )
    from core.real_execution.api_health_local_runtime_preflight import (
        SCOPED_OFFERS_DESTINATION_ATTESTATION_READY,
        preflight_scoped_qa4_offers_destination_attestation,
    )

    preflight = prepare_one_synthetic_qa4_offers_customer_create(
        context_data,
        environ=os.environ,
        approval=contract["approval"],
        defer_offer_validation=True,
    )
    destination_preflight = preflight_scoped_qa4_offers_destination_attestation(
        {
            "operation": "CREATE_OFFERS_CUSTOMER",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "environment": "QA4",
            "api_id": _OFFERS_API_ID,
        },
        environ=os.environ,
    )
    if (
        preflight.get("preflight_status") != "READY"
        or destination_preflight.get("status")
        != SCOPED_OFFERS_DESTINATION_ATTESTATION_READY
    ):
        return {"ledger": _DEFAULT_ATTEMPT_LEDGER}

    return {
        "ledger": _DEFAULT_ATTEMPT_LEDGER,
        "environ": _RuntimeEnvironment(os.environ),
        "runtime_factory": lambda: _qa4_lazy_runtime_inputs(
            contract, _DEFAULT_ATTEMPT_LEDGER
        ),
        "static_preflight": {
            "status": "READY",
            "test_offer_ready": False,
            "offers_attempts_used": 0,
        },
    }


def _qa4_lazy_runtime_inputs(contract, ledger):
    """Resolve transport collaborators only after the atomic BDA phase succeeds."""
    from core.real_execution.real_http_client import RealHttpClient

    return {
        "runtime_refs": dict(contract["runtime_refs"]),
        "runtime_secrets": _RuntimeSecrets(
            {
                "endpoint": os.environ.get("SMARTOFFERS_QA4_API_URL"),
                "headers": {"content-type": "application/json"},
                "correlation_id": contract["runtime_refs"]["CORRELATION_ID"],
                "timeout_seconds": 5,
            }
        ),
        "policy": dict(contract["policy"]),
        "approval": dict(contract["approval"]),
        "owner_opt_in": dict(contract["owner_opt_in"]),
        "ledger": ledger,
        "client_factory": RealHttpClient,
    }


def _atomic_static_preflight_ready(context, contract):
    """Verify local, non-transport gates before constructing the BDA boundary."""
    if not _is_exact_alpha_controlled_contract(contract, _run_authorization(context)):
        return False
    from core.real_execution.api_health_local_runtime_preflight import (
        SCOPED_OFFERS_DESTINATION_ATTESTATION_READY,
        preflight_scoped_qa4_offers_destination_attestation,
    )

    result = preflight_scoped_qa4_offers_destination_attestation(
        {
            "operation": "CREATE_OFFERS_CUSTOMER",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "environment": "QA4",
            "api_id": _OFFERS_API_ID,
        },
        environ=os.environ,
    )
    return result.get("status") == SCOPED_OFFERS_DESTINATION_ATTESTATION_READY


def _governed_bda_driver():
    """Load the Oracle driver only for the explicit atomic composition boundary."""
    try:
        return importlib.import_module("oracledb")
    except ImportError:
        return None


def _qa4_controlled_contract_from_environ():
    """Read one local, non-secret control document without resolving endpoints."""

    raw_contract = os.environ.get(_ALPHA_CONTROLLED_CONTRACT_REF)
    if not isinstance(raw_contract, str) or not raw_contract:
        return None
    try:
        parsed = json.loads(raw_contract)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _is_exact_alpha_controlled_context(context):
    return (
        context.get("environment") == "qa4"
        and context.get("workflow_profile") == _STANDARD_QA4_PROFILE
        and context.get("mode") == "real-controlled"
        and context.get("scenario_id") == SYNTHETIC_OFFERS_SCENARIO
        and context.get("application_confirmation") == _APPLICATION_CONFIRMATION
    )


def _is_exact_alpha_controlled_contract(contract, authorization=_ALPHA_AUTHORIZATION):
    if not isinstance(contract, dict):
        return False
    opt_in = contract.get("owner_opt_in") or {}
    policy = contract.get("policy") or {}
    flags = policy.get("runtime_flags") or {}
    no_auth = policy.get("operation_scoped_no_auth") or {}
    destination = policy.get("destination_attestation") or {}
    return (
        opt_in == {
            "approved": True,
            "operation": authorization,
            "authorization": authorization,
            "environment": "QA4",
            "mode": "real-controlled",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "application_confirmation": _APPLICATION_CONFIRMATION,
            "max_attempts": 1,
            "retry_count": 0,
            "fallback": False,
            "production": False,
        }
        and flags == {"REAL_EXECUTION_ENABLED": True, "REAL_EXECUTION_KILL_SWITCH": False, "REAL_TRANSPORT_ALLOWED": True, "PRODUCTION": False, "GLOBAL_NO_AUTH_ENABLED": False}
        and no_auth == {"authorization": authorization, "operation": "CREATE_OFFERS_CUSTOMER", "scenario_id": SYNTHETIC_OFFERS_SCENARIO, "environment": "QA4", "auth_required": False}
        and destination == {"source": "local_runtime_config", "environment": "QA4", "allowlist_match": True, "status": "MATCH"}
        and contract.get("approval") == {"approved": True, "risk_acceptance": True, "approver_ref": "local-controlled-ref", "ticket_ref": "local-controlled-ref", "approved_api_id": _OFFERS_API_ID, "approved_environment": "QA4", "approved_at_ref": "local-controlled-ref"}
        and contract.get("runtime_refs") == {"QA4_HOST_REF": "runtime-ref:qa4-host", "SENSITIVE_HEADERS_REF": "runtime-ref:qa4-headers", "TEST_PAYLOAD_REF": "runtime-ref:qa4-body", "CORRELATION_ID": "runtime-ref:qa4-correlation"}
        and policy.get("first_qa4_allowlist") == {"allowed_api_ids": [_OFFERS_API_ID], "items": {_OFFERS_API_ID: {"api_id": _OFFERS_API_ID, "method": "POST", "environment": "QA4", "timeout_seconds": 5, "retry_count": 0, "status": "manual_offers_customer", "operation": "CREATE_OFFERS_CUSTOMER", "scenario_id": SYNTHETIC_OFFERS_SCENARIO, "auth_required": False}}}
    )


def _standard_qa4_api_block(reason):
    return jsonify({"result": "BLOCKED", "reason": reason}), 400


def _parse_standard_qa4_timestamp(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _trusted_local_now():
    return datetime.now().astimezone()


def _provision_product_operational_release(test_id, trusted_release, expires_at):
    """Register a host-owned release; this has no HTTP entrypoint.

    The runtime owner supplies an already-approved plan before a user reaches
    Validate.  Browser validation can only reserve that pre-existing release.
    """
    test = get_product_test_runtime(test_id)
    request_plan = trusted_release.get("request_plan") if isinstance(trusted_release, dict) else None
    if not test or test_id != "create-customer-basic" or not isinstance(request_plan, dict):
        return False
    exact_scope = {
        "environment": "QA4",
        "workflow_profile": _STANDARD_QA4_PROFILE,
        "mode": "real-controlled",
        "run_id": test["real_run_id"],
        "owner_authorization": test["real_authorization"],
        "scenario_id": test["scenario_id"],
        "application_confirmation": _APPLICATION_CONFIRMATION,
    }
    if any(request_plan.get(key) != value for key, value in exact_scope.items()):
        return False
    return _PRODUCT_OPERATIONAL_RELEASES.provision(
        test_id=test_id,
        trusted_release=trusted_release,
        now=_trusted_local_now(),
        expires_at=expires_at,
    )


def _create_product_validation_context(test):
    """Reserve an opaque context from a pre-provisioned trusted release."""
    now = _trusted_local_now()
    return _PRODUCT_OPERATIONAL_RELEASES.reserve(
        test_id=test["id"],
        now=now,
        ttl=_PRODUCT_VALIDATION_CONTEXT_TTL,
    )


def _consume_product_validation_context(test_id, reference):
    return _PRODUCT_OPERATIONAL_RELEASES.claim(
        test_id=test_id,
        reference=reference,
        now=_trusted_local_now(),
    )


def _atomic_operation_window_status(context):
    """Gate the one atomic operation against its supplied offset-aware window."""
    context_data = context if isinstance(context, dict) else {}
    started_at = _parse_standard_qa4_timestamp(context_data.get("window_started_at"))
    expires_at = _parse_standard_qa4_timestamp(context_data.get("window_expires_at"))
    if (
        started_at is None
        or expires_at is None
        or started_at.tzinfo is None
        or expires_at.tzinfo is None
        or started_at >= expires_at
    ):
        return "WINDOW_INVALID"
    now = _trusted_local_now()
    if now.tzinfo is None:
        return "WINDOW_INVALID"
    if now < started_at:
        return "WINDOW_NOT_STARTED"
    if now >= expires_at:
        return "WINDOW_EXPIRED"
    return None


def _standard_qa4_api_context(data):
    """Return a closed, mock-only context or a stable validation reason."""

    if not isinstance(data, dict):
        return None, None, "MALFORMED_REQUEST"

    values = {field: data.get(field) for field in _STANDARD_QA4_CONTEXT_FIELDS}
    if any(not isinstance(value, str) or not value for value in values.values()):
        return None, None, "MISSING_ORCHESTRATION_CONTEXT"
    if data.get("mode") != "mock":
        return None, None, "MODE_NOT_ALLOWED"
    if data.get("environment") != "QA4":
        return None, None, "ENVIRONMENT_NOT_ALLOWED"
    if data.get("workflow_profile") != _STANDARD_QA4_PROFILE:
        return None, None, "WORKFLOW_PROFILE_NOT_ALLOWED"

    window_started_at = _parse_standard_qa4_timestamp(values["window_started_at"])
    window_expires_at = _parse_standard_qa4_timestamp(values["window_expires_at"])
    if (
        window_started_at is None
        or window_expires_at is None
        or window_started_at >= window_expires_at
    ):
        return None, None, "INVALID_OPERATIONAL_WINDOW"

    evaluated_at = data.get("evaluated_at")
    if _parse_standard_qa4_timestamp(evaluated_at) is None:
        return None, None, "INVALID_EVALUATED_AT"

    return (
        {
            "environment": "qa4",
            "workflow_profile": _STANDARD_QA4_PROFILE,
            **values,
        },
        evaluated_at,
        None,
    )


@app.route("/")
def index():
    return render_template(
        "index.html",
        scripts=SCRIPTS.keys(),
        qa_environments=list_sanitized_qa_environments(),
        runtime_profiles=list_sanitized_runtime_profiles(),
    )


@app.route("/api/questions")
def api_questions():
    return jsonify({"questions": get_questions()})


@app.route("/api/templates")
def api_list_templates():
    templates = list_templates(
        category=request.args.get("category"),
        event_type=request.args.get("event_type"),
        customer_type=request.args.get("customer_type"),
    )
    return jsonify(
        {
            "templates": templates,
            "categories": list_template_categories(),
            "total": len(templates),
        }
    )


@app.route("/api/templates/<template_id>")
def api_get_template(template_id):
    template = get_template(template_id)

    if not template:
        return jsonify({"erro": "template nao encontrado"}), 404

    return jsonify({"template": template})


@app.route("/api/scenarios/generate", methods=["POST"])
def api_generate_scenario():
    data = request.get_json(silent=True) or {}

    try:
        scenario = generate_scenario(data)
        saved_path = save_scenario(scenario)
    except ScenarioValidationError as exc:
        return jsonify({"erro": str(exc), "details": exc.errors}), 400

    return jsonify({"scenario": scenario, "saved_path": saved_path}), 201


@app.route("/api/scenarios")
def api_list_scenarios():
    return jsonify({"scenarios": list_scenarios()})


@app.route("/api/adapters")
def api_list_adapters():
    adapters = list_adapters()
    return jsonify({"adapters": adapters, "total": len(adapters)})


@app.route("/api/adapters/health")
def api_adapters_health():
    checks = adapters_healthcheck()
    status = "passed" if all(item["status"] == "passed" for item in checks) else "failed"
    return jsonify({"status": status, "adapters": checks})


@app.route("/api/qa4/standard/mock-run", methods=["POST"])
def api_standard_qa4_mock_run():
    context, evaluated_at, reason = _standard_qa4_api_context(request.get_json(silent=True))
    if reason:
        return _standard_qa4_api_block(reason)

    report = run_standard_qa4_application_mock(
        context, mode="mock", evaluated_at=evaluated_at
    )
    return jsonify({"result": report["result"], "report": report})


@app.route("/api/product-tests")
def api_product_tests():
    """The simplified UI consumes this curated, safe-only catalog."""
    return jsonify({"tests": list_product_tests()})


def _prepare_local_product_test_data(test):
    """Build a deterministic, in-memory local customer/line simulation record.

    The mock facade receives it in-process only.  It deliberately contains no
    customer, line, account, or MSISDN value and is never returned as a request
    payload or written to disk.
    """
    if test["id"] == "create-customer-basic":
        return {
            "entity": "customer_line",
            "environment": "QA4",
            "lifecycle": "CREATE",
            "synthetic": True,
            "reference": "LOCAL_SIMULATION_CUSTOMER_LINE_V1",
        }
    if test["id"] == "recharge-basic":
        return {
            "entity": "recharge",
            "environment": "QA4",
            "synthetic": True,
            "reference": "LOCAL_SIMULATION_RECHARGE_V1",
        }
    return None


def _validate_local_customer_line_simulation(record, mock_result):
    """Validate only the ephemeral local simulation record and mock outcome."""
    expected_record = {
        "entity": "customer_line",
        "environment": "QA4",
        "lifecycle": "CREATE",
        "synthetic": True,
        "reference": "LOCAL_SIMULATION_CUSTOMER_LINE_V1",
    }
    return "PASS" if record == expected_record and mock_result == "PASS" else "FAIL"


def _run_local_recharge_simulation(record):
    """Use the existing deterministic recharge template and fake-only adapter.

    The generated scenario and request plan never leave this function.  The
    public product response contains only an opaque local reference.
    """
    scenario = generate_scenario({
        "template_id": "recarga-pre-bonus-d0",
        "campaign_name": "Local Recharge Basic",
        "campaign_id": "LOCAL_RECHARGE_BASIC",
    })
    report = run_adapter_scenario(scenario, mode="mock")
    http_results = [
        result for result in report["adapter_results"]
        if result.get("step_type") == "smartoffers.http_plan"
    ]
    fake_plan_ready = bool(http_results) and all(
        result.get("adapter_id") == "fake-smartoffers"
        and (result.get("metadata") or {}).get("external_calls") is False
        and (result.get("metadata") or {}).get("network_calls") is False
        for result in http_results
    )
    expected_record = {
        "entity": "recharge",
        "environment": "QA4",
        "synthetic": True,
        "reference": "LOCAL_SIMULATION_RECHARGE_V1",
    }
    return "PASS" if record == expected_record and report["status"] == "passed" and fake_plan_ready else "FAIL"


@app.route("/api/product-tests/<test_id>/validate", methods=["POST"])
def api_product_test_validate(test_id):
    test = get_product_test_runtime(test_id)
    if not test:
        return jsonify({"result": "BLOCKED", "reason": "TEST_NOT_FOUND"}), 404
    public_test = get_product_test(test_id)
    if test["availability"] == "BLOCKED_EXTERNAL_INFORMATION":
        return jsonify({
            "result": "BLOCKED",
            "reason": "ADD_OFFER_EXTERNAL_INFORMATION_REQUIRED",
            "test": public_test,
            "phase": "VALIDATION",
            "execution_available": False,
        })
    if test["availability"] not in {"READY", "CONTRACT_READY"}:
        return jsonify({"result": "BLOCKED", "reason": "CAPABILITY_NOT_READY", "test": public_test})
    contract_plan = validate_contract_plan(test)
    if contract_plan and not contract_plan["valid"]:
        return jsonify({
            "result": "BLOCKED",
            "reason": contract_plan["reason"],
            "test": public_test,
            "phase": "VALIDATION",
            "display_status": "CONTRACT_MAPPING_BLOCKED",
            "execution_available": False,
        })
    checks = ["Environment", "Test data", "Required configuration", "Preflight"]
    execution_ready = False
    post_execution_db_validation_ready = bool(test.get("read_only_validation_ready"))
    authorization_state = "NOT_APPLICABLE"
    validation_context_ref = None
    validation_context_expires_at = None
    if test_id == "create-customer-basic":
        checks = [
            "QA4 environment",
            "Synthetic test data",
            "Operation and scenario contract",
            "Destination contract",
            "Evidence capture",
            "One-shot capability",
            "Authorization required",
        ]
        execution_ready = bool(test.get("real_contract_ready"))
        authorization_state = "REQUIRES_AUTHORIZATION"
        if execution_ready:
            validation_context_ref, validation_context_expires_at = _create_product_validation_context(test)
            execution_ready = validation_context_ref is not None
    if test["availability"] == "CONTRACT_READY":
        checks = [
            "Environment",
            "Existing operation contract",
            "Sanitized API mapping",
            "Local mock-plan preflight",
        ]
    return jsonify({
        "result": "PASS",
        "test": public_test,
        "checks": checks,
        "mode": "QA_READINESS" if test_id == "create-customer-basic" else test["execution_mode"],
        "execution_available": test["execution_available"],
        "execution_ready": execution_ready,
        "post_execution_db_validation_ready": post_execution_db_validation_ready,
        "authorization_state": authorization_state,
        "phase": "EXECUTION_PREFLIGHT" if test["execution_available"] else "VALIDATION",
        "display_status": (
            "QA_READY_REQUIRES_AUTHORIZATION"
            if test_id == "create-customer-basic" and execution_ready
            else "AUTHORIZATION_REQUIRED"
            if test_id == "create-customer-basic"
            else "READY_FOR_LOCAL_MOCK"
            if test["execution_available"]
            else "READY_FOR_CONTRACT_REVIEW"
        ),
        "reason": (
            "QA_EXECUTION_REQUIRES_OWNER_AUTHORIZATION"
            if test_id == "create-customer-basic" and execution_ready
            else "TRUSTED_OPERATIONAL_RELEASE_REQUIRED"
            if test_id == "create-customer-basic"
            else "LOCAL_MOCK_READY"
            if test["execution_available"]
            else "CONTRACT_READY_REAL_BINDING_AND_VALIDATION_REQUIRED"
        ),
        "contract_preview": contract_plan["preview"] if contract_plan else None,
        "validation_context_ref": validation_context_ref,
        "validation_context_expires_at": (
            validation_context_expires_at.isoformat() if validation_context_expires_at else None
        ),
    })


@app.route("/api/product-tests/<test_id>/execute", methods=["POST"])
def api_product_test_execute(test_id):
    test = get_product_test_runtime(test_id)
    if not test:
        return jsonify({"result": "BLOCKED", "reason": "TEST_NOT_FOUND"}), 404
    public_test = get_product_test(test_id)
    parsed_request_data = request.get_json(silent=True)
    request_data = parsed_request_data if isinstance(parsed_request_data, dict) else {}
    if test_id == "create-customer-basic":
        if request_data.get("intent") != "EXECUTE_IN_QA":
            return jsonify({"result": "BLOCKED", "reason": "QA_EXECUTION_INTENT_REQUIRED"})
        if set(request_data).difference({"intent", "validation_context_ref"}):
            return jsonify({"result": "BLOCKED", "reason": "PRODUCT_EXECUTION_INPUT_NOT_ALLOWED"})
        controlled_request, reason = _consume_product_validation_context(
            test_id, request_data.get("validation_context_ref")
        )
        if reason:
            return jsonify({"result": "BLOCKED", "reason": reason})
        report, status = _run_standard_qa4_real_controlled_request(controlled_request)
        return jsonify(report), status
    if request_data.get("intent") == "EXECUTE_IN_QA" or request_data.get("validation_context_ref"):
        return jsonify({"result": "BLOCKED", "reason": "QA_EXECUTION_NOT_AVAILABLE"})
    if test["availability"] == "BLOCKED_EXTERNAL_INFORMATION":
        return jsonify({
            "result": "BLOCKED",
            "reason": "ADD_OFFER_EXTERNAL_INFORMATION_REQUIRED",
            "test": public_test,
        })
    if not test.get("execution_available"):
        return jsonify({
            "result": "BLOCKED",
            "reason": "REAL_BINDING_AND_VALIDATION_NOT_READY",
            "test": public_test,
        })
    # No real-controlled bridge is reachable from this product-facing endpoint.
    synthetic_data = _prepare_local_product_test_data(test)
    context = {"environment": "qa4", "workflow_profile": _STANDARD_QA4_PROFILE}
    if synthetic_data:
        context["test_data"] = synthetic_data
    if test_id == "recharge-basic":
        local_result = _run_local_recharge_simulation(synthetic_data)
        mock_result = local_result
        report = None
        validation_strategy = "LOCAL_RECHARGE_REQUEST_PLAN_SIMULATION"
        completion_reason = "LOCAL_RECHARGE_SIMULATION_COMPLETED"
    else:
        report = run_standard_qa4_application_mock(
            context,
            mode="mock",
            evaluated_at=datetime.now().astimezone().isoformat(),
        )
        mock_result = report["result"]
        local_result = (
            _validate_local_customer_line_simulation(synthetic_data, mock_result)
            if synthetic_data and mock_result == "PASS"
            else mock_result
        )
        validation_strategy = "LOCAL_CUSTOMER_LINE_SIMULATION"
        completion_reason = "LOCAL_CUSTOMER_LINE_SIMULATION_COMPLETED"
    return jsonify({
        "result": local_result,
        "test": public_test,
        "environment": "QA4",
        "duration_ms": 0,
        "reason": completion_reason,
        "evidence_reference": "MOCK_RUN_NOT_PERSISTED",
        "validation": {
            "result": local_result,
            "strategy": validation_strategy,
            "external_read_only_lookup_used": False,
        },
        "evidence_summary": {
            "preflight": mock_result,
            "execution": mock_result,
            "local_verification": local_result,
            "request_sent": False,
        },
        "synthetic_data": {
            "prepared": bool(synthetic_data),
            "reference": synthetic_data["reference"] if synthetic_data else None,
        },
        **({"report": report} if report is not None else {}),
    })


@app.route("/api/evidence/<run_id>")
def api_sanitized_real_run_evidence(run_id):
    """Serve only the fixed public projection of a known sanitized run."""
    record = load_sanitized_real_run_evidence(run_id)
    if record is None:
        return jsonify({"result": "BLOCKED", "reason": "EVIDENCE_NOT_FOUND"}), 404
    return jsonify({"result": record["result"], "evidence": record})


@app.route("/api/evidence")
def api_sanitized_real_run_evidence_list():
    return jsonify({"evidence": list_sanitized_real_run_evidence()})


def _run_standard_qa4_real_controlled_request(data):
    """Invoke the existing controlled service from a trusted in-process caller.

    This is shared by the compatibility endpoint and the product facade.  It
    intentionally accepts a complete server-owned request plan, never an HTTP
    redirect or a browser-supplied real-operation contract.
    """
    if not isinstance(data, dict):
        return {"result": "BLOCKED", "reason": "MALFORMED_REQUEST"}, 400
    if data.get("mode") != "real-controlled":
        return {"result": "BLOCKED", "reason": "MODE_NOT_ALLOWED"}, 400
    if data.get("scenario_id") != SYNTHETIC_OFFERS_SCENARIO:
        return {"result": "BLOCKED", "reason": "SCENARIO_NOT_ALLOWED"}, 400
    requested_run_id = data.get("run_id")
    if requested_run_id not in (None, _RUN_02_ID, _RUN_03A_ID):
        return {"result": "BLOCKED", "reason": "RUN_ID_NOT_ALLOWED"}, 400
    expected_authorization = _run_authorization({"run_id": requested_run_id})
    supplied_authorization = data.get("owner_authorization", _ALPHA_AUTHORIZATION)
    if supplied_authorization != expected_authorization:
        return {"result": "BLOCKED", "reason": "OWNER_AUTHORIZATION_REQUIRED"}, 400
    validation_data = {**data, "mode": "mock"}
    context, evaluated_at, reason = _standard_qa4_api_context(validation_data)
    if reason:
        return {"result": "BLOCKED", "reason": reason}, 400
    if data.get("application_confirmation") != _APPLICATION_CONFIRMATION:
        return {"result": "BLOCKED", "reason": "APPLICATION_CONFIRMATION_REQUIRED"}, 400
    controlled_context = {
        **context,
        "mode": "real-controlled",
        "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
        "application_confirmation": _APPLICATION_CONFIRMATION,
    }
    if requested_run_id:
        controlled_context["run_id"] = requested_run_id
    window_status = _atomic_operation_window_status(controlled_context)
    if window_status:
        return {"result": "BLOCKED", "reason": window_status}, 200
    contract = _qa4_controlled_contract_from_environ()
    if not _atomic_static_preflight_ready(controlled_context, contract):
        return {"result": "BLOCKED", "reason": "ATOMIC_STATIC_PREFLIGHT_REQUIRED"}, 200
    report = run_atomic_qa4_bda_offer_discovery_and_offers_create(
        controlled_context,
        mode="real-controlled",
        evaluated_at=evaluated_at,
        scenario_id=SYNTHETIC_OFFERS_SCENARIO,
        bda_environ=_RuntimeEnvironment(os.environ),
        bda_driver_factory=_governed_bda_driver,
        bda_authorization={
            "owner_authorization": _run_bda_authorization(controlled_context),
            "operation": "QA4_BDA_OFFER_DISCOVERY",
            "bda_operation": "OFFER_DISCOVERY",
            "read_only_discovery_authorized": True,
            "authorization_verified": True,
            "destination_attestation_ready": True,
            "offers_operation": "CREATE_OFFERS_CUSTOMER",
            "scenario_id": SYNTHETIC_OFFERS_SCENARIO,
            "access_mode": "READ_ONLY",
            "attempts_used": 0,
        },
        bda_ledger=_DEFAULT_BDA_DISCOVERY_LEDGER,
        runtime_provider=_qa4_owner_execution_inputs,
    )
    evidence_context = {
        **controlled_context,
        "operation": "CREATE_OFFERS_CUSTOMER",
        "static_preflight": "READY",
        "operational_preflight": "READY",
        "destination_attestation": "READY",
        "authorization_verification": "READY",
        "run_id": controlled_context.get("run_id", "ALPHA_REAL_RUN_01"),
        "bda_discovery_executed": (report.get("bda_discovery") or {}).get("status") == "QA4_BDA_OFFER_DISCOVERY_OK",
        "bda_read_only_confirmed": (report.get("bda_discovery") or {}).get("select_only") is True,
        "test_offer_ready": (report.get("bda_discovery") or {}).get("found_valid_offer") is True,
        "atomic_in_process_handoff": (report.get("bda_discovery") or {}).get("found_valid_offer") is True,
        "standard_runner_real_path": report.get("real_call_executed") is True,
        "product_test_name": "Create Customer with Offer" if requested_run_id == _RUN_03A_ID else None,
        "db_postcondition_verified": False,
        "db_validation_status": "NOT_CONFIGURED" if requested_run_id == _RUN_03A_ID else None,
    }
    # A preflight/BDA block is not an execution result and must not generate a
    # misleading real-run artifact.  A sent request (including a failed one)
    # is captured automatically.
    if report.get("real_call_executed") is True or report.get("executor_send_attempted") is True:
        try:
            evidence_record = persist_sanitized_real_run_evidence(report, context=evidence_context)
        except OSError:
            evidence_record = {"recorded": False, "reason": "LOCAL_EVIDENCE_PERSISTENCE_FAILED"}
        public_evidence_reference = evidence_record.get("reference") if evidence_record.get("recorded") is True else None
        report = {
            **report,
            "evidence_recording": evidence_record,
            **({"evidence_reference": public_evidence_reference} if public_evidence_reference else {}),
        }
    return report, 200


@app.route("/api/qa4/standard/real-controlled-run", methods=["POST"])
def api_standard_qa4_real_controlled_run():
    report, status = _run_standard_qa4_real_controlled_request(request.get_json(silent=True))
    return jsonify(report), status
@app.route("/api/api-catalog")
def api_list_api_catalog():
    return jsonify(list_api_catalog_entries())


@app.route("/api/api-catalog/<api_id>")
def api_get_api_catalog_entry(api_id):
    entry = get_api_catalog_entry(api_id)

    if not entry:
        return jsonify({"erro": "api nao encontrada"}), 404

    return jsonify({"api": entry})


@app.route("/api/scenarios/<scenario_id>")
def api_get_scenario(scenario_id):
    scenario = load_scenario(scenario_id)

    if not scenario:
        return jsonify({"erro": "cenario nao encontrado"}), 404

    return jsonify({"scenario": scenario})


@app.route("/api/scenarios/<scenario_id>/dry-run", methods=["POST"])
def api_dry_run_scenario(scenario_id):
    scenario = load_scenario(scenario_id)

    if not scenario:
        return jsonify({"erro": "cenario nao encontrado"}), 404

    report = run_dry_run(scenario)
    saved_path = save_dry_run_report(report)

    return jsonify({"report": report, "saved_path": saved_path}), 201


@app.route("/api/scenarios/<scenario_id>/adapter-run", methods=["POST"])
def api_adapter_run_scenario(scenario_id):
    scenario = load_scenario(scenario_id)

    if not scenario:
        return jsonify({"erro": "cenario nao encontrado"}), 404

    data = request.get_json(silent=True) or {}

    try:
        report = run_adapter_scenario(scenario, mode=data.get("mode", "mock"))
    except AdapterRunModeError as exc:
        return jsonify({"erro": str(exc), "details": {"allowed_modes": ["mock"]}}), 400

    return jsonify({"report": report}), 201


@app.route("/api/dry-runs/<report_id>")
def api_get_dry_run(report_id):
    report = load_dry_run_report_by_id(report_id)

    if not report:
        return jsonify({"erro": "dry-run nao encontrado"}), 404

    return jsonify({"report": report})


def _send_export_file(path, export_format):
    mimetype = get_export_mimetype(export_format) or "application/octet-stream"
    return send_file(path, mimetype=mimetype, as_attachment=True, download_name=path.name)


@app.route("/api/scenarios/<scenario_id>/export/<export_format>")
def api_export_scenario(scenario_id, export_format):
    try:
        path = export_scenario_artifact(scenario_id, export_format)
    except ExportSourceNotFoundError:
        return jsonify({"erro": "cenario nao encontrado"}), 404
    except ExportFormatError:
        return jsonify({"erro": "formato de exportacao invalido"}), 400

    return _send_export_file(path, export_format)


@app.route("/api/dry-runs/<report_id>/export/<export_format>")
def api_export_dry_run(report_id, export_format):
    try:
        path = export_dry_run_artifact(report_id, export_format)
    except ExportSourceNotFoundError:
        return jsonify({"erro": "dry-run nao encontrado"}), 404
    except ExportFormatError:
        return jsonify({"erro": "formato de exportacao invalido"}), 400

    return _send_export_file(path, export_format)


@app.route("/executar")
def executar():
    tipo = request.args.get("tipo")
    analisar = request.args.get("analisar") == "true"
    execution_mode = request.args.get("execution_mode") or request.args.get("mode")
    environment = request.args.get("environment")
    runtime_profile = request.args.get("runtime_profile")
    real_confirmed = request.args.get("confirm_real") == "true"
    return Response(
        stream_legacy_execution(
            tipo,
            analisar,
            execution_mode=execution_mode,
            environment=environment,
            runtime_profile=runtime_profile,
            real_confirmed=real_confirmed,
        ),
        mimetype="text/event-stream",
    )


@app.route("/listar_testes")
def listar_testes():
    return list_legacy_tests()


@app.route("/ver_teste")
def ver_teste():
    return load_legacy_test(request.args.get("nome"))


@app.route("/abrir_pasta")
def abrir_pasta():
    return jsonify(open_legacy_base_folder())


if __name__ == "__main__":
    app.run(debug=True)
