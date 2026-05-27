import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from core.generation.storage import load_scenario

from .common import EXPORT_EXTENSIONS, EXPORT_MIME_TYPES, build_export_context, utc_now_iso
from .docx_exporter import export_docx_artifact
from .json_exporter import export_json_artifact
from .storage import load_dry_run_report, save_dry_run_report
from .xlsx_exporter import export_xlsx_artifact


class ExportSourceNotFoundError(FileNotFoundError):
    pass


class ExportFormatError(ValueError):
    pass


FORMAT_EXPORTERS = {
    "docx": export_docx_artifact,
    "xlsx": export_xlsx_artifact,
    "json": export_json_artifact,
}


def _deterministic_duration(seed, base=18, spread=30):
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return base + (int(digest[:4], 16) % spread)


def _build_dry_run_step(scenario_id, source_step, step_type):
    step_name = source_step.get("action") if step_type == "execution" else source_step.get("validation")
    duration_ms = _deterministic_duration(
        f"{scenario_id}|{step_type}|{source_step.get('step')}|{step_name}"
    )

    override = source_step.get("dry_run") or {}
    status = override.get("status") or source_step.get("dry_run_status") or "passed"
    if status not in {"passed", "failed", "skipped"}:
        status = "passed"

    default_message = (
        "Step simulado localmente, sem executar scripts ou integracoes reais."
        if step_type == "execution"
        else "Validacao simulada localmente, sem consultar sistemas externos."
    )
    message = override.get("message") or default_message

    return {
        "name": step_name,
        "type": step_type,
        "status": status,
        "duration_ms": duration_ms,
        "message": message,
        "source_step": source_step,
    }


def simulate_dry_run_report(scenario):
    started_at = datetime.now(timezone.utc)
    report_id = (
        f"dryrun-{scenario['id']}-"
        f"{started_at.strftime('%Y%m%d%H%M%S%f')}-"
        f"{uuid.uuid4().hex[:8]}"
    )

    steps = []
    for source_step in scenario.get("execution_steps") or []:
        steps.append(_build_dry_run_step(scenario["id"], source_step, "execution"))
    for source_step in scenario.get("validation_steps") or []:
        steps.append(_build_dry_run_step(scenario["id"], source_step, "validation"))

    summary = {
        "total": len(steps),
        "passed": sum(1 for step in steps if step["status"] == "passed"),
        "failed": sum(1 for step in steps if step["status"] == "failed"),
        "skipped": sum(1 for step in steps if step["status"] == "skipped"),
    }

    warnings = list(scenario.get("warnings") or [])
    source_answers = scenario.get("source_answers") or {}
    if source_answers.get("event_type") == "recarga" or source_answers.get("recharge_scenario") == "none":
        warnings.append(
            "Limitacao conhecida: event_type == \"recarga\" ainda pode permitir recharge_scenario == \"none\" no modo mockado."
        )

    duration_ms = sum(step["duration_ms"] for step in steps) + 47
    finished_at = started_at + timedelta(milliseconds=duration_ms)

    report = {
        "id": report_id,
        "scenario_id": scenario["id"],
        "status": "passed" if summary["failed"] == 0 else "failed",
        "started_at": started_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "finished_at": finished_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "duration_ms": duration_ms,
        "steps": steps,
        "summary": summary,
        "logs": [
            f"DRY_RUN|START|scenario={scenario['id']}",
            "DRY_RUN|LOCAL_ONLY|Oracle, APIs, SmartOffers, Kafka, Jenkins e scripts reais desabilitados.",
            *[
                "DRY_RUN|STEP|{status}|{type}|{name}|{message}".format(
                    status=step["status"],
                    type=step["type"],
                    name=step["name"],
                    message=step["message"],
                )
                for step in steps
            ],
            "DRY_RUN|END|{status}|total={total}|passed={passed}|failed={failed}|skipped={skipped}".format(
                status="passed" if summary["failed"] == 0 else "failed",
                **summary,
            ),
        ],
        "warnings": warnings,
    }

    return report, save_dry_run_report(report)


def _load_export_source(source_type, source_id):
    if source_type == "scenario":
        scenario = load_scenario(source_id)
        if not scenario:
            raise ExportSourceNotFoundError(source_id)
        return scenario, None

    if source_type == "dry_run":
        report = load_dry_run_report(source_id)
        if not report:
            raise ExportSourceNotFoundError(source_id)
        scenario = load_scenario(report.get("scenario_id"))
        return report, scenario

    raise ExportSourceNotFoundError(source_id)


def export_artifact(source_type, source_id, export_format):
    export_format = (export_format or "").lower()
    exporter = FORMAT_EXPORTERS.get(export_format)
    extension = EXPORT_EXTENSIONS.get(export_format)

    if not exporter or not extension:
        raise ExportFormatError(export_format)

    source_data, scenario = _load_export_source(source_type, source_id)
    context = build_export_context(
        source_type,
        source_id,
        source_data,
        export_format,
        scenario=scenario,
    )
    return exporter(context)


def export_scenario_artifact(scenario_id, export_format):
    return export_artifact("scenario", scenario_id, export_format)


def export_dry_run_artifact(report_id, export_format):
    return export_artifact("dry_run", report_id, export_format)


def get_export_mimetype(export_format):
    export_format = (export_format or "").lower()
    return EXPORT_MIME_TYPES.get(export_format)


def get_export_extension(export_format):
    export_format = (export_format or "").lower()
    return EXPORT_EXTENSIONS.get(export_format)


def load_dry_run_report_by_id(report_id):
    return load_dry_run_report(report_id)
