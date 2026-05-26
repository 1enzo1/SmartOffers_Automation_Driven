import json
import os
import re
from pathlib import Path


DEFAULT_GENERATED_DIR = "cenarios_gerados"
SCENARIO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def get_generated_dir():
    return Path(os.getenv("CENARIOS_GERADOS_PATH", DEFAULT_GENERATED_DIR))


def save_scenario(scenario):
    generated_dir = get_generated_dir()
    generated_dir.mkdir(parents=True, exist_ok=True)

    path = generated_dir / f"{scenario['id']}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)

    return str(path)


def list_scenarios():
    generated_dir = get_generated_dir()
    if not generated_dir.exists():
        return []

    scenarios = []

    for path in generated_dir.glob("*.json"):
        try:
            with path.open(encoding="utf-8") as f:
                scenario = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        scenario_id = scenario.get("id") or path.stem
        if not SCENARIO_ID_PATTERN.fullmatch(scenario_id):
            continue

        stat = path.stat()
        source_answers = scenario.get("source_answers") or {}
        scenarios.append(
            {
                "id": scenario_id,
                "titulo": scenario.get("titulo", scenario_id),
                "resumo": scenario.get("resumo", ""),
                "campaign_id": source_answers.get("campaign_id", ""),
                "event_type": source_answers.get("event_type", ""),
                "customer_type": source_answers.get("customer_type", ""),
                "validation_count": len(scenario.get("validation_steps", [])),
                "evidence_count": len(scenario.get("evidence_files", [])),
                "updated_at": stat.st_mtime,
            }
        )

    return sorted(scenarios, key=lambda item: item["updated_at"], reverse=True)


def load_scenario(scenario_id):
    if not scenario_id or not SCENARIO_ID_PATTERN.fullmatch(scenario_id):
        return None

    path = get_generated_dir() / f"{scenario_id}.json"
    if not path.exists():
        return None

    with path.open(encoding="utf-8") as f:
        return json.load(f)
