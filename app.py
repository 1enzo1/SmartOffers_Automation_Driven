import json
import os
import importlib
from datetime import datetime

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
from core.real_execution.sanitized_evidence import (
    load_sanitized_real_run_evidence,
    list_sanitized_real_run_evidence,
    persist_sanitized_real_run_evidence,
)
from core.product_test_catalog import (
    get_product_test,
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
_RUN_02_BDA_AUTHORIZATION = "ONE_QA4_REPEATABILITY_SMOKE_RUN_02"
_DEFAULT_BDA_DISCOVERY_LEDGER = BdaDiscoveryAttemptLedger()


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
    return _ALPHA_AUTHORIZATION


def _run_bda_authorization(context):
    return _RUN_02_BDA_AUTHORIZATION if _run_authorization(context) == _RUN_02_AUTHORIZATION else _ATOMIC_BDA_AUTHORIZATION


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


@app.route("/api/product-tests/<test_id>/validate", methods=["POST"])
def api_product_test_validate(test_id):
    test = get_product_test(test_id)
    if not test:
        return jsonify({"result": "BLOCKED", "reason": "TEST_NOT_FOUND"}), 404
    if test["availability"] not in {"READY", "CONTRACT_READY"}:
        return jsonify({"result": "BLOCKED", "reason": "CAPABILITY_NOT_READY", "test": test})
    contract_plan = validate_contract_plan(test)
    if contract_plan and not contract_plan["valid"]:
        return jsonify({
            "result": "BLOCKED",
            "reason": contract_plan["reason"],
            "test": test,
            "phase": "VALIDATION",
            "display_status": "CONTRACT_MAPPING_BLOCKED",
            "execution_available": False,
        })
    checks = ["Environment", "Test data", "Required configuration", "Preflight"]
    if test["availability"] == "CONTRACT_READY":
        checks = [
            "Environment",
            "Existing operation contract",
            "Sanitized API mapping",
            "Local mock-plan preflight",
        ]
    return jsonify({
        "result": "PASS",
        "test": test,
        "checks": checks,
        "mode": test["execution_mode"],
        "execution_available": test["execution_available"],
        "phase": "EXECUTION_PREFLIGHT" if test["execution_available"] else "VALIDATION",
        "display_status": (
            "READY_FOR_LOCAL_MOCK"
            if test["execution_available"]
            else "READY_FOR_CONTRACT_REVIEW"
        ),
        "reason": (
            "LOCAL_MOCK_READY"
            if test["execution_available"]
            else "CONTRACT_READY_REAL_BINDING_AND_VALIDATION_REQUIRED"
        ),
        "contract_preview": contract_plan["preview"] if contract_plan else None,
    })


@app.route("/api/product-tests/<test_id>/execute", methods=["POST"])
def api_product_test_execute(test_id):
    test = get_product_test(test_id)
    if not test:
        return jsonify({"result": "BLOCKED", "reason": "TEST_NOT_FOUND"}), 404
    if not test.get("execution_available"):
        return jsonify({
            "result": "BLOCKED",
            "reason": "REAL_BINDING_AND_VALIDATION_NOT_READY",
            "test": test,
            "attempts": "0/0",
        })
    # No real-controlled bridge is reachable from this product-facing endpoint.
    report = run_standard_qa4_application_mock(
        {"environment": "qa4", "workflow_profile": _STANDARD_QA4_PROFILE},
        mode="mock",
        evaluated_at=datetime.now().astimezone().isoformat(),
    )
    return jsonify({
        "result": report["result"],
        "test": test,
        "environment": "QA4",
        "duration_ms": 0,
        "attempts": "0/0",
        "reason": "LOCAL_MOCK_COMPLETED",
        "evidence_reference": "MOCK_RUN_NOT_PERSISTED",
        "report": report,
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


@app.route("/api/qa4/standard/real-controlled-run", methods=["POST"])
def api_standard_qa4_real_controlled_run():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _standard_qa4_api_block("MALFORMED_REQUEST")
    if data.get("mode") != "real-controlled":
        return _standard_qa4_api_block("MODE_NOT_ALLOWED")
    if data.get("scenario_id") != SYNTHETIC_OFFERS_SCENARIO:
        return _standard_qa4_api_block("SCENARIO_NOT_ALLOWED")
    requested_run_id = data.get("run_id")
    if requested_run_id not in (None, _RUN_02_ID):
        return _standard_qa4_api_block("RUN_ID_NOT_ALLOWED")
    expected_authorization = _RUN_02_AUTHORIZATION if requested_run_id == _RUN_02_ID else _ALPHA_AUTHORIZATION
    supplied_authorization = data.get("owner_authorization", _ALPHA_AUTHORIZATION)
    if supplied_authorization != expected_authorization:
        return _standard_qa4_api_block("OWNER_AUTHORIZATION_REQUIRED")
    validation_data = {**data, "mode": "mock"}
    context, evaluated_at, reason = _standard_qa4_api_context(validation_data)
    if reason:
        return _standard_qa4_api_block(reason)
    if data.get("application_confirmation") != _APPLICATION_CONFIRMATION:
        return _standard_qa4_api_block("APPLICATION_CONFIRMATION_REQUIRED")
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
        return jsonify({"result": "BLOCKED", "reason": window_status})
    contract = _qa4_controlled_contract_from_environ()
    if not _atomic_static_preflight_ready(controlled_context, contract):
        return jsonify({"result": "BLOCKED", "reason": "ATOMIC_STATIC_PREFLIGHT_REQUIRED"})
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
    }
    # A preflight/BDA block is not an execution result and must not generate a
    # misleading real-run artifact.  A sent request (including a failed one)
    # is captured automatically.
    if report.get("real_call_executed") is True or report.get("executor_send_attempted") is True:
        try:
            evidence_record = persist_sanitized_real_run_evidence(report, context=evidence_context)
        except OSError:
            evidence_record = {"recorded": False, "reason": "LOCAL_EVIDENCE_PERSISTENCE_FAILED"}
        report = {**report, "evidence_recording": evidence_record}
    return jsonify(report)
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
