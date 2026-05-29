import json
import os
import subprocess
import sys
from pathlib import Path


BASE_PATH = "evidencias_variante"

SCRIPTS = {
    "padrao": "test_campaign_api.py",
    "variante": "test_campaign_api_variante.py",
    "copy": "test_campaign_api_variante_copy.py",
}


def stream_legacy_execution(tipo, analisar):
    script = SCRIPTS.get(tipo)

    if not script:
        yield f"data:ERROR|tipo inválido: {tipo}\n\n"
        return

    try:
        yield f"data:RUN|START|{tipo}\n\n"

        env = os.environ.copy()
        env["ANALISAR_EXECUCAO"] = "1" if analisar else "0"

        process = subprocess.Popen(
            [sys.executable, "-u", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

        total_steps = 0
        errors = 0

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            if line.startswith("STEP|"):
                total_steps += 1
                yield f"data:{line}\n\n"
            elif line.startswith("SCENARIO|") or line.startswith("ANALYSIS|"):
                yield f"data:{line}\n\n"
            elif "erro" in line.lower():
                errors += 1
                yield f"data:ERROR|{line}\n\n"
            else:
                yield f"data:LOG|{line}\n\n"

        process.wait()
        status = "PASS" if errors == 0 else "FAIL"
        yield f"data:RUN|END|{status}|{total_steps}|{errors}\n\n"
    except Exception as exc:
        yield f"data:ERROR|{str(exc)}\n\n"


def list_legacy_tests():
    base = Path(BASE_PATH)

    if not base.exists():
        return {"testes": []}

    tests = sorted(
        {
            str(file.parent.relative_to(base)).replace("\\", "/")
            for file in base.rglob("*.json")
            if file.parent != base
        }
    )

    return {"testes": tests}


def load_legacy_test(name):
    if not name:
        return {}

    folder = os.path.join(BASE_PATH, name)

    if not os.path.exists(folder):
        return {"erro": "pasta não encontrada"}

    content = {}
    summary = None

    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)

        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
                content[filename] = data

                if "resumo" in filename.lower():
                    summary = data
        except Exception:
            content[filename] = "não é JSON"

    return {"arquivos": content, "resumo": summary}


def open_legacy_base_folder():
    path = os.path.abspath(BASE_PATH)

    try:
        os.startfile(path)
    except Exception:
        return {"erro": "não foi possível abrir"}

    return {"ok": True}
