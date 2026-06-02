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
from core.simulation import run_dry_run, save_dry_run_report
from core.templates import get_template, list_template_categories, list_templates


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", scripts=SCRIPTS.keys())


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
    return Response(stream_legacy_execution(tipo, analisar), mimetype="text/event-stream")


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
