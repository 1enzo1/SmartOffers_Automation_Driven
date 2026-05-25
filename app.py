import json
import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request


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
