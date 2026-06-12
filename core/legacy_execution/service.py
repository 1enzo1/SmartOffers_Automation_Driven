import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path

from core.legacy_execution.modes import evaluate_execution_mode_request
from core.utils.evidence_response_contract import analyze_smartoffers_response


BASE_PATH = "evidencias_variante"
LEGACY_REAL_SCRIPT_ENV = "SMARTOFFERS_ALLOW_LEGACY_REAL_SCRIPT"
LEGACY_REAL_SCRIPT_CONFIRMATION = "YES_I_UNDERSTAND"
LEGACY_REAL_BLOCKED_MARKER = "execucao real bloqueada"

SCRIPTS = {
    "padrao": "test_campaign_api.py",
    "variante": "test_campaign_api_variante.py",
    "copy": "test_campaign_api_variante_copy.py",
}


def stream_legacy_execution(
    tipo,
    analisar,
    allow_legacy_real_script=False,
    execution_mode=None,
    environment=None,
    real_confirmed=False,
    process_factory=None,
):
    script = SCRIPTS.get(tipo)

    if not script:
        yield f"data:ERROR|tipo inválido: {tipo}\n\n"
        return

    try:
        yield f"data:RUN|START|{tipo}\n\n"

        mode_decision = evaluate_execution_mode_request(
            mode=execution_mode,
            environment=environment,
            real_confirmed=real_confirmed,
        )
        if not mode_decision["allowed"]:
            reasons = ",".join(mode_decision["blocked_reasons"])
            yield f"data:ERROR|Execution mode blocked: {reasons}\n\n"
            yield f"data:RUN|END|BLOCKED|0|1\n\n"
            return

        yield (
            "data:LOG|EXECUTION_MODE|"
            f"{mode_decision['mode']}|environment={mode_decision['environment'] or 'none'}\n\n"
        )

        if mode_decision["dry_run_only"]:
            yield "data:LOG|Dry-run local: no legacy subprocess was started.\n\n"
            yield "data:RUN|END|PASS|0|0\n\n"
            return

        env = build_legacy_execution_env(
            analisar,
            allow_legacy_real_script=mode_decision["allow_legacy_real_script"],
            execution_mode=mode_decision["mode"],
            environment=mode_decision["environment"],
        )
        process_factory = process_factory or subprocess.Popen

        process = process_factory(
            [sys.executable, "-u", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

        total_steps = 0
        errors = 0
        blocked = False
        scenario_paths = set()

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            if is_legacy_real_blocked_output(line):
                blocked = True
                errors += 1
                yield f"data:ERROR|{line}\n\n"
            elif line.startswith("STEP|"):
                total_steps += 1
                yield f"data:{line}\n\n"
            elif line.startswith("SCENARIO|"):
                scenario_path = extract_legacy_scenario_path(line)
                if scenario_path:
                    scenario_paths.add(scenario_path)
                yield f"data:{line}\n\n"
            elif line.startswith("ANALYSIS|"):
                yield f"data:{line}\n\n"
            elif "erro" in line.lower():
                errors += 1
                yield f"data:ERROR|{line}\n\n"
            else:
                yield f"data:LOG|{line}\n\n"

        process.wait()
        response_summary = analyze_legacy_response_files(scenario_paths)
        if response_summary["failed"] > 0:
            errors += response_summary["failed"]
            issue_summary = ",".join(response_summary["issue_counts"].keys()) or "unknown"
            yield (
                "data:ERROR|SmartOffers functional response failure:"
                f" failed={response_summary['failed']} issues={issue_summary}\n\n"
            )
        elif scenario_paths and response_summary["total"] == 0:
            errors += 1
            yield "data:ERROR|SmartOffers response evidence missing\n\n"

        returncode = getattr(process, "returncode", 0)
        if returncode not in (0, None) and not blocked:
            errors += 1

        status = resolve_legacy_run_status(
            blocked=blocked,
            errors=errors,
            returncode=returncode,
            response_summary=response_summary,
        )
        yield f"data:RUN|END|{status}|{total_steps}|{errors}\n\n"
    except Exception as exc:
        yield f"data:ERROR|{str(exc)}\n\n"


def build_legacy_execution_env(
    analisar,
    allow_legacy_real_script=False,
    execution_mode=None,
    environment=None,
    base_env=None,
):
    env = dict(os.environ if base_env is None else base_env)
    env["ANALISAR_EXECUCAO"] = "1" if analisar else "0"
    env["SMARTOFFERS_EXECUTION_MODE"] = str(execution_mode or "mock")
    if environment:
        env["SMARTOFFERS_QA_ENVIRONMENT"] = str(environment)
    else:
        env.pop("SMARTOFFERS_QA_ENVIRONMENT", None)
    env.pop(LEGACY_REAL_SCRIPT_ENV, None)

    if allow_legacy_real_script:
        env[LEGACY_REAL_SCRIPT_ENV] = LEGACY_REAL_SCRIPT_CONFIRMATION

    return env


def resolve_legacy_run_status(blocked, errors, returncode, response_summary=None):
    if blocked:
        return "BLOCKED"
    if errors > 0:
        return "FAIL"
    if returncode not in (0, None):
        return "FAIL"
    if response_summary and response_summary.get("failed", 0) > 0:
        return "FAIL"
    return "PASS"


def is_legacy_real_blocked_output(line):
    normalized = unicodedata.normalize("NFKD", line)
    ascii_line = normalized.encode("ascii", "ignore").decode("ascii")
    return LEGACY_REAL_BLOCKED_MARKER in ascii_line.lower()


def extract_legacy_scenario_path(line):
    parts = line.split("|")
    if len(parts) < 6:
        return None
    return "|".join(parts[5:]).strip() or None


def analyze_legacy_response_files(scenario_paths):
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "issue_counts": {},
    }

    for response_file in find_legacy_response_files(scenario_paths):
        response = load_json_file(response_file)
        result = analyze_smartoffers_response(response)
        summary["total"] += 1

        if result["status"] == "PASS":
            summary["passed"] += 1
            continue

        summary["failed"] += 1
        for issue in result["issues"]:
            summary["issue_counts"][issue] = summary["issue_counts"].get(issue, 0) + 1

    return summary


def find_legacy_response_files(scenario_paths):
    seen = set()

    for scenario_path in scenario_paths:
        folder = Path(scenario_path)
        if not folder.exists() or not folder.is_dir():
            continue

        for path in sorted(folder.glob("*response*.json")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def load_json_file(path):
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return None


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
