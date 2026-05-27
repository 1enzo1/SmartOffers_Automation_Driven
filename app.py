import json
import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_file

from core.generation import (
    ScenarioValidationError,
    generate_scenario,
    get_questions,
    list_scenarios,
    load_scenario,
    save_scenario,
)
from core.exporters import (
    ExportFormatError,
    ExportSourceNotFoundError,
    export_dry_run_artifact,
    export_scenario_artifact,
    get_export_mimetype,
    load_dry_run_report_by_id,
)
from core.simulation import run_dry_run, save_dry_run_report


app = Flask(__name__)

BASE_PATH = "evidencias_variante"

SCRIPTS = {
    "padrao": "test_campaign_api.py",
    "variante": "test_campaign_api_variante.py",
    "copy": "test_campaign_api_variante_copy.py",
}


@app.route("/")
def index():
    return render_template("index.html", scripts=SCRIPTS.keys())


@app.route("/api/questions")
def api_questions():
    return jsonify({"questions": get_questions()})


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
    script = SCRIPTS.get(tipo)

    def gerar_log():
        if not script:
            yield f"data:ERROR|tipo inválido: {tipo}\n\n"
            return

        try:
            yield f"data:RUN|START|{tipo}\n\n"

            env = os.environ.copy()
            env["ANALISAR_EXECUCAO"] = "1" if analisar else "0"

            processo = subprocess.Popen(
                [sys.executable, "-u", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )

            total_steps = 0
            erros = 0

            for linha in processo.stdout:
                linha = linha.strip()
                if not linha:
                    continue

                if linha.startswith("STEP|"):
                    total_steps += 1
                    yield f"data:{linha}\n\n"
                elif linha.startswith("SCENARIO|") or linha.startswith("ANALYSIS|"):
                    yield f"data:{linha}\n\n"
                elif "erro" in linha.lower():
                    erros += 1
                    yield f"data:ERROR|{linha}\n\n"
                else:
                    yield f"data:LOG|{linha}\n\n"

            processo.wait()
            status = "PASS" if erros == 0 else "FAIL"
            yield f"data:RUN|END|{status}|{total_steps}|{erros}\n\n"
        except Exception as e:
            yield f"data:ERROR|{str(e)}\n\n"

    return Response(gerar_log(), mimetype="text/event-stream")


@app.route("/listar_testes")
def listar_testes():
    base = Path(BASE_PATH)

    if not base.exists():
        return {"testes": []}

    dados = sorted(
        {
            str(arquivo.parent.relative_to(base)).replace("\\", "/")
            for arquivo in base.rglob("*.json")
            if arquivo.parent != base
        }
    )

    return {"testes": dados}


@app.route("/ver_teste")
def ver_teste():
    nome = request.args.get("nome")

    if not nome:
        return {}

    pasta = os.path.join(BASE_PATH, nome)

    if not os.path.exists(pasta):
        return {"erro": "pasta não encontrada"}

    arquivos = os.listdir(pasta)
    conteudo = {}
    resumo = None

    for arq in arquivos:
        caminho = os.path.join(pasta, arq)

        try:
            with open(caminho, encoding="utf-8") as f:
                data = json.load(f)
                conteudo[arq] = data

                if "resumo" in arq.lower():
                    resumo = data
        except Exception:
            conteudo[arq] = "não é JSON"

    return {
        "arquivos": conteudo,
        "resumo": resumo
    }


@app.route("/abrir_pasta")
def abrir_pasta():
    caminho = os.path.abspath(BASE_PATH)

    try:
        os.startfile(caminho)
    except Exception:
        return jsonify({"erro": "não foi possível abrir"})

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
