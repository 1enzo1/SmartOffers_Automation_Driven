from core.generation.storage import load_scenario

from .common import EXPORT_EXTENSIONS, EXPORT_MIME_TYPES, build_export_context
from .docx_exporter import export_docx_artifact
from .json_exporter import export_json_artifact
from .storage import load_dry_run_report
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
