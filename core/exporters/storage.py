import json
import os
import re
from pathlib import Path

from .common import build_export_filename


DEFAULT_EXPORTS_DIR = "exports_gerados"
DEFAULT_DRY_RUNS_DIR = "dryruns_gerados"
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def get_exports_dir():
    return Path(os.getenv("EXPORTS_GERADOS_PATH", DEFAULT_EXPORTS_DIR))


def get_dry_runs_dir():
    return Path(os.getenv("DRYRUNS_GERADOS_PATH", DEFAULT_DRY_RUNS_DIR))


def load_dry_run_report(report_id):
    if not report_id or not ID_PATTERN.fullmatch(report_id):
        return None

    path = get_dry_runs_dir() / f"{report_id}.json"
    if not path.exists():
        return None

    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def persist_export_bytes(content_bytes, source_type, source_id, export_type, extension):
    directory = get_exports_dir()
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / build_export_filename(source_type, source_id, export_type, extension)
    path.write_bytes(content_bytes)
    return path
