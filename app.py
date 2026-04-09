from flask import Flask, render_template, request, Response, jsonify
import subprocess
from runner.executor import executar_script
from datetime import datetime
import os
import json



app = Flask(__name__)

BASE_PATH = "evidencias_variante"

SCRIPTS = {
    "padrao": "test_campaign_api.py",
    "variante": "test_campaign_api_variante.py",
    "copy": "test_campaign_api_variante_copy.py"
}


# ==========================
# HOME
# ==========================
@app.route("/")
def index():
    return render_template("index.html", scripts=SCRIPTS.keys())


# ==========================
# EXECUÇÃO (STREAM)
# ==========================
@app.route("/executar")
def executar():

    tipo = request.args.get("tipo")
    analisar = request.args.get("analisar") == "true"

    script = SCRIPTS.get(tipo)
    if not script:
        return jsonify({"erro": f"tipo de script inválido: {tipo}"}), 400

    def gerar_log():

        try:
            yield f"data:START|{tipo}\n\n"

            processo = subprocess.Popen(
                ["python", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            total_steps = 0
            erros = 0

            for linha in processo.stdout:

                linha = linha.strip()

                # 🔥 classificação
                if "erro" in linha.lower():
                    yield f"data:ERROR|{linha}\n\n"
                    erros += 1

                elif "criação" in linha.lower():
                    yield f"data:STEP|{linha}\n\n"
                    total_steps += 1

                elif "alteração" in linha.lower():
                    yield f"data:STEP|{linha}\n\n"
                    total_steps += 1

                else:
                    yield f"data:LOG|{linha}\n\n"

            processo.wait()

            if processo.returncode != 0:
                erros += 1
                yield f"data:ERROR|processo finalizou com código {processo.returncode}\n\n"

            status = "PASS" if erros == 0 else "FAIL"

            yield f"data:END|{status}|{total_steps}|{erros}\n\n"

            if analisar:
                yield f"data:AI|Análise automática: {status}\n\n"

        except Exception as e:
            yield f"data:ERROR|{str(e)}\n\n"

    return Response(gerar_log(), mimetype="text/event-stream")


# ==========================
# LISTAR TESTES
# ==========================
@app.route("/listar_testes")
def listar_testes():

    dados = []

    if not os.path.exists(BASE_PATH):
        return {"testes": []}

    for tipo in os.listdir(BASE_PATH):

        caminho_tipo = os.path.join(BASE_PATH, tipo)

        if not os.path.isdir(caminho_tipo):
            continue

        for teste in os.listdir(caminho_tipo):

            caminho_teste = os.path.join(caminho_tipo, teste)

            if os.path.isdir(caminho_teste):
                dados.append(f"{tipo}/{teste}")

    return {"testes": dados}


# ==========================
# VER TESTE (DETALHES)
# ==========================
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
            with open(caminho) as f:
                data = json.load(f)

                conteudo[arq] = data

                # ⭐ pega resumo separado
                if "resumo" in arq.lower():
                    resumo = data

        except:
            conteudo[arq] = "não é JSON"

    return {
        "arquivos": conteudo,
        "resumo": resumo
    }


# ==========================
# ABRIR PASTA
# ==========================
@app.route("/abrir_pasta")
def abrir_pasta():

    caminho = os.path.abspath(BASE_PATH)

    try:
        os.startfile(caminho)
    except:
        return jsonify({"erro": "não foi possível abrir"})

    return jsonify({"ok": True})


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    app.run(debug=True)
