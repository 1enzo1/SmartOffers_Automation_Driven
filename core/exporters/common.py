import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone


KNOWN_LIMITATIONS = [
    "Dry-run e exports permanecem locais e mockados; Oracle, APIs, Kafka e Jenkins reais nao sao acionados.",
    "Limitacao conhecida: event_type == \"recarga\" ainda pode permitir recharge_scenario == \"none\" no modo mockado.",
]

EXPORT_MIME_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
}

EXPORT_EXTENSIONS = {
    "docx": "docx",
    "xlsx": "xlsx",
    "json": "json",
}


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def safe_filename(value):
    value = str(value or "").strip()
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "export"


def build_export_filename(source_type, source_id, export_type, extension):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return (
        f"{safe_filename(source_type)}-"
        f"{safe_filename(source_id)}-"
        f"{safe_filename(export_type)}-"
        f"{stamp}.{extension}"
    )


def dedupe_preserve_order(items):
    seen = set()
    unique = []

    for item in items or []:
        if not item or item in seen:
            continue
        seen.add(item)
        unique.append(item)

    return unique


def flatten_json(value, prefix=""):
    rows = []

    if isinstance(value, Mapping):
        if not value and prefix:
            rows.append((prefix, "{}"))
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_json(child, child_prefix))
        return rows

    if isinstance(value, list):
        if not value and prefix:
            rows.append((prefix, "[]"))
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            rows.extend(flatten_json(child, child_prefix))
        return rows

    if prefix:
        label = prefix
    else:
        label = "value"

    if value is None:
        rendered = ""
    elif isinstance(value, (dict, list)):
        rendered = json.dumps(value, ensure_ascii=False, indent=2)
    else:
        rendered = str(value)

    rows.append((label, rendered))
    return rows


def build_export_context(source_type, source_id, source_data, export_type, scenario=None):
    source_type = source_type or "scenario"
    source_data = source_data or {}
    scenario_data = scenario or {}
    report_data = {}

    if source_type == "dry_run":
        report_data = source_data
        if not scenario_data:
            scenario_data = {}
    else:
        scenario_data = source_data

    answers = scenario_data.get("source_answers") or {}
    title = scenario_data.get("titulo") or report_data.get("id") or source_id
    summary = scenario_data.get("resumo") or report_data.get("summary_text") or ""

    if not summary and report_data:
        report_summary = report_data.get("summary") or {}
        summary = (
            f"Dry-run {report_data.get('status', 'unknown')} "
            f"com {report_summary.get('total', 0)} steps."
        )

    warnings = dedupe_preserve_order(
        list(scenario_data.get("warnings") or []) + list(report_data.get("warnings") or [])
    )

    dry_run_summary = report_data.get("summary") or {}
    dry_run_steps = report_data.get("steps") or []
    dry_run_logs = report_data.get("logs") or []

    if answers.get("event_type") == "recarga":
        warnings = dedupe_preserve_order(
            warnings + [
                "Limitacao conhecida: event_type == \"recarga\" ainda pode permitir recharge_scenario == \"none\" no modo mockado.",
            ]
        )

    metadata = {
        "generated_at": utc_now_iso(),
        "export_type": export_type,
        "source_type": source_type,
        "source_id": source_id,
        "known_limitations": list(KNOWN_LIMITATIONS),
    }

    return {
        "metadata": metadata,
        "source_type": source_type,
        "source_id": source_id,
        "title": title,
        "summary": summary,
        "scenario": scenario_data,
        "dry_run": report_data,
        "campaign_id": answers.get("campaign_id", ""),
        "campaign_name": answers.get("campaign_name", ""),
        "objective": answers.get("objective", ""),
        "customer_type": answers.get("customer_type", ""),
        "document_type": answers.get("document_type", ""),
        "event_type": answers.get("event_type", ""),
        "payload": scenario_data.get("payload") or {},
        "execution_steps": scenario_data.get("execution_steps") or [],
        "validation_steps": scenario_data.get("validation_steps") or [],
        "queries": scenario_data.get("queries") or [],
        "checkpoints": scenario_data.get("checkpoints") or [],
        "evidence_files": scenario_data.get("evidence_files") or [],
        "warnings": warnings,
        "dry_run_summary": dry_run_summary,
        "dry_run_steps": dry_run_steps,
        "dry_run_logs": dry_run_logs,
    }
